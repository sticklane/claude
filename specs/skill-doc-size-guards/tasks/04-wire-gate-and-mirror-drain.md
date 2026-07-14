# Task 04: Wire the size/TOC gate into drain's checklist and mirror the drain changes

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 01, 03
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R6, R7)
Touch: .claude/skills/drain/reference.md, codex/.agents/skills/drain/SKILL.md, antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

Drain's own pre-merge checklist now runs `evals/lint-skill-size-gate.sh`
whenever a generation's `Touch:` includes a `.claude/skills/*/SKILL.md` or
`.claude/skills/*/reference.md` path, treating a non-zero exit as a merge
blocker for that task (the same mechanical role `lint-ultra-gate.sh`
already plays, but invoked conditionally since most drain tasks don't
touch skill docs). The two mirrors of drain content stay in lockstep with
task 03's changes plus this task's checklist wiring: the codex `SKILL.md`
mirror (real content, not a symlink) and the antigravity workflow mirror
(procedural port, not verbatim). `.claude-plugin/plugin.json`'s version
bumps one patch level.

## Touch

Do not re-touch `.claude/skills/drain/SKILL.md` in this task (task 03
already landed the shrink and its content is final going into this task)
except for the one-line reference to the new gate if the checklist you're
wiring lives partly in SKILL.md's own pre-merge summary — prefer adding
the actual check to `drain/reference.md`'s checklist sections, per this
spec's Open Questions note that the exact hook point (Push guard vs. Exit
checklist) is an implementation judgment call.

## Steps

1. Pick either drain/reference.md's "Push guard (canonical)" section or
   its "Exit checklist (seven sections)" section (your judgment — both
   exist; see the Open Questions note in ../SPEC.md) and add a step: when
   a generation's `Touch:` includes any `.claude/skills/*/SKILL.md` or
   `.claude/skills/*/reference.md` path, run
   `bash evals/lint-skill-size-gate.sh` and treat non-zero exit as a merge
   blocker for that task.
2. Update `codex/.agents/skills/drain/SKILL.md` to match the post-task-03
   `.claude/skills/drain/SKILL.md` content (it is real, non-symlinked
   content per CLAUDE.md's port-chain rule) plus this task's checklist
   addition if the checklist step lives in SKILL.md rather than
   reference.md.
3. Update `antigravity/.agents/workflows/drain.md` (currently 1056 lines)
   to carry the same procedural changes from task 03 (the shrink/reorg)
   and this task's new checklist step. Per
   `.claude/rules/mirror-procedure-discipline.md`: classify each place the
   workflow's procedure differs from the updated SKILL.md +
   reference.md pair as load-bearing (a difference antigravity's own
   mechanism forces — leave it) or incidental (prose drift — fix it with
   a small, targeted edit; never a full rewrite). Do NOT byte-diff this
   file against the source — it is a paraphrased port, not a verbatim
   mirror (docs/memory/workboard-mirror-verbatim.md).
4. Bump `.claude-plugin/plugin.json`'s `version` one patch level from its
   value at this task's own base commit (currently `0.8.63` at spec
   authoring time, but re-read the live value before bumping — a sibling
   task elsewhere in the repo may have already bumped it).

<!--
PLAN (task 04 — wire gate + mirror drain):
- Hook point (Open Question): chose reference.md's "Push guard (canonical)"
  section over "Exit checklist" — the gate is a per-task pre-merge blocker;
  Push guard is the per-task merge/push mechanics home, Exit checklist is a
  once-per-session human report (fires too late for a per-task merge block).
  SPEC R6 leaves exact placement to implementation; C1 only requires the
  string in reference.md, which this satisfies.
- codex has SKILL.md only (no reference.md mirror in the thin overlay), so the
  gate step is ported INLINE into codex SKILL.md's DONE bullet, beside its
  inline "Push guard (canonical)" summary.
- Task 03 net-changed only reference.md (TOC heading; SKILL.md pre-trimmed by
  ancestor 2f19e4d), so the only procedural content to port to antigravity is
  THIS task's gate step (added to the workflow's merge/push-guard region).
- plugin.json bumped 0.9.0 → 0.9.1 (base value re-read live; sibling had moved
  it from 0.8.63).
- Gate script currently FAILs (7 non-drain reference.md files lack TOCs) — that
  is task 02's job (pending), not task 04's; not in my Touch, not a C1–C4 gate.
-->

## Acceptance

- [x] `grep -q "lint-skill-size-gate" .claude/skills/drain/reference.md` →
      match. Evidence: `grep -c` → 1 (added to the "Push guard (canonical)"
      section as a conditional pre-merge blocker).
- [x] `diff <(git show HEAD~1:codex/.agents/skills/drain/SKILL.md 2>/dev/null) codex/.agents/skills/drain/SKILL.md`
      → non-empty diff (confirms the codex mirror actually changed in this
      task's commit, not skipped). Evidence: 8-line insertion (`250a251,258`)
      adding the skill-doc size/TOC gate to codex's DONE bullet; single-commit
      branch so HEAD~1 = base commit 90adcf3.
- [x] `git show <this task's base commit>:.claude-plugin/plugin.json | grep '"version"'`
      compared against `grep '"version"' .claude-plugin/plugin.json` →
      values differ (cite both in the evidence line; never hard-code the
      literal `0.8.63` since a sibling task may move it first). Evidence:
      base (90adcf3) `"version": "0.9.0"` vs current `"version": "0.9.1"` — differ.
- [ ] MANUAL (per `.claude/rules/mirror-verification.md`'s manual-pending
      escape): confirm `antigravity/.agents/workflows/drain.md` reads as
      procedurally equivalent to the updated `drain/SKILL.md` +
      `drain/reference.md` pair, per
      `.claude/rules/mirror-procedure-discipline.md`'s load-bearing vs.
      incidental classification. This is a live cross-reference read, not
      grep-checkable — if this task runs unattended with no way to
      exercise antigravity interactively, mark this criterion
      manual-pending with that reason stated, for a human or the
      orchestrator to confirm post-merge.
      MANUAL-PENDING: ran unattended with no way to exercise antigravity
      interactively (`.claude/rules/mirror-verification.md` manual-pending
      escape). Static classification (`.claude/rules/mirror-procedure-discipline.md`):
      the gate step added to `antigravity/.agents/workflows/drain.md`'s
      merge/push-guard region is a faithful procedural port of the
      reference.md + codex additions — same condition (`Touch:` includes a
      `.claude/skills/*/SKILL.md` or `*/reference.md` path), same command
      (`bash evals/lint-skill-size-gate.sh`), same consequence (non-zero exit
      = merge blocker / slot-machine path), same `lint-ultra-gate.sh` role
      reference, placed at the same decision point (before merge, after the
      push-guard clause). No load-bearing divergence introduced. Live
      cross-reference read left for a human/orchestrator post-merge.

## Decisions

- [2026-07-14 /drain] Open Question (SPEC R6, hook-point placement):
  chose reference.md's "Push guard (canonical)" section over "Exit
  checklist" for the new lint-skill-size-gate merge-blocker step.
  Rationale: the gate is a per-task pre-merge blocker; Push guard is
  the per-task merge/push-mechanics home, while Exit checklist is a
  once-per-session human report that fires too late to block a
  per-task merge. Reversible: move the added paragraph (and the
  matching codex/antigravity mirror spots) to "Exit checklist (seven
  sections)" if a different placement is preferred later.
