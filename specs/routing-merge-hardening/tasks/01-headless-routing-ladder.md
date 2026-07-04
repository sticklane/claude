# Task 01: Headless fallback joins the routing ladder

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (F1)
Touch: .claude/skills/drain/reference.md, runtimes/claude-code.md, .claude/rules/token-discipline.md

## Goal

The headless worker template carries the same three-rung model ladder as
Task-tool dispatch: `--model sonnet` on attempt 1, `--model opus` on the
relaunch, `--model fable` for tournament entrants. The token-discipline
scope note no longer says headless runs "their profile's default in v1".

## Steps

1. In `.claude/skills/drain/reference.md`, find the headless fallback
   section (the `claude -p` template). Add `--model <alias>` to the
   command template and one sentence stating the rung selection: attempt
   1 `sonnet`, relaunch `opus`, tournament `fable` — same ladder as the
   Task-tool path in SKILL.md step 3.
2. Mirror the flag into the `## Headless` template in
   `runtimes/claude-code.md` (template restates reference.md's contract —
   keep them identical).
3. In `.claude/rules/token-discipline.md`, update the scope sentence
   "Pins bind Agent-tool dispatch only; the headless fallback templates
   run their profile's default in v1" to say the headless templates pass
   the same tier through `--model`.

## Acceptance

- [ ] `grep -q -- '--model' .claude/skills/drain/reference.md` → exit 0
- [ ] `grep -q -- '--model' runtimes/claude-code.md` → exit 0
- [ ] `! grep -q 'default in v1' .claude/rules/token-discipline.md` → exit 0
- [ ] `./bin/check-token-discipline` → exit 0
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
