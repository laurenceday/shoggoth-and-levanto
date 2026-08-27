#!/usr/bin/env python3
"""Check the static site, its evidence registries and local asset boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from scripts.measure_site import measure, webp_dimensions
except ModuleNotFoundError:  # Direct execution from scripts/.
    from measure_site import measure, webp_dimensions


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
ALLOWED_STATUSES = {
    "current",
    "vendor-reported",
    "inferred",
    "proposed",
    "illustrative",
    "unknown",
}
UNSOURCED_STATUSES = {"proposed", "illustrative", "unknown"}
FORBIDDEN_TAGS = {"script", "form", "iframe", "object", "embed"}
IGNORED_DIRS = {".git", ".hexaemeron", ".elenchus", ".metron", ".venv", "__pycache__"}
FORBIDDEN_SOURCE_DIRS = {
    "mascot-imagegen-kit",
    "mascot-imagegen-kit-main",
    "shoggoth-vs-centaur",
    "plaidcat",
    "wildcat-finance-skills",
    "levanto-agent-skill",
}
RUNTIME_SUFFIXES = {".js", ".mjs", ".cjs"}
TEXT_SUFFIXES = {".html", ".css", ".md", ".json", ".py", ".txt", ".yml", ".yaml"}
SOURCE_ID = re.compile(r"^[A-Z][A-Z0-9-]*$")
PRIVATE_PATH = re.compile(
    r"(?:file:" r"//|/Us" r"ers/|/var/fol" r"ders/|/private/v" r"ar/|/t" r"mp/)"
)
CREDENTIAL = re.compile(
    r"(?i)(?:\bbearer\s+[A-Za-z0-9._~-]{24,}|\bgh[pousr]_[A-Za-z0-9]{20,}"
    r"|\bsk-[A-Za-z0-9]{20,}|\bsage_(?:live|test)_[A-Za-z0-9]{16,})"
)
AUTHORITY_SENTENCE = (
    "Sage may route, refuse or escalate; Sage alone does not authorise a Promise Machine transition."
)
EXAMPLE_LABEL = "Illustrative and unexecuted"
HERO_PATH = "assets/generated/cooperative-threshold.webp"
HERO_WIDTH = 1122
HERO_HEIGHT = 1402
HERO_BYTES = 74006
HERO_SHA256 = "bd04c8eb0af1104811acc62763c6245098d3b9ad66961986315b50718f772377"
SITE_ORIGIN = "https://laurenceday.github.io/shoggoth-and-levanto"
SOCIAL_PATH = "assets/generated/social-preview.webp"
SOCIAL_WIDTH = 1200
SOCIAL_HEIGHT = 630
SOCIAL_BYTES = 60100
SOCIAL_SHA256 = "7af8236616704a7af887cf383ded9e5001e2ca38c16f40fdea7051c4973d32e1"


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    detail: str

    def render(self) -> str:
        return f"{self.code} {self.path}: {self.detail}"


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key {key!r}")
        document[key] = value
    return document


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.hrefs: list[str] = []
        self.nav_hrefs: list[str] = []
        self.current_hrefs: list[str] = []
        self.stylesheets: list[str] = []
        self.images: list[dict[str, str]] = []
        self.claims: list[tuple[str, str | None]] = []
        self.statuses: list[str] = []
        self.editions: list[str] = []
        self.forbidden_tags: list[str] = []
        self.runtime_attributes: list[str] = []
        self.metadata: dict[str, list[str]] = {}
        self.canonicals: list[str] = []
        self.refresh_meta = False
        self.body_page: str | None = None
        self.nav_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value for key, value in attrs}
        if tag == "nav":
            self.nav_depth += 1
        if tag in FORBIDDEN_TAGS:
            self.forbidden_tags.append(tag)
        if values.get("id"):
            identifier = str(values["id"])
            if identifier in self.ids:
                self.duplicate_ids.add(identifier)
            self.ids.add(identifier)
        self.runtime_attributes.extend(key for key in values if key.startswith("on"))
        if tag == "meta" and (values.get("http-equiv") or "").lower() == "refresh":
            self.refresh_meta = True
        if tag == "meta":
            metadata_key = values.get("property") or values.get("name")
            if metadata_key:
                self.metadata.setdefault(metadata_key, []).append(values.get("content") or "")
        href = values.get("href")
        if href is not None:
            self.hrefs.append(href)
            if self.nav_depth and tag == "a":
                self.nav_hrefs.append(href)
                if values.get("aria-current") == "page":
                    self.current_hrefs.append(href)
        if tag == "link" and "stylesheet" in (values.get("rel") or "").split():
            if href is not None:
                self.stylesheets.append(href)
        if tag == "link" and "canonical" in (values.get("rel") or "").split():
            if href is not None:
                self.canonicals.append(href)
        if tag == "img":
            self.images.append({key: value or "" for key, value in attrs})
        claim = values.get("data-claim")
        if claim:
            self.claims.append((claim, values.get("data-status")))
        status = values.get("data-status")
        if status:
            self.statuses.append(status)
        edition = values.get("data-edition")
        if edition:
            self.editions.append(edition)
        if tag == "body":
            self.body_page = values.get("data-page")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag == "nav" and self.nav_depth:
            self.nav_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self.nav_depth:
            self.nav_depth -= 1


def load_json(path: Path, findings: list[Finding], code: str) -> object | None:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (OSError, UnicodeError, ValueError) as exc:
        findings.append(Finding(code, path.name, f"cannot read valid UTF-8 JSON: {exc}"))
        return None


def parse_pages(root: Path, findings: list[Finding]) -> dict[str, PageParser]:
    parsed: dict[str, PageParser] = {}
    for name in PAGES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            findings.append(Finding("S001", name, "required regular page is missing"))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(Finding("S002", name, f"cannot read UTF-8 page: {exc}"))
            continue
        parser = PageParser()
        try:
            parser.feed(text)
            parser.close()
        except Exception as exc:
            findings.append(Finding("S003", name, f"HTML parser refused the page: {exc}"))
            continue
        parsed[name] = parser
    return parsed


def check_page_contract(root: Path, parsed: dict[str, PageParser], findings: list[Finding]) -> None:
    required_nav = set(PAGES)
    for name, page in parsed.items():
        expected_body = Path(name).stem
        if page.body_page != expected_body:
            findings.append(Finding("S010", name, f"body data-page must be {expected_body!r}"))
        if page.duplicate_ids:
            findings.append(Finding("S009", name, f"duplicate ids: {sorted(page.duplicate_ids)}"))
        if page.forbidden_tags:
            tags = ", ".join(sorted(set(page.forbidden_tags)))
            findings.append(Finding("S011", name, f"runtime tag present: {tags}"))
        if page.runtime_attributes:
            findings.append(
                Finding("S021", name, f"runtime event attributes present: {sorted(set(page.runtime_attributes))}")
            )
        if page.refresh_meta:
            findings.append(Finding("S022", name, "meta refresh is not accepted"))
        if len(page.stylesheets) != 1:
            findings.append(Finding("S012", name, "must load exactly one stylesheet"))
        else:
            split = urlsplit(page.stylesheets[0])
            if split.path != "assets/style.css" or not split.query:
                findings.append(
                    Finding("S013", name, "stylesheet must be assets/style.css with a version query")
                )
        local_nav = {
            urlsplit(href).path
            for href in page.nav_hrefs
            if not urlsplit(href).scheme and urlsplit(href).path.endswith(".html")
        }
        if local_nav != required_nav:
            missing = sorted(required_nav - local_nav)
            extra = sorted(local_nav - required_nav)
            findings.append(
                Finding("S014", name, f"navigation mismatch; missing={missing}, extra={extra}")
            )
        if page.current_hrefs != [name]:
            findings.append(Finding("S015", name, f"aria-current must point only to {name}"))
        if "proposed" not in page.statuses:
            findings.append(Finding("S016", name, "explicit proposed status is missing"))
        if page.editions != ["cooperative-v1"]:
            findings.append(Finding("S017", name, "footer must carry edition cooperative-v1 once"))
        claim_ids = [claim_id for claim_id, _ in page.claims]
        if len(claim_ids) < 4:
            findings.append(Finding("S026", name, "each page must expose at least four bounded claims"))
        duplicate_claims = sorted({claim_id for claim_id in claim_ids if claim_ids.count(claim_id) > 1})
        if duplicate_claims:
            findings.append(Finding("S027", name, f"duplicate claim ids: {duplicate_claims}"))
        text = (root / name).read_text(encoding="utf-8")
        illustrative_count = sum(status == "illustrative" for _, status in page.claims)
        label_count = len(
            re.findall(
                rf'<span\s+class="example-label"\s*>\s*{re.escape(EXAMPLE_LABEL)}\s*</span>',
                text,
            )
        )
        if label_count != illustrative_count:
            findings.append(
                Finding(
                    "S028",
                    name,
                    f"every illustrative claim needs the exact unexecuted label; claims={illustrative_count}, labels={label_count}",
                )
            )
        for image in page.images:
            src = image.get("src", "")
            if not src:
                findings.append(Finding("S018", name, "image has no src"))
            if not image.get("alt"):
                findings.append(Finding("S019", name, f"image {src!r} has no alt text"))
            for field in ("width", "height"):
                try:
                    if int(image.get(field, "0")) <= 0:
                        raise ValueError
                except ValueError:
                    findings.append(Finding("S020", name, f"image {src!r} lacks positive {field}"))
            if src:
                split = urlsplit(src)
                if split.scheme or split.netloc or split.path.startswith("/"):
                    findings.append(Finding("S023", name, f"image must be a local subpath-safe asset: {src}"))
                else:
                    target = (root / unquote(split.path)).resolve()
                    if not target.is_relative_to(root) or not target.is_file() or target.is_symlink():
                        findings.append(Finding("S024", name, f"image target is missing or unsafe: {src}"))
                    elif target.suffix.lower() != ".webp":
                        findings.append(Finding("S025", name, f"image must use WebP: {src}"))


def check_authority_and_art(
    root: Path, parsed: dict[str, PageParser], findings: list[Finding]
) -> None:
    sentence_locations = []
    for name in PAGES:
        path = root / name
        if path.is_file():
            sentence_locations.extend([name] * path.read_text(encoding="utf-8").count(AUTHORITY_SENTENCE))
    if sentence_locations != ["architecture.html"]:
        findings.append(
            Finding(
                "S029",
                "architecture.html",
                f"protected authority sentence must appear exactly once on architecture.html; found={sentence_locations}",
            )
        )
    architecture = parsed.get("architecture.html")
    if architecture is not None and "authority-boundary" not in architecture.ids:
        findings.append(Finding("S033", "architecture.html", "authority-boundary anchor is missing"))
    pilot = parsed.get("pilot.html")
    if pilot is not None and "braking-authority" not in pilot.ids:
        findings.append(Finding("S034", "pilot.html", "braking-authority anchor is missing"))

    images = [(name, image) for name, page in parsed.items() for image in page.images]
    expected_image = {
        "src": HERO_PATH,
        "width": str(HERO_WIDTH),
        "height": str(HERO_HEIGHT),
    }
    if len(images) != 1 or images[0][0] != "index.html" or any(
        images[0][1].get(field) != value for field, value in expected_image.items()
    ):
        findings.append(
            Finding("S035", HERO_PATH, "the generated hero must be the site's sole content image with fixed intrinsic dimensions")
        )

    hero = root / HERO_PATH
    if not hero.is_file() or hero.is_symlink():
        findings.append(Finding("S036", HERO_PATH, "generated hero is missing or symbolic"))
        return
    try:
        digest = hashlib.sha256(hero.read_bytes()).hexdigest()
        dimensions = webp_dimensions(hero)
    except (OSError, ValueError) as exc:
        findings.append(Finding("S037", HERO_PATH, f"generated hero cannot be verified: {exc}"))
        return
    if digest != HERO_SHA256 or dimensions != (HERO_WIDTH, HERO_HEIGHT) or hero.stat().st_size != HERO_BYTES:
        findings.append(
            Finding(
                "S038",
                HERO_PATH,
                f"generated hero drifted; sha256={digest}, dimensions={dimensions}, bytes={hero.stat().st_size}",
            )
        )

    source_path = root / "evidence" / "sources.json"
    source_document = load_json(source_path, findings, "S039")
    if isinstance(source_document, dict) and isinstance(source_document.get("sources"), list):
        records = [item for item in source_document["sources"] if isinstance(item, dict) and item.get("id") == "GEN-HERO"]
        if len(records) != 1 or records[0].get("revision") != f"sha256:{HERO_SHA256}":
            findings.append(Finding("S039", "evidence/sources.json", "GEN-HERO does not bind the approved digest"))

    prompt_path = root / "assets" / "imagegen-prompts.md"
    try:
        prompt = prompt_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        findings.append(Finding("S067", str(prompt_path.relative_to(root)), f"prompt record cannot be read: {exc}"))
        return
    prompt_markers = (
        "## generated/cooperative-threshold.webp",
        "Production prompt:",
        "Reference roles:",
        "Exclusions:",
        f"WebP, {HERO_WIDTH} × {HERO_HEIGHT}, {HERO_BYTES:,} bytes.",
        HERO_SHA256,
    )
    missing_markers = [marker for marker in prompt_markers if marker not in prompt]
    if missing_markers:
        findings.append(Finding("S068", "assets/imagegen-prompts.md", f"prompt provenance is incomplete: {missing_markers}"))


def check_social_preview(
    root: Path, parsed: dict[str, PageParser], findings: list[Finding]
) -> None:
    social = root / SOCIAL_PATH
    if not social.is_file() or social.is_symlink():
        findings.append(Finding("S090", SOCIAL_PATH, "social preview is missing or symbolic"))
        return
    try:
        digest = hashlib.sha256(social.read_bytes()).hexdigest()
        dimensions = webp_dimensions(social)
    except (OSError, ValueError) as exc:
        findings.append(Finding("S091", SOCIAL_PATH, f"social preview cannot be verified: {exc}"))
        return
    if (
        digest != SOCIAL_SHA256
        or dimensions != (SOCIAL_WIDTH, SOCIAL_HEIGHT)
        or social.stat().st_size != SOCIAL_BYTES
    ):
        findings.append(
            Finding(
                "S092",
                SOCIAL_PATH,
                f"social preview drifted; sha256={digest}, dimensions={dimensions}, bytes={social.stat().st_size}",
            )
        )

    social_url = f"{SITE_ORIGIN}/{SOCIAL_PATH}"
    common_metadata = {
        "og:type": "website",
        "og:site_name": "Shoggoth + Levanto",
        "og:title": "Shoggoth + Levanto",
        "og:description": "A second opinion. Not a second authority.",
        "og:image": social_url,
        "og:image:width": str(SOCIAL_WIDTH),
        "og:image:height": str(SOCIAL_HEIGHT),
        "og:image:alt": "Shoggoth and Levanto meet at a cooperative threshold",
        "twitter:card": "summary_large_image",
        "twitter:title": "Shoggoth + Levanto",
        "twitter:description": "A second opinion. Not a second authority.",
        "twitter:image": social_url,
    }
    for name, page in parsed.items():
        page_url = f"{SITE_ORIGIN}/" if name == "index.html" else f"{SITE_ORIGIN}/{name}"
        expected_metadata = {**common_metadata, "og:url": page_url}
        for key, value in expected_metadata.items():
            if page.metadata.get(key) != [value]:
                findings.append(Finding("S093", name, f"metadata {key} must be exactly {value!r}"))
        if page.canonicals != [page_url]:
            findings.append(Finding("S094", name, f"canonical URL must be exactly {page_url}"))

    source_document = load_json(root / "evidence" / "sources.json", findings, "S095")
    if isinstance(source_document, dict) and isinstance(source_document.get("sources"), list):
        records = [item for item in source_document["sources"] if isinstance(item, dict) and item.get("id") == "GEN-SOCIAL"]
        if len(records) != 1 or records[0].get("revision") != f"sha256:{SOCIAL_SHA256}":
            findings.append(Finding("S095", "evidence/sources.json", "GEN-SOCIAL does not bind the approved digest"))

    prompt_path = root / "assets" / "imagegen-prompts.md"
    try:
        prompt = prompt_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        findings.append(Finding("S096", "assets/imagegen-prompts.md", f"social prompt record cannot be read: {exc}"))
        return
    prompt_markers = (
        "## generated/social-preview.webp",
        "Shoggoth + Levanto",
        "A second opinion. Not a second authority.",
        f"WebP, {SOCIAL_WIDTH} × {SOCIAL_HEIGHT}, {SOCIAL_BYTES:,} bytes.",
        SOCIAL_SHA256,
        "Text inspection after compression:",
    )
    normalized_prompt = " ".join(prompt.split())
    missing_markers = [
        marker for marker in prompt_markers if " ".join(marker.split()) not in normalized_prompt
    ]
    if missing_markers:
        findings.append(Finding("S096", "assets/imagegen-prompts.md", f"social prompt provenance is incomplete: {missing_markers}"))


def local_target(root: Path, page_name: str, href: str) -> tuple[Path, str] | None:
    split = urlsplit(href)
    if split.scheme:
        if split.scheme.lower() not in {"http", "https", "mailto", "tel"}:
            raise ValueError(f"unsupported URI scheme {split.scheme!r}")
        return None
    if split.netloc:
        raise ValueError("scheme-relative links are not accepted")
    if split.path.startswith("/"):
        raise ValueError("root-relative link is unsafe under a Pages subpath")
    raw_path = unquote(split.path)
    relative = Path(page_name).parent / (raw_path or page_name)
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("link leaves the site root")
    return target, unquote(split.fragment)


def check_links(root: Path, parsed: dict[str, PageParser], findings: list[Finding]) -> None:
    for name, page in parsed.items():
        for href in page.hrefs:
            if not href or href.startswith(("mailto:", "tel:")):
                continue
            try:
                target_info = local_target(root, name, href)
            except ValueError as exc:
                findings.append(Finding("S030", name, f"{href!r}: {exc}"))
                continue
            if target_info is None:
                continue
            target, fragment = target_info
            if not target.is_file() or target.is_symlink():
                findings.append(Finding("S031", name, f"local target does not exist: {href}"))
                continue
            if fragment and target.suffix.lower() == ".html":
                target_name = str(target.relative_to(root))
                target_page = parsed.get(target_name)
                if target_page is None or fragment not in target_page.ids:
                    findings.append(Finding("S032", name, f"fragment does not exist: {href}"))


def check_sources(root: Path, findings: list[Finding]) -> set[str]:
    path = root / "evidence" / "sources.json"
    document = load_json(path, findings, "S040")
    if not isinstance(document, dict):
        return set()
    if document.get("schema") != "source-registry-v1":
        findings.append(Finding("S041", "evidence/sources.json", "unsupported schema"))
    edition = document.get("edition")
    if not isinstance(edition, dict) or edition.get("name") != "cooperative-v1":
        findings.append(Finding("S042", "evidence/sources.json", "edition is not cooperative-v1"))
    sources = document.get("sources")
    if not isinstance(sources, list) or not sources:
        findings.append(Finding("S043", "evidence/sources.json", "sources must be a non-empty list"))
        return set()
    ids: set[str] = set()
    required = {"id", "title", "kind", "role", "url", "revision", "observed_at", "note"}
    for index, source in enumerate(sources):
        label = f"source[{index}]"
        if not isinstance(source, dict) or set(source) != required:
            findings.append(Finding("S044", "evidence/sources.json", f"{label} has wrong fields"))
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id):
            findings.append(Finding("S045", "evidence/sources.json", f"{label} has invalid id"))
            continue
        if source_id in ids:
            findings.append(Finding("S046", "evidence/sources.json", f"duplicate id {source_id}"))
        ids.add(source_id)
        for field in ("title", "kind", "role", "observed_at", "note"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                findings.append(Finding("S047", "evidence/sources.json", f"{source_id}.{field} is empty"))
        url = source.get("url")
        if url is not None:
            try:
                split = urlsplit(url) if isinstance(url, str) else None
            except ValueError:
                split = None
            if (
                split is None
                or split.scheme != "https"
                or not split.netloc
                or split.username is not None
                or split.password is not None
            ):
                findings.append(
                    Finding("S048", "evidence/sources.json", f"{source_id}.url must be an HTTPS URL without credentials")
                )
        revision = source.get("revision")
        if revision is not None and (not isinstance(revision, str) or not revision.strip()):
            findings.append(Finding("S049", "evidence/sources.json", f"{source_id}.revision is invalid"))
    return ids


def check_claims(
    root: Path,
    parsed: dict[str, PageParser],
    source_ids: set[str],
    findings: list[Finding],
) -> None:
    path = root / "evidence" / "claims.json"
    document = load_json(path, findings, "S050")
    if not isinstance(document, dict):
        return
    if document.get("schema") != "claim-registry-v1" or document.get("edition") != "cooperative-v1":
        findings.append(Finding("S051", "evidence/claims.json", "schema or edition is wrong"))
    statuses = document.get("statuses")
    if not isinstance(statuses, list) or set(statuses) != ALLOWED_STATUSES or len(statuses) != len(ALLOWED_STATUSES):
        findings.append(Finding("S052", "evidence/claims.json", "status vocabulary is incomplete or duplicated"))
    claims = document.get("claims")
    if not isinstance(claims, list) or not claims:
        findings.append(Finding("S053", "evidence/claims.json", "claims must be a non-empty list"))
        return
    registry: dict[str, dict[str, object]] = {}
    required = {"id", "page", "status", "source_ids", "summary"}
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or set(claim) != required:
            findings.append(Finding("S054", "evidence/claims.json", f"claim[{index}] has wrong fields"))
            continue
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not SOURCE_ID.fullmatch(claim_id):
            findings.append(Finding("S055", "evidence/claims.json", f"claim[{index}] has invalid id"))
            continue
        if claim_id in registry:
            findings.append(Finding("S056", "evidence/claims.json", f"duplicate id {claim_id}"))
        registry[claim_id] = claim
        page = claim.get("page")
        status = claim.get("status")
        refs = claim.get("source_ids")
        if page not in PAGES:
            findings.append(Finding("S057", "evidence/claims.json", f"{claim_id} names unknown page"))
        if status not in ALLOWED_STATUSES:
            findings.append(Finding("S058", "evidence/claims.json", f"{claim_id} has unknown status"))
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            findings.append(Finding("S059", "evidence/claims.json", f"{claim_id}.source_ids is invalid"))
            refs = []
        unknown = sorted(set(refs) - source_ids)
        if unknown:
            findings.append(Finding("S060", "evidence/claims.json", f"{claim_id} has unknown sources {unknown}"))
        if status not in UNSOURCED_STATUSES and not refs:
            findings.append(Finding("S061", "evidence/claims.json", f"{claim_id} requires a source"))
        if not isinstance(claim.get("summary"), str) or not str(claim["summary"]).strip():
            findings.append(Finding("S062", "evidence/claims.json", f"{claim_id}.summary is empty"))
    seen: set[str] = set()
    for page_name, page in parsed.items():
        for claim_id, html_status in page.claims:
            claim = registry.get(claim_id)
            if claim is None:
                findings.append(Finding("S063", page_name, f"unknown claim id {claim_id}"))
                continue
            seen.add(claim_id)
            if claim.get("page") != page_name:
                findings.append(Finding("S064", page_name, f"claim {claim_id} belongs to {claim.get('page')}"))
            if html_status != claim.get("status"):
                findings.append(Finding("S065", page_name, f"claim {claim_id} status does not match registry"))
    missing = sorted(set(registry) - seen)
    if missing:
        findings.append(Finding("S066", "evidence/claims.json", f"claims absent from pages: {missing}"))


def iter_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_symlink():
            yield path, None
        elif path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path, path.read_text(encoding="utf-8")


def check_repository_boundary(root: Path, findings: list[Finding]) -> None:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_dir() and path.name.casefold() in FORBIDDEN_SOURCE_DIRS:
            findings.append(Finding("S077", str(relative), "upstream or reference source mirror is not accepted"))
        if path.is_file() and path.suffix.lower() in RUNTIME_SUFFIXES:
            findings.append(Finding("S078", str(relative), "runtime JavaScript file is not accepted"))
    for path, text in iter_text_files(root):
        relative = str(path.relative_to(root))
        if text is None:
            findings.append(Finding("S070", relative, "symbolic links are not accepted"))
            continue
        if PRIVATE_PATH.search(text):
            findings.append(Finding("S071", relative, "private absolute path is present"))
        if CREDENTIAL.search(text):
            findings.append(Finding("S072", relative, "credential-shaped value is present"))
    css_path = root / "assets" / "style.css"
    if not css_path.is_file() or css_path.is_symlink():
        findings.append(Finding("S073", "assets/style.css", "shared stylesheet is missing"))
    else:
        css = css_path.read_text(encoding="utf-8")
        if re.search(r"(?i)@import\b|url\(\s*['\"]?https?://", css):
            findings.append(Finding("S074", "assets/style.css", "remote CSS asset is present"))
    forbidden_asset_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".avif"}
    assets = root / "assets"
    if assets.is_dir():
        for path in assets.rglob("*"):
            if path.is_file() and path.suffix.lower() in forbidden_asset_suffixes:
                findings.append(Finding("S075", str(path.relative_to(root)), "asset format is not approved"))


def check_budgets(root: Path, findings: list[Finding]) -> None:
    expected = {
        "site.max_html_bytes": 102400,
        "site.css_bytes": 24576,
        "site.max_webp_bytes": 204800,
        "site.index_first_load_bytes": 358400,
        "site.runtime_javascript_bytes": 0,
    }
    document = load_json(root / "evidence" / "metron-budgets.json", findings, "S080")
    if not isinstance(document, dict) or not isinstance(document.get("budgets"), list):
        findings.append(Finding("S081", "evidence/metron-budgets.json", "budget list is missing"))
        return
    observed: dict[str, object] = {}
    required = {"name", "unit", "limit", "variance", "direction"}
    for entry in document["budgets"]:
        if not isinstance(entry, dict) or set(entry) != required:
            findings.append(Finding("S082", "evidence/metron-budgets.json", "budget fields are wrong"))
            continue
        observed[str(entry.get("name"))] = entry.get("limit")
    if observed != expected:
        findings.append(Finding("S083", "evidence/metron-budgets.json", "budget names or limits drifted"))
    for name in PAGES:
        path = root / name
        if path.is_file() and path.stat().st_size > expected["site.max_html_bytes"]:
            findings.append(Finding("S084", name, "HTML byte budget exceeded"))
    css_path = root / "assets" / "style.css"
    if css_path.is_file() and css_path.stat().st_size > expected["site.css_bytes"]:
        findings.append(Finding("S085", "assets/style.css", "CSS byte budget exceeded"))
    for path in (root / "assets").rglob("*.webp") if (root / "assets").is_dir() else []:
        if path.stat().st_size > expected["site.max_webp_bytes"]:
            findings.append(Finding("S086", str(path.relative_to(root)), "WebP byte budget exceeded"))
    try:
        measurements = measure(root)["measurements"]
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        findings.append(Finding("S087", ".", f"complete site measurement failed: {exc}"))
        return
    for name, limit in expected.items():
        value = measurements.get(name)
        if not isinstance(value, int):
            findings.append(Finding("S088", ".", f"measurement {name} is missing or not an integer"))
        elif name == "site.runtime_javascript_bytes" and value != limit:
            findings.append(Finding("S089", ".", f"{name} must remain exactly {limit}; observed {value}"))
        elif name != "site.runtime_javascript_bytes" and value > limit:
            findings.append(Finding("S089", ".", f"{name} exceeds {limit}; observed {value}"))


def check_site(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        return [Finding("S000", str(root), "site root is not a directory")]
    root_pages = {path.name for path in root.glob("*.html") if path.is_file()}
    if root_pages != set(PAGES):
        findings.append(
            Finding(
                "S004",
                ".",
                f"root page inventory mismatch; missing={sorted(set(PAGES) - root_pages)}, extra={sorted(root_pages - set(PAGES))}",
            )
        )
    parsed = parse_pages(root, findings)
    check_page_contract(root, parsed, findings)
    check_authority_and_art(root, parsed, findings)
    check_social_preview(root, parsed, findings)
    check_links(root, parsed, findings)
    source_ids = check_sources(root, findings)
    source_page = parsed.get("sources.html")
    if source_page is not None:
        missing_source_anchors = sorted(source_id for source_id in source_ids if f"src-{source_id}" not in source_page.ids)
        if missing_source_anchors:
            findings.append(
                Finding(
                    "S069",
                    "sources.html",
                    f"registered sources lack public anchors: {missing_source_anchors}",
                )
            )
    check_claims(root, parsed, source_ids, findings)
    try:
        check_repository_boundary(root, findings)
    except (OSError, UnicodeError) as exc:
        findings.append(Finding("S076", ".", f"repository boundary read failed: {exc}"))
    check_budgets(root, findings)
    return sorted(set(findings))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="site root")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    findings = check_site(root)
    if findings:
        for finding in findings:
            print(f"ERROR {finding.render()}", file=sys.stderr)
        print(f"site check failed: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print(f"site check clean: {len(PAGES)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
