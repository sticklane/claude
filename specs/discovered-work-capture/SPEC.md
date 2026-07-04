# Discovered-work capture in /drain

Status: ready

> Re-homed 2026-07-03 from `specs/beads-integration` (now closed). This is the
> zero-dependency half of that spec — the discovered-work verdict contract —
> decoupled from the withdrawn beads queue backend. The three interview
> decisions below were recorded before the beads full exit and are unaffected
> by it. Recommend a `/critique` pass before dispatch.

## Problem

When a drain/build worker finds NEW work mid-task ("this module also has X
broken"), the toolkit has nowhere to put it — it becomes a deferred question
(wrong channel: there is nothing to ask) or vanishes with the worker's
context. The `discovered-from` concept (from the Beads research; see
`docs/external-playbooks.md`) names exactly this edge, and we can adopt it at
zero dependency cost: capture the discovery in the worker's verdict and let
drain record it, without a new backend or binary.

## Solution

Discovered work travels **in the worker's verdict and drain records it** —
preserving the "workers report, drain records" state model — as a
`## Discovered` entry in the source task file plus a `draft` stub task file.
Workers never write to files. Recording happens only for the verdict drain
finally routes (merged tournament winner or final attempt); discarded
candidates' discoveries are dropped. Draft stubs are never dispatchable and
are promoted manually. Files touched:
`.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`,
`antigravity/.agents/workflows/drain.md`, `docs/external-playbooks.md`.

## Requirements

- R1 (verdict contract): both drain worker prompts in
  `.claude/skills/drain/reference.md` (background and headless) extend the
  final-message contract with an optional block: `Discovered:` — zero or more
  entries, each "title — one-line rationale — blocking or non-blocking".
  Workers never write discoveries to files (the existing queue-state and
  untrusted-data clauses stand unchanged).
- R2 (drain records): drain's step-3 collect handles a verdict's Discovered
  entries for every verdict type — but only from the verdict drain finally
  routes (the merged tournament winner or the final attempt; discarded
  candidates' and superseded attempts' discoveries are dropped),
  deduplicating by title against the source task's existing `## Discovered`
  entries: append each to a `## Discovered` section in the source task file
  (main checkout, committed like all drain bookkeeping), and for each entry
  scaffold a stub task file `specs/<slug>/tasks/NN-<short-slug>.md` with
  `Status: draft`, `Discovered-from: <source task file>`, the rationale as
  Goal, and an `## Acceptance` section containing only
  `<!-- draft: needs runnable criteria before promotion -->`. A discovery's
  blocking-or-not is recorded in the stub header only (no edits to the source
  task's `Depends on:` — a human decides at promotion time). Stub numbering:
  NN = highest task number already present in that tasks directory + 1, chosen
  at collect time. Convention, stated where drain's inventory defines
  dependencies: `Depends on:` entries may be task numbers (within-spec) or
  repo-relative task-file paths (cross-spec); drain inventory accepts both.
- R3 (draft status): the status table in drain reference.md gains a `draft`
  row: never dispatchable, excluded from the batch interview and from "queue
  empty" (a queue with only draft+done reports drained, listing drafts for
  human promotion; a `pending` task whose UNMET dependencies are all drafts
  reports the same way — "drained pending promotion" — rather than leaving
  step 4 without a terminal condition). Promotion is manual: a human (or an
  /idea / /breakdown pass) replaces the placeholder Acceptance with runnable
  criteria and flips `draft` → `pending`.
- R4 (antigravity mirror): `antigravity/.agents/workflows/drain.md` mirrors
  R1–R3 fully (Discovered verdict contract, drain-records collect, draft
  status), per CLAUDE.md's `.claude/` → `antigravity/` mirror rule.
- R5 (research record): `docs/external-playbooks.md` gains a "Beads" entry:
  what was adopted (discovered-from as R1–R3), that the optional beads queue
  backend was evaluated and declined in the 2026-07-03 full exit (Dolt
  rewrite churn, binary dependency, loss of diffable committed state), and the
  adoption triggers under the literal heading-phrase "adoption triggers"
  (queues ≫ 10 tasks or multi-repo; genuinely parallel claiming; recurring
  queue-state defects), with source links.
- R6 (versioning): the implementing change bumps `.claude-plugin/plugin.json`'s
  minor version by exactly one from whatever value it finds (skill behavior
  changes); if another spec's implementation lands in the same commit-set with
  its own mandated bump, one combined single-minor bump satisfies both.

## Out of scope

- Any beads queue backend, feature-detection, or bd CLI lifecycle mapping —
  withdrawn with the 2026-07-03 full exit; see `specs/beads-integration`
  (closed) and `~/specs/beads-full-exit/`.
- Auto-promotion of draft stubs (human / idea-pass judgment by design).
- Editing the source task's `Depends on:` when a blocking discovery is
  recorded (the blocking flag lives in the stub header; a human wires
  dependencies at promotion).

## Acceptance criteria

- [ ] `test "$(grep -c 'Discovered:' .claude/skills/drain/reference.md)" -ge 2` — both worker prompts carry the verdict block (R1)
- [ ] `grep -q "## Discovered" .claude/skills/drain/SKILL.md && grep -q "Discovered-from:" .claude/skills/drain/reference.md` — collect mechanics + stub header defined (R2)
- [ ] ``grep -qF '| `draft` |' .claude/skills/drain/reference.md && grep -qi "promotion" .claude/skills/drain/reference.md`` (R3)
- [ ] `grep -q 'Discovered:' antigravity/.agents/workflows/drain.md && grep -qi 'draft' antigravity/.agents/workflows/drain.md && grep -q '## Discovered' antigravity/.agents/workflows/drain.md` — mirror carries the R1–R3 markers (R4)
- [ ] `grep -qi "beads" docs/external-playbooks.md && grep -qi "adoption triggers" docs/external-playbooks.md` (R5)
- [ ] `.claude-plugin/plugin.json` minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R6)
- [ ] End to end (markdown mode): a fresh session executing drain's collect against a mock DONE verdict containing one non-blocking Discovered entry produces the `## Discovered` append plus a `draft` stub with `Discovered-from:` and placeholder acceptance, and a subsequent inventory pass does NOT dispatch the draft (manual dry-read until the eval harness covers /drain).

## Open questions

(none — the three decisions are recorded in Solution; recommended options
adopted, reversible before implementation.)
