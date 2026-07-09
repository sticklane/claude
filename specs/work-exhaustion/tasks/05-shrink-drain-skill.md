# Task 05: Shrink drain/SKILL.md back under the 500-line convention

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: 02, 03, 04
Priority: P3
Budget: 16 turns
Spec: ../SPEC.md
Discovered-from: specs/work-exhaustion/tasks/01-drain-orchestrator-contract.md
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude-plugin/plugin.json

## Goal

`drain/SKILL.md` is back under 500 lines with NO contract change: heavy
reference prose moves into `drain/reference.md` (one level deep, per
CLAUDE.md's reference conventions), execution-critical contracts stay in
SKILL.md's first 30 lines, and every machine-checked token the
work-exhaustion and agentprof specs grep for survives in SKILL.md
itself. Runs after tasks 02–04 so the moved prose is final.

## Steps

1. Record the pre-move token inventory (the acceptance greps below) and
   `wc -l`.
2. Move detail prose (not contract statements) into reference.md
   sections; leave one-line pointers.
3. Re-run the full token inventory, lint gate, and line count.
4. Bump plugin.json one patch level from the value at this task's own
   base commit.

## Acceptance

- [ ] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500
- [ ] `grep -qi "dispatchable work remains" .claude/skills/drain/SKILL.md && grep -qi "critique intake" .claude/skills/drain/SKILL.md && grep -q "## Decisions" .claude/skills/drain/SKILL.md && grep -q "/handoff" .claude/skills/drain/SKILL.md && grep -qi "checklist" .claude/skills/drain/SKILL.md` → all match (work-exhaustion contract survives)
- [ ] `grep -c "agentprof:stage=" .claude/skills/drain/SKILL.md` → 5 and `grep -c "agentprof:role=" .claude/skills/drain/SKILL.md` → 5 (instrumentation markers survive)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
- [ ] plugin.json version differs from `git show <this task's base commit>:.claude-plugin/plugin.json` (cite both values)
