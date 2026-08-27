# ADR-003: Bind claim statuses to source editions

## Status

Accepted, 2026-08-27.

## Context

The site combines repository evidence, mutable vendor documentation, a vendor
benchmark, observed HTTP behaviour, prior-art sites, proposed architecture and
illustrative fixtures. One undifferentiated source badge would make those
classes look equally established.

Levanto's public pages may change without this repository changing. Shoggoth's
current behaviour is tied to a commit. The prior comparison and Plaidcat audits
showed that status belongs to the precise clause it supports.

## Decision

Keep machine-readable source and claim registries. Each claim names its page,
one status and the source ids that support it. Repository sources carry a
commit; mutable pages carry an observation date and a digest where one was
captured. Proposed and illustrative claims remain visibly separate from
current and vendor-reported ones.

## Alternatives

- Put one source list at the bottom of each page. It is readable, but does not
  show which source supports which clause.
- Copy source text into the repository. That would freeze words, but increases
  copying and licensing risk while hiding whether the original moved.
- Mark every official statement verified. Official material is authoritative
  for a vendor's stated contract, not independent proof of performance,
  reliability or suitability.

## Consequences

An edition-wide check refuses unknown source ids, status drift and a mutable
source digest change without review. Readers can distinguish what the source
says, what this study infers and what the architecture merely proposes. The
registries add upkeep whenever a source edition changes, which is the intended
cost of changing a public claim.
