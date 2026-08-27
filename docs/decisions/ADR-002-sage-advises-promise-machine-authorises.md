# ADR-002: Sage advises and the Promise Machine authorises

## Status

Accepted, 2026-08-27.

## Context

Shoggoth's current Promise Machine records the evidence needed for a declared
transition and refuses the transition when that evidence is absent, stale or
insufficient. Levanto's public material describes Sage as a probabilistic API
for closed-ended decisions. Those contracts answer different questions.

A policy classifier may help with semantic routing, refusal or escalation. A
probabilistic result is not the same thing as proof that an evidence gate
passed, and confidence is not a correctness guarantee.

## Decision

Sage may route, refuse or escalate; Sage alone does not authorise a Promise
Machine transition.

For any later adapter, deterministic local code validates and redacts a bounded
packet, checks the Sage response schema, applies status and confidence policy,
and chooses a low-consequence route, review or refusal. The existing Promise
Machine still decides whether the dependent transition is authorised.

## Alternatives

- Treat Sage as the final policy engine. This is simpler to wire, but it
  collapses probabilistic classification into deterministic authority.
- Use Sage only as prose advice with no structured record. This avoids direct
  authority, but it cannot be joined reliably to the input, policy or later
  route.
- Exclude Sage from every hand-off. This preserves the current system, but it
  does not test the cooperative question in the request.

## Consequences

The first pilot is asymmetric: Sage may add friction by requesting review or
refusal, but cannot remove a deterministic gate or independently permit a
consequential transition. Each future decision record needs the input digest,
policy digest, question id, decision kind, model id, time, response status and
local route. Any automatic low-consequence route needs a separately accepted
policy and measured examples.
