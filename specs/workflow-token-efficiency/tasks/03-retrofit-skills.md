# Task 03: Retrofit the five execution skills with tiers, budgets, bounds

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: 01, 02, ../../ultra-mode/tasks/02-skill-ultra-paths.md
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R3, R4, R7-mirror)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/parallel/SKILL.md, .claude/skills/autopilot/SKILL.md, .claude/skills/autopilot/reference.md, .claude/skills/design/SKILL.md, .claude/skills/evals/SKILL.md, .claude/skills/evals/reference.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/parallel.md, antigravity/.agents/workflows/autopilot.md, antigravity/.agents/skills/design/SKILL.md, antigravity/.agents/workflows/evals.md

## Goal

Every agent-spawning instruction in drain, parallel, autopilot, design,
and evals states an explicit tier (model or effort) plus an output budget
for what returns to the orchestrator; implementing workers stay
session-model and explicitly delegate mechanical scouting to scout-tier
scouts; every authorized loop carries a cycle bound ≤ 4.
`bin/check-token-discipline` flips from exit 1 to exit 0. Antigravity
mirrors carry the same text in the same commit.

## Touch

Serialized after ultra-mode 02 (same drain/parallel files). Must NOT
touch: build or breakdown skills (spec Out of scope), bin/ or tests/
(task 02 owns them; run, don't edit — if a fixture is genuinely wrong,
stop DEFERRED rather than tune the checker to pass), .claude/workflows/
(task 04), plugin.json (task 05).

## Steps

1. `bin/check-token-discipline` → confirm exit 1 (RED baseline).
2. Retrofit each file: tier token per dispatch paragraph (tier language
   per the rules section from task 01, inline Claude default only —
   runtimes/ owns other mappings), output budgets (verdict + evidence
   shapes), loop bounds.
3. Mirror to antigravity.
4. `bin/check-token-discipline` → exit 0 (GREEN);
   `git worktree add /tmp/pre-retrofit <pre-retrofit-sha> &&
   bin/check-token-discipline /tmp/pre-retrofit` → exit 1; remove the
   temp worktree.
5. `bash evals/lint-ultra-gate.sh` still exits 0 (ultra sections
   untouched); `./evals/run.sh breakdown` unaffected (breakdown not in
   scope).

## Acceptance

- [ ] `bin/check-token-discipline` → exit 0 on the retrofitted tree
- [ ] `bin/check-token-discipline /tmp/pre-retrofit` (worktree at the pre-retrofit sha) → exit 1
- [ ] `bash tests/test_check_token_discipline.sh` → still exit 0 (checker untouched)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0 (no ultra-gate regressions)
- [ ] Antigravity mirror paths appear in the implementing commit's `git show --stat`
