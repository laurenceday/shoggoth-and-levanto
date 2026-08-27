# ADR-001: Publish a static source-bound Pages site

## Status

Accepted, 2026-08-27.

## Context

The request is to explain a cooperative Shoggoth and Levanto design through an
existing GitHub Pages repository. A live Sage adapter would add a credential,
data egress, retention, availability, abuse, cost and telemetry boundary. None
of those operational choices is needed to test whether the proposed hand-off
is understandable and source-bound.

The target already publishes `main:/` through GitHub Pages. It has no build
system, application server or dependency tree.

## Decision

Publish plain HTML5, one repository-owned CSS file, original compressed WebP
art and Python standard-library checks, with no runtime JavaScript or live Sage
call.

## Alternatives

- Build a live Sage adapter now. This would demonstrate an API call, but it
  would force unresolved choices about keys, data classes, retention, failure
  policy and authority before the documentary boundary is accepted.
- Add a framework or static-site generator. It could reduce repeated markup,
  but it would add a toolchain and generated output to ten small pages.
- Copy the Plaidcat site. That would be quick, but its content and information
  architecture answer a different question. Only its presentation grammar is
  prior art here.
- Add a GitHub deployment workflow. The repository already has a Pages source,
  so a second publication path would change hosting without a need.

## Consequences

The site works from a repository checkout and GitHub Pages without a build
step. Every claim and asset is visible in the reviewed tree. A future live
adapter requires a new study, threat boundary, telemetry design and deployment
decision. Repeated navigation is accepted as the cost of having no generator.

The supplied mascot kit remains generation-only. The repository may hold the
final original site image and its prompt record, but not the kit or its source
images. No Levanto logo is licensed by this decision.
