#!/usr/bin/env python3
"""Run the repository unittest suite and emit an Elenchus report."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


def safe_report_path(root: Path, raw: str) -> Path:
    root = root.resolve()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("report path must stay inside the repository")
    if candidate.suffix != ".json" or candidate.parent.name != ".elenchus":
        raise ValueError("report must be a JSON file directly under .elenchus")
    return candidate


def atomic_write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".unittest-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def run(root: Path, report_path: Path, verbosity: int = 2) -> tuple[bool, int]:
    root = root.resolve()
    started_ns = time.time_ns()
    if report_path.exists():
        report_path.unlink()
    root_text = str(root)
    inserted = root_text not in sys.path
    if inserted:
        sys.path.insert(0, root_text)
    try:
        suite = unittest.defaultTestLoader.discover(str(root / "tests"))
        result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    finally:
        if inserted:
            sys.path.remove(root_text)
    report = {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }
    atomic_write_report(report_path, report)
    if report_path.stat().st_mtime_ns < started_ns:
        report_path.unlink(missing_ok=True)
        raise RuntimeError("test report is not fresh")
    success = result.wasSuccessful() and result.testsRun > 0
    return success, result.testsRun


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="JSON path directly under .elenchus")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        report_path = safe_report_path(root, args.report)
        success, count = run(root, report_path)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"test runner refused: {exc}")
        return 2
    print(f"unittest report: {count} test(s), {'passed' if success else 'failed'}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
