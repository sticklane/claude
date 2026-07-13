# Task 03: Shrink drain/SKILL.md to ≤500 lines and add a TOC heading to drain/reference.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirements R4, R5 drain portion)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

`.claude/skills/drain/SKILL.md` drops from 517 to at or under 500 lines
(aim for real headroom, e.g. ≤490, so the file doesn't immediately recreate
the "exactly 500 with zero headroom" problem the spec's Problem section
cites) with NO contract change: heavy detail prose moves into
`drain/reference.md`, one-line pointers are left behind, execution-critical
contracts stay in SKILL.md's first 30 lines, and every machine-checked
token another spec greps for survives. Separately, `drain/reference.md`
(1595 lines) gains a `## Table of contents` heading within its first 20
lines — promote its existing prose "Contents:" line (line 3) into, or
supplement it with, a heading matching requirement 3's pattern, listing the
file's `## `-level sections.

This is the riskiest task in this spec: SKILL.md bodies truncate on
compaction (CLAUDE.md's authoring-conventions bullet) so a careless move
can silently drop execution-critical contracts. This spec's precedent is
`specs/work-exhaustion/tasks/05-shrink-drain-skill.md` — read it in full
before starting; follow the same procedure (record a token inventory
first, move only detail prose, re-verify the inventory after).

## Touch

Do not edit `.claude/skills/drain/reference.md`'s "Exit checklist" or
"Push guard (canonical)" sections' _content_ beyond adding the TOC heading
and receiving relocated prose from SKILL.md — wiring the new lint gate
into those sections is a separate, later task (04) in this spec; don't
add the `lint-skill-size-gate.sh` reference yourself here. Do not edit
`codex/.agents/skills/drain/SKILL.md`, `antigravity/.agents/workflows/drain.md`,
or `.claude-plugin/plugin.json` — those are task 04's.

## Steps

1. Record a pre-move token inventory: `wc -l .claude/skills/drain/SKILL.md`,
   and the counts/matches for: `agentprof:stage=` (currently 9),
   `agentprof:role=` (currently 3), `dispatchable work remains`,
   `critique intake`, `## Decisions`, `/handoff`, `checklist` — all
   case-insensitive where noted, all currently present.
2. Move detail prose (not contract statements — anything in the first 30
   lines is execution-critical and must stay) out of SKILL.md into
   corresponding sections of `drain/reference.md`, leaving a one-line
   pointer in SKILL.md at each relocation site.
3. Add the `## Table of contents` heading to `drain/reference.md` within
   its first 20 lines, listing its `## `-level section titles (the
   existing "Contents:" prose line at line 3 can be promoted into this
   heading or kept alongside it).
4. Re-run the full token inventory from step 1 against the new SKILL.md;
   every token/count must still be present and every count must match
   (agentprof:stage= still 9, agentprof:role= still 3) — a moved detail
   sentence is fine, a lost contract token is not.
5. Confirm `wc -l` on SKILL.md is at or under 500 (target ≤490 for
   headroom).

## Acceptance

- [ ] `wc -l < .claude/skills/drain/SKILL.md` → a number ≤ 500 (ideally
      ≤ 490).
- [ ] `grep -c "agentprof:stage=" .claude/skills/drain/SKILL.md` → 9 and
      `grep -c "agentprof:role=" .claude/skills/drain/SKILL.md` → 3
      (unchanged from the pre-task baseline recorded in step 1).
- [ ] `grep -qi "dispatchable work remains" .claude/skills/drain/SKILL.md && grep -qi "critique intake" .claude/skills/drain/SKILL.md && grep -q "## Decisions" .claude/skills/drain/SKILL.md && grep -q "/handoff" .claude/skills/drain/SKILL.md && grep -qi "checklist" .claude/skills/drain/SKILL.md`
      → all match (exit 0).
- [ ] `grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/drain/reference.md)`
      → match.
- [ ] `bash evals/lint-ultra-gate.sh; echo "exit:$?"` → `exit:0` (the
      pre-existing ultra-path gate must stay green — drain/SKILL.md is one
      of its four checked files).
