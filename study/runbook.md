# Runbook: cooperative Shoggoth and Levanto site

> Public repository copy. The controller's host-local plugin path is rendered
> as `$PLUGIN_ROOT` here so no private absolute path enters the published tree.

This runbook derives from `.hexaemeron/study.md` at the receipted digest held by
Fiat. It builds one static GitHub Pages edition. It does not add a live Sage
client, send a prompt to Sage, or change the authority of the Promise Machine.

The three steps are one ordered capability. Each step leaves the repository
green and is small enough for its own audit, prose check, signed commit and
stacked pull request. Later steps may rely only on the controller-recorded exit
state of earlier steps.

The active contracts are the pinned Wildcat Skills editions named in the
study: [Protasis](https://github.com/wildcat-finance/skills/blob/934c47104e9e23d05c8aa3e8b15e8e36481c03fc/plugins/hexaemeron/skills/protasis/SKILL.md),
[Phylax](https://github.com/wildcat-finance/skills/blob/934c47104e9e23d05c8aa3e8b15e8e36481c03fc/plugins/hexaemeron/skills/phylax/SKILL.md),
[Ephoros](https://github.com/wildcat-finance/skills/blob/934c47104e9e23d05c8aa3e8b15e8e36481c03fc/plugins/hexaemeron/skills/ephoros/SKILL.md),
[Metron](https://github.com/wildcat-finance/skills/blob/934c47104e9e23d05c8aa3e8b15e8e36481c03fc/plugins/hexaemeron/skills/metron/SKILL.md),
[Elenchus](https://github.com/wildcat-finance/skills/blob/934c47104e9e23d05c8aa3e8b15e8e36481c03fc/plugins/hexaemeron/skills/elenchus/SKILL.md),
and [Hypomnema](https://github.com/wildcat-finance/skills/blob/934c47104e9e23d05c8aa3e8b15e8e36481c03fc/plugins/hexaemeron/skills/hypomnema/SKILL.md).

## Step 1: Establish the source-bound static site contract

**Goal.** Create the static page shell, source and claim registries, repository
checks, decision records and committed specification copies that every later
page must obey.

**Entry.** Commit `7c0b5fad20ae6da06d3e254d2915f3d23ec2b6e0` on the
controller-created Step 1 branch, with the study and this runbook receipted and
no product file changed.

**Exit.** All ten root pages render a shared navigation and explicit proposal
status; the evidence registries validate; every local target resolves; the
runner writes a fresh non-empty structured report; the MIT licence, Python pin,
CI workflow, three ADRs and committed study/runbook copies exist. These exact
commands exit zero:

```bash
python3 scripts/check_site.py --root .
python3 scripts/run_tests.py --report .elenchus/site.json
python3 -m unittest discover -s tests -v
```

**Files.** `.github/workflows/site-check.yml`, `.gitignore`, `.python-version`,
`LICENSE`, `README.md`, `index.html`, `sage.html`, `shoggoth.html`,
`handoffs.html`, `architecture.html`, `policy.html`, `pilot.html`,
`limits.html`, `engineering-primer.html`, `sources.html`, `assets/style.css`,
`docs/decisions/ADR-001-static-source-bound-pages-site.md`,
`docs/decisions/ADR-002-sage-advises-promise-machine-authorises.md`,
`docs/decisions/ADR-003-claim-status-and-source-editions.md`,
`evidence/sources.json`, `evidence/claims.json`,
`evidence/metron-budgets.json`, `scripts/check_site.py`,
`scripts/measure_site.py`, `scripts/run_tests.py`, `study/study.md`,
`study/runbook.md`, and `tests/test_site.py`.

**Tests.** Add standard-library tests for the page inventory, shared
navigation, source and claim schemas, status vocabulary, local links and
fragments, versioned CSS URL, static-only rule, forbidden local paths,
credential patterns and report freshness. The runner refuses zero discovered
tests and records the exact count.

Test command: `python3 scripts/run_tests.py --report {report}`

Report format: `unittest-json-v1`

Report file: `.elenchus/site.json`

**Disciplines.** phylax: this step opens public-source ingestion, HTML output,
CI and path/secret checks. ephoros: the structured runner and checker name the
page, target and rule needed to explain a failed build; no unattended runtime
exists. metron: budgets and the measurement producer are fixed here, but no
accepted baseline or speed claim exists yet. elenchus: no failure is in hand;
the source-bound runner contract is established for later audit fixes.
hypomnema: the static deployment, authority split and claim-status model are
expensive to reverse, so ADR-001 through ADR-003 record them.

## Step 2: Publish the cooperative architecture and original artwork

**Goal.** Replace the page shells with source-labelled accounts of Sage,
Shoggoth, their proposed hand-offs, pilot limits and engineering controls, then
add one original compressed hero image.

**Entry.** The controller-recorded Step 1 merge is the first parent of the run
branch; Step 1 checks, audit, prose and push receipts are green; no source or
claim edition has changed since that receipt.

**Exit.** The ten pages answer the study's page questions; every factual clause
has a claim id, status and source binding; the protected authority sentence is
present; all Sage examples say illustrative and unexecuted; the hero is an
original WebP of at most 200 KiB with intrinsic dimensions and a recorded
prompt/reference-role entry. These exact commands exit zero:

```bash
python3 scripts/check_site.py --root .
python3 scripts/measure_site.py --root . --out .metron/site-run.json
python3 scripts/run_tests.py --report .elenchus/site.json
```

**Files.** `index.html`, `sage.html`, `shoggoth.html`, `handoffs.html`,
`architecture.html`, `policy.html`, `pilot.html`, `limits.html`,
`engineering-primer.html`, `sources.html`, `assets/style.css`,
`assets/generated/cooperative-threshold.webp`, `assets/imagegen-prompts.md`,
`evidence/sources.json`, `evidence/claims.json`, `scripts/check_site.py`,
`scripts/measure_site.py`, and `tests/test_site.py`.

**Tests.** Extend the standard-library suite for every claim id, source id and
status badge; the protected authority sentence; illustrative Sage labels;
image type, dimensions and byte limit; first-load budget; complete navigation;
and the absence of copied mascot-kit digests or remote runtime assets.

Test command: `python3 scripts/run_tests.py --report {report}`

Report format: `unittest-json-v1`

Report file: `.elenchus/site.json`

**Disciplines.** phylax: generated art and researched claims cross into public
repository bytes, so provenance, secret, path and remote-asset checks apply.
ephoros: each failed claim, link or asset check names the page and identifier;
the site still has no unattended application. metron: the final hero and page
content enter the fixed byte budget and are measured with the Step 1 producer.
elenchus: no failure is assumed; any audit fix must reproduce against its
unfixed parent through the declared runner. hypomnema: no new expensive choice
is planned; the content implements ADR-001 through ADR-003 and must amend them
before changing those choices.

## Step 3: Harden, measure and demonstrate the GitHub Pages edition

**Goal.** Complete accessibility, responsive, print, cache, measurement and
publication checks, then run the local HTTP demo that mirrors the Pages path.

**Entry.** The controller-recorded Step 2 merge is the first parent of the run
branch; Step 2 checks, audit, prose and push receipts are green; its generated
asset and evidence editions are unchanged.

**Exit.** Desktop, narrow-screen and print review records have no open layout
or accessibility issue; CSS is cache-versioned; the accepted Metron baseline
matches the final files; README commands work; local HTTP smoke checks every
page and asset under the repository subpath; and the public smoke command is
ready for the integration receipt. These exact commands exit zero:

```bash
python3 scripts/check_site.py --root .
python3 scripts/measure_site.py --root . --out .metron/site-run.json
python3 "$PLUGIN_ROOT/skills/metron/scripts/metron.py" check --budgets evidence/metron-budgets.json --baseline evidence/metron-baseline.json --run .metron/site-run.json
python3 scripts/run_tests.py --report .elenchus/site.json
python3 scripts/demo_site.py --root . --port 4173 --base-path /shoggoth-and-levanto/ --expected-edition cooperative-v1
```

After the integration merge and successful Pages build, run the same public
inventory against the deployed base:

```bash
python3 scripts/public_smoke.py --base-url https://laurenceday.github.io/shoggoth-and-levanto/ --expected-edition cooperative-v1 --out .hexaemeron/pages-readback.json
```

**Files.** `README.md`, all ten root HTML pages, `assets/style.css`,
`evidence/metron-baseline.json`, `scripts/check_site.py`,
`scripts/measure_site.py`, `scripts/demo_site.py`, `scripts/public_smoke.py`,
`tests/test_site.py`, and `study/visual-review.md`.

**Tests.** Extend the standard-library suite for responsive image rules,
focus-visible states, reduced motion, print visibility, cache-versioned local
assets, subpath-safe links, the `cooperative-v1` edition marker, HTTP status and
content-type checks, and refusal of a stale or empty public readback.

Test command: `python3 scripts/run_tests.py --report {report}`

Report format: `unittest-json-v1`

Report file: `.elenchus/site.json`

**Disciplines.** phylax: the local server and public smoke tool accept a path or
URL, so fixed schemes, loopback binding, timeouts, redirect limits and output
boundaries apply. ephoros: the one-shot readback records merge/build context,
HTTP status, content type, edition and failed target; no persistent monitor or
alert is claimed. metron: this step records the first accepted baseline and
checks the same producer against the study budgets. elenchus: responsive,
cache, subpath and smoke failures are reproduced and guarded through the
declared runner. hypomnema: no alert runbook is created because no unattended
monitor exists; the README is the durable operator entry point.

## Build boundary

Always: preserve claim statuses, source editions, the protected authority
sentence, static-only delivery, intrinsic image dimensions, no-runtime-script
policy, signed Fiat provenance and a green structured report at every step.

Ask first: adding a dependency, live Sage call, credential, form, analytics,
backend, non-GitHub deployment, Levanto mark, third-party font or automatic
consequential route.

Never: put a key in browser code, transmit a real agent packet, copy the mascot
kit into the repository, present vendor claims as independently measured,
present proposed integration as current, let Sage authorise a Promise Machine
transition, or merge outside the controller order.

## Readiness report

Ready to build. The Protasis checklist is 18 of 18: all twelve study items are
answered; the prior pull requests and audit sources are accounted for; the
five discipline contracts are cited; success criteria and step exits name
commands; boundaries and trade-offs are explicit; every step has the required
fields and runner contract; Step 1 scaffolds; Step 3 demonstrates; and the
dependency order is fixed. Failed checks: none.

The study establishes the source and authority model. It assumes the public
Pages source remains `main:/` and the authenticated publisher can complete the
upstream merge. The merge permission cannot be settled by the build itself, so
Fiat must verify it again at the integration gate.

### Amendment -- 2026-08-27

**What changed.** Complete replacement Exit: All ten root pages render a
shared navigation and explicit proposal status; the evidence registries
validate; every local target resolves; the runner writes a fresh non-empty
structured report; the Python pin, repository-owned local CI entry point,
three ADRs and committed study/runbook copies exist; and the README records
that the repository currently grants no reuse licence. The exact commands
`python3 scripts/check_site.py --root .`, `python3 scripts/run_tests.py
--report .elenchus/site.json`, `python3 scripts/check_all.py`, and `python3 -m
unittest discover -s tests -v` exit zero. Complete replacement Files:
`.gitignore`, `.python-version`, `README.md`, `index.html`, `sage.html`,
`shoggoth.html`, `handoffs.html`, `architecture.html`, `policy.html`,
`pilot.html`, `limits.html`, `engineering-primer.html`, `sources.html`,
`assets/style.css`,
`docs/decisions/ADR-001-static-source-bound-pages-site.md`,
`docs/decisions/ADR-002-sage-advises-promise-machine-authorises.md`,
`docs/decisions/ADR-003-claim-status-and-source-editions.md`,
`evidence/sources.json`, `evidence/claims.json`,
`evidence/metron-budgets.json`, `scripts/check_all.py`,
`scripts/check_site.py`, `scripts/measure_site.py`, `scripts/run_tests.py`,
`study/study.md`, `study/runbook.md`, and `tests/test_site.py`.

**Why.** The receipted study names a new deployment workflow and a chosen
licence as ask-first boundaries. No operator choice authorised either one, so
the scaffold must preserve the existing Pages configuration and record the
current no-licence state. A local entry point supplies the CI command without
changing repository or hosting settings.

**Steps touched.** Step 1's Exit and Files fields.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-27

**What changed.** Complete replacement Exit: Desktop, narrow-screen and print
review records have no open layout or accessibility issue; CSS is
cache-versioned; the accepted Metron baseline matches the final files; README
commands work; local HTTP smoke checks every page and asset under the
repository subpath; and the public smoke command is ready for the integration
receipt. The exact commands `python3 scripts/check_site.py --root .`, `python3
scripts/measure_site.py --root . --out .metron/site-run.json`, `python3
"$PLUGIN_ROOT/skills/metron/scripts/metron.py" check --budgets
evidence/metron-budgets.json --baseline evidence/metron-baseline.json --run
.metron/site-run.json`, `python3 scripts/run_tests.py --report
.elenchus/site.json`, and `python3 scripts/demo_site.py --root . --port 4173
--base-path /shoggoth-and-levanto/ --expected-edition cooperative-v1` exit
zero. After the integration merge and successful Pages build, `python3
scripts/public_smoke.py --base-url
https://laurenceday.github.io/shoggoth-and-levanto/ --expected-edition
cooperative-v1 --out .hexaemeron/pages-readback.json` exits zero against the
deployed base.

**Why.** The baseline Step 3 command named one host's absolute plugin path.
The study refuses private local paths in public repository bytes, and the
portable plugin root already governs the same pinned checker.

**Steps touched.** Step 3's Exit field.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
