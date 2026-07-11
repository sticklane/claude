# Task 04: `evals/run.sh` default runner derives from the active runtime

Status: in-progress
Depends on: 01
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirement R8)
Touch: evals/run.sh

## Goal

`evals/run.sh`'s default runner (used when `RUNNER_CMD` is unset, currently
hardcoded at ~lines 85-87 as `claude -p "$(cat "$scenario/prompt.txt")"
--permission-mode dontAsk --max-turns 40 --allowed-tools "$allowed"`) is
derived from the repo's active runtime profile via `runtimes/parse_headless.py`,
falling back to today's hardcoded `claude -p` line only when no
`.claude/runtime.md` exists or it names `claude-code`. The explicit
`RUNNER_CMD` override (~lines 78-83) is untouched — it remains the one-off
escape hatch, unaffected by this spec.

## Touch

Shell-script-only change to `evals/run.sh`. Do not touch
`.claude/skills/workboard/workboard.py` (task 02) or
`.claude/skills/drain/reference.md` (task 03) — disjoint files.

## Steps

1. Read the current `RUNNER_CMD` branch (~lines 78-88) in `evals/run.sh`
   to confirm the exact surrounding shell structure before editing.
2. In the `else` branch (no `RUNNER_CMD` set), resolve the repo's active
   runtime the same way drain/workboard do (read `.claude/runtime.md` if
   present, default `claude-code`), call `python3
   runtimes/parse_headless.py <runtime>` to get the joined template,
   substitute the scenario's prompt text into the `<prompt>` placeholder,
   and run that instead of the hardcoded `claude -p` line — but when the
   resolved runtime is `claude-code` (explicit or by absence of
   `.claude/runtime.md`), keep running today's exact hardcoded line
   unchanged (this preserves "the inline Claude default" per CLAUDE.md's
   authoring conventions and keeps the regression path byte-identical).
3. Handle the runtime returning `NONE` (no scriptable relaunch) by failing
   the eval run early with a clear error message — evals require a
   scriptable headless invocation, so this is a real failure, not a
   silent skip.
4. Confirm `evals/run.sh`'s existing scenarios still pass unmodified in the
   no-`.claude/runtime.md` case (the regression path).

## Acceptance

- [ ] `bash evals/run.sh` (no `.claude/runtime.md` present in the toolkit
      checkout) → existing scenarios pass exactly as before this task
- [ ] `grep -c 'runtimes/parse_headless.py' evals/run.sh` → `1` or more
- [ ] `grep -c 'RUNNER_CMD' evals/run.sh` → unchanged from before this task
      (override branch untouched)
- [ ] Manual check: setting a scratch `.claude/runtime.md` to name
      `gemini-cli` and running `bash evals/run.sh` (dry-run / echo the
      resolved command rather than actually invoking `gemini`) shows the
      `gemini -p "<prompt>" \` shape substituted, not the hardcoded
      `claude -p` line
