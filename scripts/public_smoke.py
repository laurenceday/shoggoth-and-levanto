#!/usr/bin/env python3
"""Read the fixed GitHub Pages inventory and write one bounded readback."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PUBLIC_BASE_URL = "https://laurenceday.github.io/shoggoth-and-levanto/"
PUBLIC_HOST = "laurenceday.github.io"
PUBLIC_PATH = "/shoggoth-and-levanto/"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 8.0
EDITION = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
RUN_ID = re.compile(r"^[0-9]{1,32}$")


@dataclass(frozen=True)
class Target:
    path: str
    content_type: str
    html: bool = False


PUBLIC_TARGETS = (
    Target("", "text/html", True),
    Target("sage.html", "text/html", True),
    Target("shoggoth.html", "text/html", True),
    Target("handoffs.html", "text/html", True),
    Target("architecture.html", "text/html", True),
    Target("policy.html", "text/html", True),
    Target("pilot.html", "text/html", True),
    Target("limits.html", "text/html", True),
    Target("engineering-primer.html", "text/html", True),
    Target("sources.html", "text/html", True),
    Target("assets/style.css", "text/css"),
    Target("assets/generated/cooperative-threshold.webp", "image/webp"),
    Target("assets/generated/social-preview.webp", "image/webp"),
    Target("evidence/claims.json", "application/json"),
    Target("evidence/sources.json", "application/json"),
)


class SmokeError(ValueError):
    """A bounded public-readback failure."""


class TargetFailure(SmokeError):
    def __init__(self, target: str, detail: str) -> None:
        super().__init__(detail)
        self.target = target or "<site root>"
        self.detail = detail


def validate_edition(value: str) -> str:
    if not EDITION.fullmatch(value):
        raise SmokeError("expected edition has an invalid shape")
    return value


def validate_public_base(raw: str) -> str:
    try:
        split = urlsplit(raw)
        port = split.port
    except ValueError as exc:
        raise SmokeError(f"public base URL is invalid: {exc}") from exc
    if (
        split.scheme != "https"
        or split.hostname != PUBLIC_HOST
        or port not in {None, 443}
        or split.username is not None
        or split.password is not None
        or split.path != PUBLIC_PATH
        or split.query
        or split.fragment
    ):
        raise SmokeError(f"public base URL must be {PUBLIC_BASE_URL}")
    return raw


def url_within_base(raw: str, base_url: str) -> bool:
    try:
        candidate = urlsplit(raw)
        base = urlsplit(base_url)
        candidate_port = candidate.port
        base_port = base.port
    except ValueError:
        return False
    return (
        candidate.scheme == base.scheme
        and candidate.hostname == base.hostname
        and candidate_port == base_port
        and candidate.username is None
        and candidate.password is None
        and candidate.path.startswith(base.path)
        and not candidate.fragment
    )


class BoundedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, base_url: str, maximum: int) -> None:
        super().__init__()
        self.base_url = base_url
        self.maximum = maximum
        self.followed = 0

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        self.followed += 1
        if self.followed > self.maximum:
            raise HTTPError(new_url, code, "redirect limit exceeded", headers, file_pointer)
        if not url_within_base(new_url, self.base_url):
            raise HTTPError(new_url, code, "redirect left the fixed site base", headers, file_pointer)
        return super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )


def fetch_inventory(
    base_url: str,
    expected_edition: str,
    *,
    maximum_redirects: int,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> list[dict[str, object]]:
    validate_edition(expected_edition)
    if timeout <= 0 or timeout > REQUEST_TIMEOUT_SECONDS:
        raise SmokeError("request timeout is outside the accepted bound")
    opener = build_opener(BoundedRedirectHandler(base_url, maximum_redirects))
    records: list[dict[str, object]] = []
    edition_marker = f'data-edition="{expected_edition}"'.encode("utf-8")
    for target in PUBLIC_TARGETS:
        url = urljoin(base_url, target.path)
        request = Request(
            url,
            headers={
                "Accept": "*/*",
                "User-Agent": "shoggoth-levanto-pages-readback/1",
            },
            method="GET",
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                status = int(response.status)
                final_url = response.geturl()
                content_type = response.headers.get_content_type().lower()
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, OSError, TimeoutError, ValueError) as exc:
            raise TargetFailure(target.path, f"request failed: {exc}") from exc
        if not url_within_base(final_url, base_url):
            raise TargetFailure(target.path, "final URL left the fixed site base")
        if status != 200:
            raise TargetFailure(target.path, f"expected HTTP 200, observed {status}")
        if content_type != target.content_type:
            raise TargetFailure(
                target.path,
                f"expected {target.content_type}, observed {content_type}",
            )
        if not body:
            raise TargetFailure(target.path, "response body is empty")
        if len(body) > MAX_RESPONSE_BYTES:
            raise TargetFailure(target.path, "response exceeds the two-megabyte bound")
        if target.html and body.count(edition_marker) != 1:
            raise TargetFailure(
                target.path,
                f"edition marker {expected_edition!r} was not present exactly once",
            )
        records.append(
            {
                "target": target.path or "/",
                "url": final_url,
                "status": status,
                "content_type": content_type,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "edition": expected_edition if target.html else None,
            }
        )
    return records


def safe_output(root: Path, raw: str) -> Path:
    root = root.resolve()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(root):
        raise SmokeError("readback output must stay inside the repository")
    if candidate.suffix != ".json" or candidate.parent.name != ".hexaemeron":
        raise SmokeError("readback output must be a JSON file directly under .hexaemeron")
    return candidate


def atomic_write_json(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".pages-readback-", dir=path.parent)
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


def deployment_context() -> dict[str, object]:
    github_sha = os.environ.get("GITHUB_SHA", "")
    github_run_id = os.environ.get("GITHUB_RUN_ID", "")
    return {
        "github_sha": github_sha if COMMIT.fullmatch(github_sha) else None,
        "github_run_id": github_run_id if RUN_ID.fullmatch(github_run_id) else None,
    }


def readback_document(
    base_url: str,
    expected_edition: str,
    records: list[dict[str, object]],
    *,
    failed_target: str | None = None,
    failure: str | None = None,
) -> dict[str, object]:
    return {
        "schema": "pages-readback-v1",
        "complete": failed_target is None,
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_url": base_url,
        "expected_edition": expected_edition,
        "deployment_context": deployment_context(),
        "targets": records,
        "failed_target": failed_target,
        "failure": failure,
    }


def validate_complete_readback(path: Path, started_ns: int) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise SmokeError("readback is missing or symbolic")
    if path.stat().st_mtime_ns < started_ns:
        raise SmokeError("readback predates this smoke run")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise SmokeError(f"readback is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema") != "pages-readback-v1":
        raise SmokeError("readback schema is not pages-readback-v1")
    if document.get("complete") is not True or document.get("failed_target") is not None:
        raise SmokeError("readback is not complete")
    records = document.get("targets")
    expected = [target.path or "/" for target in PUBLIC_TARGETS]
    if not isinstance(records, list) or [record.get("target") for record in records if isinstance(record, dict)] != expected:
        raise SmokeError("readback target inventory is stale or incomplete")
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("status") != 200
            or not isinstance(record.get("bytes"), int)
            or record["bytes"] <= 0
        ):
            raise SmokeError("readback carries an invalid target result")
    return document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-edition", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    started_ns = time.time_ns()
    try:
        base_url = validate_public_base(args.base_url)
        expected_edition = validate_edition(args.expected_edition)
        output = safe_output(root, args.out)
        if output.is_symlink():
            raise SmokeError("readback output cannot be symbolic")
        output.unlink(missing_ok=True)
        try:
            records = fetch_inventory(
                base_url,
                expected_edition,
                maximum_redirects=2,
            )
        except TargetFailure as exc:
            failure = readback_document(
                base_url,
                expected_edition,
                [],
                failed_target=exc.target,
                failure=exc.detail,
            )
            atomic_write_json(output, failure)
            print(f"public smoke failed at {exc.target}: {exc.detail}")
            return 1
        document = readback_document(base_url, expected_edition, records)
        atomic_write_json(output, document)
        validate_complete_readback(output, started_ns)
    except SmokeError as exc:
        print(f"public smoke refused: {exc}")
        return 2
    print(f"public Pages smoke clean: {len(records)} targets; readback {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
