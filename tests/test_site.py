from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from scripts.check_site import (
    ALLOWED_STATUSES,
    CREDENTIAL,
    PAGES,
    PRIVATE_PATH,
    check_site,
    iter_text_files,
    local_target,
    parse_pages,
)
from scripts.measure_site import measure
from scripts.run_tests import atomic_write_report, run, safe_report_path


ROOT = Path(__file__).resolve().parents[1]


class SiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.findings = []
        cls.pages = parse_pages(ROOT, cls.findings)
        cls.sources = json.loads((ROOT / "evidence" / "sources.json").read_text(encoding="utf-8"))
        cls.claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))

    def test_complete_site_check_is_clean(self) -> None:
        self.assertEqual(check_site(ROOT), [])

    def test_page_inventory_is_exact(self) -> None:
        observed = {path.name for path in ROOT.glob("*.html")}
        self.assertEqual(observed, set(PAGES))
        self.assertEqual(set(self.pages), set(PAGES))

    def test_navigation_is_complete_and_marks_current_page(self) -> None:
        for name, page in self.pages.items():
            with self.subTest(page=name):
                local = {
                    urlsplit(href).path
                    for href in page.nav_hrefs
                    if urlsplit(href).path.endswith(".html")
                }
                self.assertEqual(local, set(PAGES))
                self.assertEqual(page.current_hrefs, [name])

    def test_source_registry_has_unique_pinned_entries(self) -> None:
        self.assertEqual(self.sources["schema"], "source-registry-v1")
        self.assertEqual(self.sources["edition"]["name"], "cooperative-v1")
        source_ids = [source["id"] for source in self.sources["sources"]]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertIn("SHOGGOTH", source_ids)
        self.assertIn("L-OPENAPI", source_ids)
        self.assertIn("U-MASCOT-KIT", source_ids)
        for source in self.sources["sources"]:
            self.assertTrue(source["observed_at"])

    def test_claim_status_vocabulary_and_page_binding(self) -> None:
        self.assertEqual(self.claims["schema"], "claim-registry-v1")
        self.assertEqual(set(self.claims["statuses"]), ALLOWED_STATUSES)
        registry = {claim["id"]: claim for claim in self.claims["claims"]}
        self.assertEqual(len(registry), len(self.claims["claims"]))
        seen: set[str] = set()
        for name, page in self.pages.items():
            for claim_id, status in page.claims:
                seen.add(claim_id)
                self.assertEqual(registry[claim_id]["page"], name)
                self.assertEqual(registry[claim_id]["status"], status)
        self.assertEqual(seen, set(registry))

    def test_every_local_link_and_fragment_resolves(self) -> None:
        for name, page in self.pages.items():
            for href in page.hrefs:
                target_info = local_target(ROOT, name, href)
                if target_info is None:
                    continue
                target, fragment = target_info
                with self.subTest(page=name, href=href):
                    self.assertTrue(target.is_file())
                    if fragment and target.suffix == ".html":
                        target_page = self.pages[str(target.relative_to(ROOT))]
                        self.assertIn(fragment, target_page.ids)

    def test_stylesheet_is_local_and_versioned(self) -> None:
        versions = set()
        for page in self.pages.values():
            self.assertEqual(len(page.stylesheets), 1)
            split = urlsplit(page.stylesheets[0])
            self.assertEqual(split.path, "assets/style.css")
            self.assertTrue(split.query)
            self.assertFalse(split.scheme)
            versions.add(split.query)
        self.assertEqual(len(versions), 1)

    def test_site_has_no_runtime_surface(self) -> None:
        for name, page in self.pages.items():
            with self.subTest(page=name):
                self.assertEqual(page.forbidden_tags, [])
        css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8").lower()
        self.assertNotIn("@import", css)
        self.assertNotIn("url(http", css)

    def test_tracked_text_has_no_private_path_or_credential_shape(self) -> None:
        for path, text in iter_text_files(ROOT):
            with self.subTest(path=path):
                self.assertIsNotNone(text)
                self.assertIsNone(PRIVATE_PATH.search(text or ""))
                self.assertIsNone(CREDENTIAL.search(text or ""))

    def test_budget_file_names_every_measurement(self) -> None:
        budgets = json.loads((ROOT / "evidence" / "metron-budgets.json").read_text(encoding="utf-8"))
        observed = {entry["name"]: entry["limit"] for entry in budgets["budgets"]}
        self.assertEqual(
            observed,
            {
                "site.max_html_bytes": 102400,
                "site.css_bytes": 24576,
                "site.max_webp_bytes": 204800,
                "site.index_first_load_bytes": 358400,
                "site.runtime_javascript_bytes": 0,
            },
        )

    def test_measurement_producer_matches_budget_names(self) -> None:
        document = measure(ROOT)
        budget_document = json.loads(
            (ROOT / "evidence" / "metron-budgets.json").read_text(encoding="utf-8")
        )
        budget_names = {entry["name"] for entry in budget_document["budgets"]}
        self.assertEqual(set(document["measurements"]), budget_names)
        self.assertEqual(document["measurements"]["site.runtime_javascript_bytes"], 0)
        self.assertEqual(len([item for item in document["files"] if item["kind"] == "html"]), 10)

    def test_report_writer_replaces_stale_bytes_with_exact_schema(self) -> None:
        report = {
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 3,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_dir = root / ".elenchus"
            report_dir.mkdir()
            path = safe_report_path(root, ".elenchus/example.json")
            path.write_text("stale", encoding="utf-8")
            before = time.time_ns()
            atomic_write_report(path, report)
            self.assertGreaterEqual(path.stat().st_mtime_ns, before)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), report)

    def test_runner_refuses_a_zero_test_suite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tests = root / "tests"
            tests.mkdir()
            (tests / "__init__.py").write_text("", encoding="utf-8")
            success, count = run(root, root / ".elenchus" / "empty.json", verbosity=0)
            self.assertFalse(success)
            self.assertEqual(count, 0)
            report = json.loads((root / ".elenchus" / "empty.json").read_text(encoding="utf-8"))
            self.assertEqual(report["testsRun"], 0)

    def test_decision_records_and_licence_boundary_are_present(self) -> None:
        decisions = sorted((ROOT / "docs" / "decisions").glob("ADR-*.md"))
        self.assertEqual(len(decisions), 3)
        for path in decisions:
            text = path.read_text(encoding="utf-8")
            for heading in ("## Status", "## Context", "## Decision", "## Alternatives", "## Consequences"):
                self.assertIn(heading, text)
            self.assertNotIn("Superseded by ADR-00N", text)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Licence status", readme)
        self.assertFalse((ROOT / "LICENSE").exists())


if __name__ == "__main__":
    unittest.main()
