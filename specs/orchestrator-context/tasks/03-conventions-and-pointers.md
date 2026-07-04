# Task 03: Relaunch-every convention + ultra-template baton pointer

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: 01, ../../ultra-mode/tasks/01-runtime-orchestration-section.md
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirements R4, R5)
Touch: .claude/skills/breakdown/SKILL.md, antigravity/.agents/skills/breakdown/SKILL.md, runtimes/claude-code.md

## Goal

Breakdown's task-file/queue conventions document the baton grammar and
the `Relaunch-every: N` SPEC.md header (absence = default 4), so specs
can tune N. The ultra-mode workflow templates in `runtimes/claude-code.md`
carry a template comment noting that the MAIN session treats a long
workflow as its own baton boundary (scriptPath + resumeFromRunId + task
state make the main session disposable), pointing at drain's baton
mechanism rather than duplicating it.

## Touch

Depends on ultra-mode 01 so the pointer lands in the real
`## Orchestration (ultra)` templates (the spec's fallback — an amendment
note in ultra-mode's SPEC.md — applies only if ultra-mode were skipped).
Must NOT touch: drain/autopilot/parallel skill files, the workboard
scanner, plugin.json.

## Steps

1. Confirm acceptance greps fail (RED).
2. Add the `Relaunch-every:` documentation to breakdown SKILL.md's
   conventions (one short passage; grammar cited from drain, not
   restated); mirror to the antigravity breakdown skill.
3. Add the baton-boundary comment to the drain/parallel workflow
   templates in runtimes/claude-code.md.
4. Run acceptance; run `./evals/run.sh breakdown` (breakdown has a stored
   evalset).

## Acceptance

- [ ] `grep -q "Relaunch-every" .claude/skills/breakdown/SKILL.md && grep -q "Relaunch-every" antigravity/.agents/skills/breakdown/SKILL.md` → exit 0, absence-means-4 stated
- [ ] `grep -qi "baton" runtimes/claude-code.md` → exit 0, inside the orchestration templates as a pointer comment
- [ ] `./evals/run.sh breakdown` → 1/1 scenarios pass
