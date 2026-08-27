#!/usr/bin/env python3
"""Run the complete local static-site check without external dependencies."""

from __future__ import annotations

from pathlib import Path

from check_site import PAGES, check_site
from measure_site import atomic_write_json, measure
from run_tests import run


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = check_site(root)
    if findings:
        for finding in findings:
            print(f"ERROR {finding.render()}")
        print(f"local check failed: {len(findings)} site finding(s)")
        return 1
    measurement_path = root / ".metron" / "site-run.json"
    atomic_write_json(measurement_path, measure(root))
    success, count = run(root, root / ".elenchus" / "site.json", verbosity=1)
    if not success:
        print(f"local check failed: {count} test(s) ran")
        return 1
    print(f"local check clean: {len(PAGES)} pages, {count} test(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
