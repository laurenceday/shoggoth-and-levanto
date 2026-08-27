from __future__ import annotations

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from scripts.check_site import (
    ALLOWED_STATUSES,
    AUTHORITY_SENTENCE,
    CREDENTIAL,
    EXAMPLE_LABEL,
    HERO_BYTES,
    HERO_HEIGHT,
    HERO_PATH,
    HERO_SHA256,
    HERO_WIDTH,
    PAGES,
    PRIVATE_PATH,
    SITE_ORIGIN,
    SOCIAL_BYTES,
    SOCIAL_HEIGHT,
    SOCIAL_PATH,
    SOCIAL_SHA256,
    SOCIAL_WIDTH,
    PageParser,
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

    def copy_site(self, directory: str) -> Path:
        destination = Path(directory) / "site"
        shutil.copytree(
            ROOT,
            destination,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", ".hexaemeron", ".elenchus", ".metron", "__pycache__"
            ),
        )
        return destination

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
            self.assertIn(f'src-{source["id"]}', self.pages["sources.html"].ids)

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
        for page in self.pages.values():
            self.assertGreaterEqual(len(page.claims), 4)
        for claim_id in (
            "POLICY-KINDS-USES",
            "LIMIT-CONFIDENCE-CONTROL",
            "LIMIT-SERVICE-CONTROL",
            "LIMIT-RETENTION-CONTROL",
            "ENG-ENDPOINT-CONTROL",
        ):
            self.assertEqual(registry[claim_id]["status"], "proposed")

    def test_authority_sentence_is_single_and_protected(self) -> None:
        locations = [
            name
            for name in PAGES
            for _ in range((ROOT / name).read_text(encoding="utf-8").count(AUTHORITY_SENTENCE))
        ]
        self.assertEqual(locations, ["architecture.html"])
        self.assertIn("authority-boundary", self.pages["architecture.html"].ids)
        self.assertIn("braking-authority", self.pages["pilot.html"].ids)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            index = root / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "Sage can add a route, refusal or escalation signal, but final transition authority remains with the Promise Machine.",
                    AUTHORITY_SENTENCE,
                ),
                encoding="utf-8",
            )
            self.assertIn("S029", {finding.code for finding in check_site(root)})

    def test_illustrative_examples_are_explicitly_unexecuted(self) -> None:
        illustrative = sum(
            status == "illustrative"
            for page in self.pages.values()
            for _, status in page.claims
        )
        labels = sum(
            (ROOT / name).read_text(encoding="utf-8").count(
                f'<span class="example-label">{EXAMPLE_LABEL}</span>'
            )
            for name in PAGES
        )
        self.assertEqual(labels, illustrative)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            page = root / "sage.html"
            page.write_text(
                page.read_text(encoding="utf-8").replace(EXAMPLE_LABEL, "Example", 1),
                encoding="utf-8",
            )
            self.assertIn("S028", {finding.code for finding in check_site(root)})

    def test_generated_hero_is_digest_and_provenance_bound(self) -> None:
        hero = ROOT / HERO_PATH
        self.assertEqual(hero.stat().st_size, HERO_BYTES)
        measured = measure(ROOT)
        record = next(item for item in measured["files"] if item["path"] == HERO_PATH)
        self.assertEqual((record["width"], record["height"]), (HERO_WIDTH, HERO_HEIGHT))
        source = next(item for item in self.sources["sources"] if item["id"] == "GEN-HERO")
        self.assertEqual(source["revision"], f"sha256:{HERO_SHA256}")
        prompt = (ROOT / "assets" / "imagegen-prompts.md").read_text(encoding="utf-8")
        self.assertIn(HERO_SHA256, prompt)
        self.assertIn("Reference roles:", prompt)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            prompt_path = root / "assets" / "imagegen-prompts.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8").replace(HERO_SHA256, "0" * 64),
                encoding="utf-8",
            )
            self.assertIn("S068", {finding.code for finding in check_site(root)})

    def test_social_preview_and_sitewide_metadata_are_bound(self) -> None:
        social = ROOT / SOCIAL_PATH
        self.assertEqual(social.stat().st_size, SOCIAL_BYTES)
        measured = measure(ROOT)
        record = next(item for item in measured["files"] if item["path"] == SOCIAL_PATH)
        self.assertEqual((record["width"], record["height"]), (SOCIAL_WIDTH, SOCIAL_HEIGHT))
        source = next(item for item in self.sources["sources"] if item["id"] == "GEN-SOCIAL")
        self.assertEqual(source["revision"], f"sha256:{SOCIAL_SHA256}")
        social_url = f"{SITE_ORIGIN}/{SOCIAL_PATH}"
        for name, page in self.pages.items():
            page_url = f"{SITE_ORIGIN}/" if name == "index.html" else f"{SITE_ORIGIN}/{name}"
            with self.subTest(page=name):
                self.assertEqual(page.metadata["og:image"], [social_url])
                self.assertEqual(page.metadata["twitter:image"], [social_url])
                self.assertEqual(page.metadata["og:url"], [page_url])
                self.assertEqual(page.canonicals, [page_url])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            page = root / "index.html"
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    '<meta property="og:image:width" content="1200">',
                    '<meta property="og:image:width" content="1199">',
                    1,
                ),
                encoding="utf-8",
            )
            self.assertIn("S093", {finding.code for finding in check_site(root)})

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

    def test_duplicate_ids_are_rejected(self) -> None:
        parser = PageParser()
        parser.feed('<main id="same"><p id="same">duplicate</p></main>')
        parser.close()
        self.assertEqual(getattr(parser, "duplicate_ids", set()), {"same"})

    def test_duplicate_html_attributes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            page = root / "index.html"
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    '<img src="assets/generated/cooperative-threshold.webp"',
                    '<img src="https://example.com/unreviewed.webp" src="assets/generated/cooperative-threshold.webp"',
                    1,
                ),
                encoding="utf-8",
            )
            self.assertIn("S097", {finding.code for finding in check_site(root)})

    def test_active_html_bypass_surfaces_are_rejected(self) -> None:
        for href in (
            "http://example.com/insecure",
            "https:relative",
            "https://user:pass@example.com/credential-bearing",
        ):
            with self.subTest(href=href), self.assertRaises(ValueError):
                local_target(ROOT, "index.html", href)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            page = root / "index.html"
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "</head>",
                    '<base href="https://example.com/"><link rel="preconnect" href="https://example.com/"><style>body{color:red}</style></head>',
                    1,
                ).replace(
                    '<main id="main">',
                    '<svg><image href="https://example.com/pixel"></image></svg><main id="main" style="background:url(https://example.com/pixel)">',
                    1,
                ),
                encoding="utf-8",
            )
            codes = {finding.code for finding in check_site(root)}
            self.assertIn("S011", codes)
            self.assertIn("S098", codes)
            self.assertIn("S099", codes)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            page = root / "index.html"
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    '<main id="main">',
                    '<svg><image href="https://example.com/pixel"></image></svg><main id="main">',
                    1,
                ),
                encoding="utf-8",
            )
            self.assertIn("S011", {finding.code for finding in check_site(root)})

    def test_css_urls_and_unapproved_assets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            css = root / "assets" / "style.css"
            css.write_text(
                css.read_text(encoding="utf-8") + '\n.hidden { background: url("generated/font.woff2"); }\n',
                encoding="utf-8",
            )
            (root / "assets" / "generated" / "font.woff2").write_bytes(b"not a font")
            codes = {finding.code for finding in check_site(root)}
            self.assertIn("S074", codes)
            self.assertIn("S079", codes)
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            css = root / "assets" / "style.css"
            css.write_text(
                css.read_text(encoding="utf-8")
                + '\n.hidden { background-image: image-set("generated/social-preview.webp" 1x); }\n',
                encoding="utf-8",
            )
            self.assertIn("S074", {finding.code for finding in check_site(root)})

    def test_hidden_runtime_inputs_are_rejected_and_measured(self) -> None:
        with self.assertRaises(ValueError):
            local_target(ROOT, "index.html", "javascript:alert(1)")
        parser = PageParser()
        parser.feed('<meta http-equiv="refresh" content="0"><a onclick="run()">x</a>')
        parser.close()
        self.assertTrue(getattr(parser, "refresh_meta", False))
        self.assertEqual(getattr(parser, "runtime_attributes", []), ["onclick"])
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            (root / "runtime.js").write_text("alert(1);\n", encoding="utf-8")
            codes = {finding.code for finding in check_site(root)}
            self.assertIn("S078", codes)
            self.assertGreater(measure(root)["measurements"]["site.runtime_javascript_bytes"], 0)

    def test_image_sources_must_be_local_webp_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            path = root / "index.html"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                "</main>",
                '<img src="https://example.com/copied.png" alt="copied" width="10" height="10">\n</main>',
            )
            path.write_text(text, encoding="utf-8")
            codes = {finding.code for finding in check_site(root)}
            self.assertIn("S023", codes)

    def test_extra_page_and_reference_source_mirror_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            (root / "rogue.html").write_text("<!doctype html><title>rogue</title>\n", encoding="utf-8")
            mirror = root / "mascot-imagegen-kit-main"
            mirror.mkdir()
            (mirror / "reference.txt").write_text("reference bytes\n", encoding="utf-8")
            codes = {finding.code for finding in check_site(root)}
            self.assertIn("S004", codes)
            self.assertIn("S077", codes)

    def test_source_urls_require_full_https_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            path = root / "evidence" / "sources.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["sources"][0]["url"] = "https:relative"
            document["sources"][1]["url"] = "https://user:pass@example.com/source"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            url_findings = [finding for finding in check_site(root) if finding.code == "S048"]
            self.assertEqual(len(url_findings), 2)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_site(directory)
            path = root / "evidence" / "sources.json"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                '  "schema": "source-registry-v1",',
                '  "schema": "source-registry-v1",\n  "schema": "source-registry-v1",',
                1,
            )
            path.write_text(text, encoding="utf-8")
            codes = {finding.code for finding in check_site(root)}
            self.assertIn("S040", codes)

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

    def test_runner_keeps_repository_on_path_during_test_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            tests = root / "tests"
            tests.mkdir()
            source = (
                "import sys\n"
                "import unittest\n\n"
                "class RuntimePathTest(unittest.TestCase):\n"
                "    def test_repository_root_is_visible(self):\n"
                f"        self.assertIn({str(root)!r}, sys.path)\n"
            )
            (tests / "test_runtime_path.py").write_text(source, encoding="utf-8")
            success, count = run(root, root / ".elenchus" / "path.json", verbosity=0)
            self.assertTrue(success)
            self.assertEqual(count, 1)

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
