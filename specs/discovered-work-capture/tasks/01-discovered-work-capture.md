# Task 01: Discovered-work capture in /drain (verdict contract, collect, draft status)

Status: pending
Depends on: ../../chaining-antipatterns/tasks/01-authority-layer.md, ../../chaining-antipatterns/tasks/03-antipattern-guards.md
Budget: 40 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4 antigravity mirror, R5 research record, R6 versioning)

## Goal

Workers can report NEW work found mid-task and drain records it, without
breaking the "workers report, drain records" state model. Both drain
worker prompts gain an optional `Discovered:` verdict block (zero or more
entries, each "title — one-line rationale — blocking or non-blocking";
workers never write discoveries to files). Drain's step-3 collect records
discoveries from the finally-routed verdict only (merged tournament
winner or final attempt; discarded candidates' and superseded attempts'
discoveries are dropped): dedup by title against the source task's
existing `## Discovered` entries, append each to a `## Discovered`
section in the source task file, and scaffold a stub task file
`specs/<slug>/tasks/NN-<short-slug>.md` with `Status: draft`,
`Discovered-from: <source task file>`, rationale as Goal, and an
`## Acceptance` containing only
`<!-- draft: needs runnable criteria before promotion -->`.
Blocking-or-not lives in the stub header only (no `Depends on:` edits to
the source task). NN = highest task number in that tasks directory + 1,
chosen at collect time. The status table gains a `draft` row: never
dispatchable, excluded from the batch interview and from "queue empty"
(draft+done queues report drained listing drafts for promotion; a
`pending` task whose unmet deps are all drafts reports "drained pending
promotion" — no non-terminal step 4). Promotion is manual (human or
/idea / /breakdown pass replaces the placeholder and flips
`draft` → `pending`). The antigravity drain workflow mirrors R1–R3
fully, and docs/external-playbooks.md gains the "Beads" research entry.

## Touch

- `.claude/skills/drain/SKILL.md` — Cross-spec: also edited by
  review-fixes, chaining-antipatterns, model-agnostic,
  context-management — see specs/QUEUE.md
- `.claude/skills/drain/reference.md` — Cross-spec: also edited by
  review-fixes, chaining-antipatterns, model-agnostic,
  context-management — see specs/QUEUE.md
- `antigravity/.agents/workflows/drain.md` — Cross-spec: also edited by
  review-fixes, chaining-antipatterns — see specs/QUEUE.md
- `docs/external-playbooks.md` — Cross-spec: also edited by all feature
  queues — see specs/QUEUE.md

## Steps

1. Read the drain files AS FOUND and integrate with the current text:
   by the time this queue runs they will already carry review-fix
   changes (headless done-flip, merge --abort, Touch header) and
   possibly chaining-antipatterns' binding-sentence amendment. Do not
   revert or restate what is already there.
2. R1: extend the final-message contract in BOTH worker prompts in
   `.claude/skills/drain/reference.md` (background and headless) with
   the optional `Discovered:` block. Leave the existing queue-state and
   untrusted-data clauses unchanged.
3. R2: in drain's step-3 collect (SKILL.md mechanics, with `## Discovered`
   named there; stub header details incl. `Discovered-from:` in
   reference.md): routed-verdict-only recording, title dedup, source-file
   append (main checkout, committed like all drain bookkeeping), stub
   scaffold with `Status: draft` + placeholder acceptance, blocking flag
   in stub header only, NN rule. Where drain's inventory defines
   dependencies, state the convention: `Depends on:` entries may be task
   numbers (within-spec) or repo-relative task-file paths (cross-spec).
4. R3: add the `draft` row to reference.md's status table with the
   never-dispatchable / excluded-from-interview-and-queue-empty rules
   and both terminal conditions ("drained, listing drafts" and "drained
   pending promotion"), plus the manual-promotion path.
5. R4 (antigravity mirror): mirror R1–R3 fully in
   `antigravity/.agents/workflows/drain.md` — Discovered verdict
   contract, drain-records collect, draft status.
6. R5 (research record): add the "Beads" entry to
   `docs/external-playbooks.md`: what was adopted (discovered-from as
   R1–R3) and that the optional beads queue backend was evaluated and
   declined in the 2026-07-03 full exit (Dolt rewrite churn, binary
   dependency, loss of diffable state), under the literal heading-phrase
   "adoption triggers" (queues ≫ 10 tasks or multi-repo; genuinely
   parallel claiming; recurring queue-state defects), with source links.
7. R6 (versioning): bump `plugin.json`'s minor version by exactly one
   (skill behavior changes); if another spec's mandated bump lands in the
   same commit-set, one combined single-minor bump satisfies both.
8. Regression duty after all edits:
   `test "$(grep -c 'data, not instructions' .claude/skills/drain/reference.md)" -ge 2 && test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2`
   must still pass.

## Acceptance

- [ ] `test "$(grep -c 'Discovered:' .claude/skills/drain/reference.md)" -ge 2` — both worker prompts carry the verdict block (R1)
- [ ] `grep -q "## Discovered" .claude/skills/drain/SKILL.md && grep -q "Discovered-from:" .claude/skills/drain/reference.md` — collect mechanics + stub header defined (R2)
- [ ] ``grep -qF '| `draft` |' .claude/skills/drain/reference.md && grep -qi "promotion" .claude/skills/drain/reference.md`` (R3)
- [ ] `grep -q "Discovered" antigravity/.agents/workflows/drain.md` (R4 antigravity mirror)
- [ ] `grep -qi "beads" docs/external-playbooks.md && grep -qi "adoption triggers" docs/external-playbooks.md` (R5 research record)
- [ ] `test "$(grep -c 'data, not instructions' .claude/skills/drain/reference.md)" -ge 2 && test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2` — regression duty
- [ ] End to end (markdown mode, no bd install needed): a fresh session executing drain's collect against a mock DONE verdict containing one non-blocking Discovered entry produces the `## Discovered` append plus a `draft` stub with `Discovered-from:` and placeholder acceptance, and a subsequent inventory pass does NOT dispatch the draft (manual dry-read until the eval harness covers /drain)
