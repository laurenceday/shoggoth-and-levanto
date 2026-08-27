#!/usr/bin/env python3
"""Serve and smoke-test the site at its exact GitHub Pages subpath."""

from __future__ import annotations

import argparse
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from scripts.check_site import check_site
    from scripts.public_smoke import PUBLIC_TARGETS, SmokeError, fetch_inventory
except ModuleNotFoundError:  # Direct execution from scripts/.
    from check_site import check_site
    from public_smoke import PUBLIC_TARGETS, SmokeError, fetch_inventory


DEFAULT_BASE_PATH = "/shoggoth-and-levanto/"
LOOPBACK = "127.0.0.1"


def validate_base_path(value: str) -> str:
    if value != DEFAULT_BASE_PATH:
        raise SmokeError(f"base path must be exactly {DEFAULT_BASE_PATH}")
    return value


def validate_port(value: int) -> int:
    if value < 0 or value > 65535:
        raise SmokeError("port must be from 0 to 65535")
    return value


def handler_for(root: Path, base_path: str):
    root = root.resolve()
    routes = {
        base_path + target.path: (
            root / (target.path or "index.html"),
            target.content_type,
        )
        for target in PUBLIC_TARGETS
    }

    class StaticHandler(BaseHTTPRequestHandler):
        server_version = "CooperativePagesDemo/1"
        sys_version = ""

        def do_GET(self) -> None:
            self._serve(include_body=True)

        def do_HEAD(self) -> None:
            self._serve(include_body=False)

        def _serve(self, *, include_body: bool) -> None:
            split = urlsplit(self.path)
            route = unquote(split.path)
            if split.query or route not in routes:
                self.send_error(404, "Not found")
                return
            path, content_type = routes[route]
            try:
                resolved = path.resolve(strict=True)
                if (
                    not resolved.is_relative_to(root)
                    or not resolved.is_file()
                    or path.is_symlink()
                ):
                    raise OSError("unsafe target")
                body = resolved.read_bytes()
            except OSError:
                self.send_error(404, "Not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def log_message(self, format_string: str, *args) -> None:
            return

    return StaticHandler


def run_demo(
    root: Path,
    port: int,
    base_path: str,
    expected_edition: str,
) -> tuple[str, list[dict[str, object]]]:
    root = root.resolve()
    if not root.is_dir():
        raise SmokeError("site root is not a directory")
    validate_port(port)
    validate_base_path(base_path)
    findings = check_site(root)
    if findings:
        raise SmokeError(f"site contract has {len(findings)} finding(s)")
    server = ThreadingHTTPServer(
        (LOOPBACK, port),
        handler_for(root, base_path),
    )
    server.daemon_threads = True
    actual_port = int(server.server_address[1])
    base_url = f"http://{LOOPBACK}:{actual_port}{base_path}"
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        records = fetch_inventory(
            base_url,
            expected_edition,
            expected_root=root,
            maximum_redirects=0,
        )
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    if worker.is_alive():
        raise SmokeError("local demo server did not stop")
    return base_url, records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--base-path", required=True)
    parser.add_argument("--expected-edition", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        base_url, records = run_demo(
            Path(args.root),
            args.port,
            args.base_path,
            args.expected_edition,
        )
    except (OSError, SmokeError) as exc:
        print(f"local Pages demo refused: {exc}")
        return 1
    print(f"local Pages demo clean: {len(records)} targets at {base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
