# Task 03: Trim drain/SKILL.md back under the 500-line budget

Status: done
Promotion-ready: true
Promoted-by-run: c92aedb1ae49f8d3
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, codex/.agents/skills/drain/SKILL.md, antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

Reduce `.claude/skills/drain/SKILL.md` from 503 lines back to <=500 lines by
relocating detail prose to `drain/reference.md` and leaving one-line
pointers, preserving all execution-critical contracts in the first 30 lines
and all machine-checked tokens other specs depend on, following the same
technique as the closed prior task `specs/skill-doc-size-guards/tasks/03-shrink-drain-skill-and-toc.md`.
Then inspect the codex and antigravity mirrors per CLAUDE.md's port-chain
convention -- for a pure prose relocation with no procedural change, the
mirrors may need no edit at all (`.claude/rules/mirror-procedure-discipline.md`:
mirrors track procedure, not exact prose/line-count), but this task must
actively confirm that classification for each mirror rather than skip them
silently (CLAUDE.md's codex-leg rule: a task changing one of the four
`.claude/skills/{drain,build,autopilot,evals}/SKILL.md` files must carry the
matching `codex/.agents/skills/<name>/SKILL.md` update in its `Touch:`).

## Touch

`.claude/skills/drain/SKILL.md` and `reference.md` are the actual trim.
`codex/.agents/skills/drain/SKILL.md` (real content, not a symlink) and
`antigravity/.agents/workflows/drain.md` are listed so this task CAN inspect
and, if warranted, update them -- do not touch any other skill's files.
`.claude-plugin/plugin.json` version bump per CLAUDE.md's categorical rule
that a spec touching `.claude/skills/` files carries the bump in some task's
Touch (this spec's task 02 already bumped once for the harness-audit skill;
this task's drain-skill edit is a separate skill-content change needing its
own bump).

## Steps

1. Read `.claude/skills/drain/SKILL.md` (503 lines) and `reference.md`,
   and the closed prior task `specs/skill-doc-size-guards/tasks/03-shrink-drain-skill-and-toc.md`
   for the established technique (move detail prose to reference.md, leave a
   citing pointer in SKILL.md; never change procedure/steps/order/conditions
   -- `.claude/rules/mirror-procedure-discipline.md` and this repo's own
   quality bar for SKILL.md: execution-critical contracts stay in the first
   30 lines).
2. Trim SKILL.md to <=500 lines (target <=490 for headroom), preserving
   every `agentprof:stage=`/`agentprof:role=` marker and the specific tokens
   listed in Acceptance below.
3. Inspect `codex/.agents/skills/drain/SKILL.md`: classify the trim as
   load-bearing (codex's own mechanism forces a matching edit) or incidental
   (no procedural change, so no edit needed) per mirror-procedure-discipline.
   Record the classification and action taken (or explicitly not taken) in
   your final verdict's `Decisions:` section.
4. Inspect `antigravity/.agents/workflows/drain.md` the same way, recording
   the same classification in `Decisions:`.
5. Bump `.claude-plugin/plugin.json`'s version above its value at this
   task's own base commit.

## Acceptance

- [x] `wc -l < .claude/skills/drain/SKILL.md` → <=500. Evidence: `495`.
- [x] `grep -c "agentprof:stage=" .claude/skills/drain/SKILL.md` → 9. Evidence: `9`.
- [x] `grep -c "agentprof:role=" .claude/skills/drain/SKILL.md` → 3. Evidence: `3`.
- [x] `bash evals/lint-skill-size-gate.sh; echo "exit:$?"` → exit:0. Evidence: `lint-skill-size-gate: OK` / `exit:0`.
- [x] `F=.claude/skills/drain/SKILL.md; grep -qi "dispatchable work remains" $F && grep -qi "critique intake" $F && grep -q "## Decisions" $F && grep -qi "/handoff" $F && grep -qi "checklist" $F`. Evidence: `exit:0`.
- [x] Final verdict's `Decisions:` section states, for both
      `codex/.agents/skills/drain/SKILL.md` and
      `antigravity/.agents/workflows/drain.md`, whether it was edited or
      confirmed no-edit-needed, with one-line reasoning for each. Evidence:
      both classified no-edit-needed (INCIDENTAL) in the run verdict's Decisions.
- [x] Version bumped from this task's own base commit:
      `BASE=$(git merge-base main HEAD); OLD=$(git show $BASE:.claude-plugin/plugin.json | grep '"version"'); NEW=$(grep '"version"' .claude-plugin/plugin.json); [ "$OLD" != "$NEW" ]`. Evidence: `0.9.7 -> 0.9.8`.
