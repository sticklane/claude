# Task 02: breakdown skill gathers structure via ctx in indexed repos

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/breakdown/SKILL.md, antigravity/.agents/workflows/breakdown.md

## Goal

/breakdown's structure-scouting step (its step 2, "If file-level
dependencies are unclear, ask `scout` agents") instructs: in an indexed
repo (`.context/` at the repo root), gather symbol-level structure for
task-file authoring via `ctx tree` (per module/file) and `ctx sig` /
`ctx refs` (per touched symbol) BEFORE any scout dispatch or file read —
citing the 2026-07-21 budget_analysis pairing (three task files written
from two `ctx tree` outlines, zero source reads) as the model.

## Touch

Do NOT touch `.claude-plugin/plugin.json` (task 06 owns the bump) and do
NOT touch the ctx SKILL.md (registry-governed, other specs own it). The
antigravity leg is a paraphrased port — content-coverage, not byte-diff.

## Steps

1. Edit `.claude/skills/breakdown/SKILL.md`'s scouting step: add the
   index-first instruction, conditional on `.context/` presence, with
   the two-command recipe (`ctx tree` per module; `ctx sig`/`ctx refs`
   per symbol a task will touch) and the fallback to scouts when the
   repo is unindexed or the question is content-shaped.
2. Port the same procedure to `antigravity/.agents/workflows/breakdown.md`
   (`.claude/rules/mirror-procedure-discipline.md`).

## Acceptance

- [ ] `grep -c 'ctx tree' .claude/skills/breakdown/SKILL.md` → ≥1
- [ ] `grep -c '.context/' .claude/skills/breakdown/SKILL.md` → ≥1 (the index-presence condition)
- [ ] `grep -c 'ctx tree' antigravity/.agents/workflows/breakdown.md` → ≥1
- [ ] `grep -rc 'ctx show' .claude/skills/breakdown/ | grep -v ':0' | wc -l` → 0

Depth ceiling: L0/L1 prose greps — the artifact is skill doctrine; the
behavioral complement is task 04's telemetry plus the existing breakdown
evalset (`evals/breakdown/`), which a follow-up eval scenario can extend
to assert ctx-first scouting in an indexed fixture.
