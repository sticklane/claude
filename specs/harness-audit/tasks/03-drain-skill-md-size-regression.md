Status: draft
Discovered-from: specs/harness-audit/tasks/01-harness-audit-skill.md
Spec: ../SPEC.md
Blocking: no

# drain/SKILL.md regressed back over the 500-line budget

`.claude/skills/drain/SKILL.md` is 503 lines, exceeding the 500-line
SKILL.md budget `evals/lint-skill-size-gate.sh` enforces. `specs/skill-doc-size-guards`
already fixed this once (closed), but subsequent unrelated doc edits pushed
it back over the line -- needs a fresh trim pass (or a docs/TASKS.md-tracked
follow-up) to bring it back under budget.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
