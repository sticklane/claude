# Critique findings — READY WITH NITS (2026-07-17, /idea intake)

SPEC.md content hash at settled verdict: `sha256:e6be55c258dbfd0ccd1b59321a883097e836f62ee2dd2d4bc2fb3fc0dc3dd9fd`

Critic verdict (round 4 of 4): READY WITH NITS. Three prior rounds found
and fixed blockers (a card link built from data the reused adapter
strips, an unbuildable `unblock.step` display requirement, a
grep/summary-count contradiction, a non-importable acceptance command);
this round found none, only optional polish. Spec is agent-ready for
`/breakdown` as-is.

Optional nits (none block; apply only if convenient):

1. **R4's `repo:spec-slug` badge and priority-if-non-empty have no
   dedicated acceptance check** (confidence ~65). A worker could pass every
   grep (`href="/spec/"`, `data-text=`) while omitting the visible badge or
   priority field. Optional fix: add a grep anchoring the badge class, or a
   line in the e2e check asserting the badge/priority is visible.

2. **Problem-section citation `workboard.py:245-264` labeled "Status:
   header parsing"** (confidence ~~60) actually points at the status
   vocabulary sets, not the `Status:`-line parse itself (~~:314).
   Motivational prose only, not load-bearing on any requirement or
   acceptance check.

3. **R2's acceptance check exercises one representative status per
   column** (confidence ~55), not every synonym (e.g. `pending`/`todo`/
   `ready` all map to Pending, but only one is asserted). The mapping is a
   verified clean partition, so real-world risk is low.
