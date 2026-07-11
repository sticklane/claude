# Task 01: six efficiency stop-rules across dispatch surfaces

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirements R1-R6)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md, .claude/skills/critique/SKILL.md, .claude/agents/verifier.md, .claude/agents/scout.md, .claude/rules/token-discipline.md

## Goal

Six one-to-three-line stop rules land verbatim-anchored (SPEC R1-R6):
Bash-denial retry-once rule ("bare single command") in the drain worker
prompt AND verifier.md; "chained short sleeps" ban in token-discipline
Dispatch authoring AND the worker prompt; re-read discipline ("once per
edit round") in the worker prompt and critic-named-sections line in
critique SKILL.md; "under your worktree root" edit rule in the worker
prompt preamble; scout "not found where expected" stop rule in scout.md;
"load only the named section" on the FIRST SKILL.md pointer citing each
of reference.md's "Worker prompt" / "Owner lease" / "Baton pass".

## Touch

Text only — NO antigravity/ (task 02), NO plugin.json (task 02), no code.

## Steps

1. Add each rule at its surface; keep every literal anchor phrase exactly.
2. Run the spec's six anchor greps; confirm each newly hits.

## Acceptance

- [ ] `grep -qi 'bare single command' .claude/skills/drain/reference.md && grep -qi 'bare single command' .claude/agents/verifier.md` → hits (R1)
- [ ] `grep -qi 'chained short sleeps' .claude/rules/token-discipline.md && grep -qi 'chained short sleeps' .claude/skills/drain/reference.md` → hits (R2)
- [ ] `grep -qi 'once per edit round' .claude/skills/drain/reference.md && grep -qi 'sections the critic named' .claude/skills/critique/SKILL.md` → hits (R3)
- [ ] `grep -qi 'under your worktree root' .claude/skills/drain/reference.md` → hits (R4)
- [ ] `grep -qi 'not found where expected' .claude/agents/scout.md` → hits (R5)
- [ ] `grep -qi 'load only the named section' .claude/skills/drain/SKILL.md` → hits AND MANUAL: on the first pointer citing each of the three sections (R6)
- [ ] `bash agentprof/scripts/check.sh` → green (no code changed)
