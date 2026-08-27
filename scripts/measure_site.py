#!/usr/bin/env python3
"""Measure the static files governed by the site's Metron budgets."""

from __future__ import annotations

import argparse
import json
import os
import struct
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


PAGES = (
    "index.html",
    "sage.html",
    "shoggoth.html",
    "handoffs.html",
    "architecture.html",
    "policy.html",
    "pilot.html",
    "limits.html",
    "engineering-primer.html",
    "sources.html",
)
IGNORED_DIRS = {".git", ".hexaemeron", ".elenchus", ".metron", ".venv", "__pycache__"}
RUNTIME_SUFFIXES = {".js", ".mjs", ".cjs"}


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.resources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value for key, value in attrs}
        if tag == "link" and "stylesheet" in (values.get("rel") or "").split():
            if values.get("href"):
                self.resources.append(str(values["href"]))
        if tag == "img" and values.get("src"):
            self.resources.append(str(values["src"]))


def webp_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError(f"{path} is not a WebP RIFF file")
    cursor = 12
    while cursor + 8 <= len(data):
        chunk = data[cursor : cursor + 4]
        size = int.from_bytes(data[cursor + 4 : cursor + 8], "little")
        payload = data[cursor + 8 : cursor + 8 + size]
        if len(payload) != size:
            raise ValueError(f"{path} has a truncated WebP chunk")
        if chunk == b"VP8X" and size >= 10:
            width = 1 + int.from_bytes(payload[4:7], "little")
            height = 1 + int.from_bytes(payload[7:10], "little")
            return width, height
        if chunk == b"VP8 " and size >= 10 and payload[3:6] == b"\x9d\x01\x2a":
            width = struct.unpack_from("<H", payload, 6)[0] & 0x3FFF
            height = struct.unpack_from("<H", payload, 8)[0] & 0x3FFF
            return width, height
        if chunk == b"VP8L" and size >= 5 and payload[0] == 0x2F:
            bits = int.from_bytes(payload[1:5], "little")
            width = 1 + (bits & 0x3FFF)
            height = 1 + ((bits >> 14) & 0x3FFF)
            return width, height
        cursor += 8 + size + (size & 1)
    raise ValueError(f"{path} has no supported WebP image chunk")


def safe_output(root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("measurement output must stay inside the site root")
    if candidate.suffix != ".json" or candidate.parent.name != ".metron":
        raise ValueError("measurement output must be a JSON file directly under .metron")
    return candidate


def atomic_write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".site-run-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def measure(root: Path) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("site root is not a directory")
    files: list[dict[str, object]] = []
    html_sizes: list[int] = []
    for name in PAGES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"required page is missing: {name}")
        size = path.stat().st_size
        html_sizes.append(size)
        files.append({"path": name, "bytes": size, "kind": "html"})
    css = root / "assets" / "style.css"
    if not css.is_file() or css.is_symlink():
        raise ValueError("assets/style.css is missing")
    css_size = css.stat().st_size
    files.append({"path": "assets/style.css", "bytes": css_size, "kind": "css"})
    webp_sizes: list[int] = []
    for path in sorted((root / "assets").rglob("*.webp")):
        if path.is_symlink():
            raise ValueError(f"symbolic image is not accepted: {path.relative_to(root)}")
        width, height = webp_dimensions(path)
        size = path.stat().st_size
        webp_sizes.append(size)
        files.append(
            {
                "path": str(path.relative_to(root)),
                "bytes": size,
                "kind": "webp",
                "width": width,
                "height": height,
            }
        )
    index = root / "index.html"
    parser = ResourceParser()
    parser.feed(index.read_text(encoding="utf-8"))
    parser.close()
    first_load = index.stat().st_size
    seen: set[Path] = set()
    for resource in parser.resources:
        split = urlsplit(resource)
        if split.scheme or split.netloc or split.path.startswith("/"):
            raise ValueError(f"index resource must be local and subpath-safe: {resource}")
        target = (root / split.path).resolve()
        if not target.is_relative_to(root) or not target.is_file() or target.is_symlink():
            raise ValueError(f"index resource is missing or unsafe: {resource}")
        if target not in seen:
            seen.add(target)
            first_load += target.stat().st_size
    runtime_files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_file() and path.suffix.lower() in RUNTIME_SUFFIXES:
            size = path.stat().st_size
            runtime_files.append(size)
            files.append({"path": str(relative), "bytes": size, "kind": "javascript"})
    measurements = {
        "site.max_html_bytes": max(html_sizes),
        "site.css_bytes": css_size,
        "site.max_webp_bytes": max(webp_sizes, default=0),
        "site.index_first_load_bytes": first_load,
        "site.runtime_javascript_bytes": sum(runtime_files),
    }
    return {
        "schema": "site-measurement-v1",
        "note": "Static byte and intrinsic-dimension measurement",
        "measurements": measurements,
        "files": files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="site root")
    parser.add_argument("--out", required=True, help="JSON path directly under .metron")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        output = safe_output(root, args.out)
        document = measure(root)
        atomic_write_json(output, document)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"measurement refused: {exc}")
        return 1
    count = len(document["files"])
    print(f"site measurement written: {output.relative_to(root)} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
