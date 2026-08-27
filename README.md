# Shoggoth and Levanto

A source-bound proposal for a cooperative guardrail layer between Shoggoth's
evidence-gated agent hand-offs and Levanto's Sage decision API.

This repository is a static research site. It does not call Sage, carry a Sage
key, or let a model authorise a Promise Machine transition. The proposed split
is narrower: Sage may classify a closed-ended policy question, while local
deterministic policy and the existing Promise Machine decide what happens next.

The intended public edition is
[laurenceday.github.io/shoggoth-and-levanto](https://laurenceday.github.io/shoggoth-and-levanto/).

## Evidence edition

- Site edition: `cooperative-v1`
- Shoggoth source: `wildcat-finance/skills@934c47104e9e23d05c8aa3e8b15e8e36481c03fc`
- Levanto public sources observed: 2026-08-27
- Claim registry: `evidence/claims.json`
- Source registry: `evidence/sources.json`

The pages label current, vendor-reported, inferred, proposed, illustrative and
unknown material separately. A source label supports only the clause tied to
its claim id.

## Local checks

The repository pins Python 3.13.15 and uses only its standard library.

```bash
python3 scripts/check_site.py --root .
python3 scripts/run_tests.py --report .elenchus/site.json
python3 scripts/check_all.py
python3 scripts/measure_site.py --root . --out .metron/site-run.json
```

`scripts/check_all.py` is the local CI entry point. No deployment workflow is
added: the repository already publishes GitHub Pages from `main:/`.

## Page map

- `index.html`: cooperative thesis and status
- `sage.html`: public Sage contract
- `shoggoth.html`: Shoggoth's evidence and delivery boundary
- `handoffs.html`: present agent hand-offs
- `architecture.html`: proposed checkpoint architecture
- `policy.html`: decision kinds and local routing
- `pilot.html`: reversible pilot design
- `limits.html`: failure and trust boundaries
- `engineering-primer.html`: later implementation constraints
- `sources.html`: source and claim edition

The receipted study and runbook live under `study/`. The three standing design
decisions live under `docs/decisions/`.

## Licence status

No licence has been granted for this repository. Public visibility does not by
itself grant permission to copy, modify or redistribute its contents.
