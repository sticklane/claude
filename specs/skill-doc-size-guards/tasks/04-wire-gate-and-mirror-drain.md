# Task 04: Wire the size/TOC gate into drain's checklist and mirror the drain changes

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
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

## Acceptance

- [ ] `grep -q "lint-skill-size-gate" .claude/skills/drain/reference.md` →
      match.
- [ ] `diff <(git show HEAD~1:codex/.agents/skills/drain/SKILL.md 2>/dev/null) codex/.agents/skills/drain/SKILL.md`
      → non-empty diff (confirms the codex mirror actually changed in this
      task's commit, not skipped).
- [ ] `git show <this task's base commit>:.claude-plugin/plugin.json | grep '"version"'`
      compared against `grep '"version"' .claude-plugin/plugin.json` →
      values differ (cite both in the evidence line; never hard-code the
      literal `0.8.63` since a sibling task may move it first).
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
