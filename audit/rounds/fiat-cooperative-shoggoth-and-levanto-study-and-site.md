## Step 1, round 1 -- 2026-08-27T17:33:10Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=not-applicable; confidence-misread=reviewed; service-failure=not-applicable; schema-drift=not-applicable; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=not-applicable; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=not-applicable; image-cache-layout=not-applicable; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=not-applicable; pages-cache=not-applicable; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: browser-rendered contrast, keyboard, narrow-screen and print behaviour; live Pages publication and cache behaviour; future Sage adapter network, schema and data handling; Step 2 generated-image bytes and provenance

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | scripts/check_site.py; scripts/measure_site.py | The static-only checker allowed runtime URI schemes, event attributes, meta refresh and JavaScript files, while the measurement producer always reported zero JavaScript bytes. | fixed in this round |
| S1-R1-02 | medium | scripts/check_site.py | Page inventory, duplicate fragment ids and non-local or non-WebP image sources were not rejected. | fixed in this round |
| S1-R1-03 | medium | scripts/check_site.py | Source URLs with an HTTPS scheme but no authority or with embedded credentials passed validation; malformed URLs could terminate the check. | fixed in this round |
| S1-R1-04 | medium | scripts/check_site.py | No path rule refused copied mascot or prior-art source directories despite the source-copying boundary. | fixed in this round |
| S1-R1-05 | low | scripts/run_tests.py | The test runner removed the repository root from `sys.path` before test methods ran, so runtime imports could fail after successful discovery. | fixed in this round |

Leads not pursued: none

## Step 1, round 2 -- 2026-08-27T17:35:18Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=not-applicable; confidence-misread=reviewed; service-failure=not-applicable; schema-drift=not-applicable; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=not-applicable; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=not-applicable; image-cache-layout=not-applicable; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=not-applicable; pages-cache=not-applicable; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: browser-rendered contrast, keyboard, narrow-screen and print behaviour; live Pages publication and cache behaviour; future Sage adapter network, schema and data handling; Step 2 generated-image bytes and provenance

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | scripts/check_site.py | JSON objects with duplicate keys were accepted with last-value-wins parsing, so source, claim or budget bytes could hide an overridden field. | fixed in this round |

Leads not pursued: none

## Step 1, round 3 -- 2026-08-27T17:38:23Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=not-applicable; confidence-misread=reviewed; service-failure=not-applicable; schema-drift=not-applicable; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=not-applicable; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=not-applicable; image-cache-layout=not-applicable; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=not-applicable; pages-cache=not-applicable; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: browser-rendered contrast, keyboard, narrow-screen and print behaviour; live Pages publication and cache behaviour; future Sage adapter network, schema and data handling; Step 2 generated-image bytes and provenance

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none

## Step 2, round 1 -- 2026-08-27T18:16:05Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=reviewed; confidence-misread=reviewed; service-failure=reviewed; schema-drift=reviewed; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=reviewed; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=reviewed; image-cache-layout=reviewed; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=not-applicable; pages-cache=not-applicable; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: keyboard and print behaviour reserved for Step 3; live Pages publication and cache behaviour; a future Sage adapter's live network, schema and data handling

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | scripts/check_site.py | Duplicate HTML attributes were collapsed with last-value-wins parsing, while a browser may honour a different `src`, `href`, metadata or status value. | fixed in this round |
| S2-R1-02 | medium | scripts/check_site.py | A `base` element, plain-HTTP link, resource-hint link, inline style or active media attribute could change resolution or create an unreviewed network surface without failing the static contract. | fixed in this round |
| S2-R1-03 | medium | scripts/check_site.py; scripts/measure_site.py | CSS `url()` references and undeclared asset types could load bytes that the first-load measurement did not inventory. | fixed in this round |

Leads not pursued: none

## Step 2, round 2 -- 2026-08-27T18:18:43Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=reviewed; confidence-misread=reviewed; service-failure=reviewed; schema-drift=reviewed; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=reviewed; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=reviewed; image-cache-layout=reviewed; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=not-applicable; pages-cache=not-applicable; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: keyboard and print behaviour reserved for Step 3; live Pages publication and cache behaviour; a future Sage adapter's live network, schema and data handling

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | scripts/check_site.py | Page links with an HTTPS scheme but no authority, or with embedded credentials, passed the HTML link boundary. | fixed in this round |
| S2-R2-02 | medium | scripts/check_site.py | Inline SVG remained available as an unreviewed external-image and reuse surface despite the site's no-SVG design boundary. | fixed in this round |
| S2-R2-03 | medium | scripts/check_site.py; scripts/measure_site.py | CSS `image-set()` could reference an allowed image without adding its bytes to the index first-load measurement. | fixed in this round |

Leads not pursued: none

## Step 2, round 3 -- 2026-08-27T18:19:23Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=reviewed; confidence-misread=reviewed; service-failure=reviewed; schema-drift=reviewed; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=reviewed; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=reviewed; image-cache-layout=reviewed; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=not-applicable; pages-cache=not-applicable; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: keyboard and print behaviour reserved for Step 3; live Pages publication and cache behaviour; a future Sage adapter's live network, schema and data handling

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none

## Step 3, round 1 -- 2026-08-27T18:34:19Z

Audit schema: fiat-audit-round/v2

Covered: authority-inversion=reviewed; status-collapse=reviewed; policy-drift=reviewed; confidence-misread=reviewed; service-failure=reviewed; schema-drift=reviewed; credential-leak=reviewed; content-egress=reviewed; diagnostic-retention=reviewed; prompt-injection=reviewed; source-drift=reviewed; skill-surface-divergence=reviewed; benchmark-overclaim=reviewed; endorsement-drift=reviewed; source-copying=reviewed; image-provenance=reviewed; image-cache-layout=reviewed; link-integrity=reviewed; page-accessibility=reviewed; asset-budget=reviewed; pages-publication=reviewed; pages-cache=reviewed; test-runner-contract=reviewed; hidden-runtime=reviewed

Not checked: the live Pages build and cache response, which remain reserved for the integration receipt; any future Sage adapter's live network, schema and data handling

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | scripts/public_smoke.py | A public site carrying the expected edition marker, status and content type passed even when its bytes differed from the checked local files, so a stale build from the same edition could earn a clean readback. | fixed in this round |
| S3-R1-02 | medium | scripts/public_smoke.py | The complete-readback validator ignored content type, digest, edition, URL, deployment-context shape and local-match fields once target names, status and positive byte counts were present. | fixed in this round |
| S3-R1-03 | low | scripts/public_smoke.py | An output unlink or write failure escaped the bounded refusal path and could emit a traceback containing a private local path. | fixed in this round |

Leads not pursued: none
