# Verification evidence: task 01 (eval-transcript-runner)

Verdict: PASS (one minor finding, non-blocking — see below)

Branch: task/01-eval-transcript-runner
Base for append-only diff: c596bd8c1bdae18f69c86dfb58f6dac2f534c6f8

## Criterion 1: `grep -q "EVAL_TRANSCRIPT" evals/run.sh && bash -n evals/run.sh`

Command: `grep -q "EVAL_TRANSCRIPT" evals/run.sh && bash -n evals/run.sh; echo "EXIT1=$?"`
Result: `EXIT1=0` — PASS. Syntax check clean, variable present.

## Criterion 2: `grep -q "stream-json" evals/run.sh`

Command: `grep -q "stream-json" evals/run.sh; echo "EXIT2=$?"`
Result: `EXIT2=0` — PASS.

## Criterion 3: `EVAL_DRY_RUN=1 bash evals/run.sh breakdown`

Command run, tail of output:

```
DRY-RUN [claude-code] runner: claude -p "<prompt>" --output-format stream-json --verbose --permission-mode dontAsk --max-turns 40 --allowed-tools Read\,Edit\,Write\,Glob\,Grep\,Bash\(git\ \*\)\,Bash\(ls\ \*\)\,Bash\(wc\ \*\)\,Task
PASS  breakdown/01-small-spec
----
1/1 scenarios passed
```

Contains `--output-format stream-json --verbose` and `1/1 scenarios passed` — PASS.

## Criterion 4: `./evals/runner-selftest.sh`

Ran twice for reproducibility; both times:

```
eval: no locatable transcript for 'handoff/01-pass'; EVAL_TRANSCRIPT is empty (assertions requiring it must fail loudly)
eval: no locatable transcript for 'handoff/01-fail'; EVAL_TRANSCRIPT is empty (assertions requiring it must fail loudly)
runner selftest: OK (PASS and FAIL plumbing verified with .../evals/stub-cli.sh)
```

Exit 0 both times — PASS. (The two stderr warnings are expected: the
selftest's RUNNER_CMD-override branch has no stream-json mechanism, so
EVAL_TRANSCRIPT is correctly cleared + warned, per spec.)

## Manual-pending criterion (paid `claude -p` real run)

Not executed (unattended worker cannot launch `claude -p`; correctly marked
manual-pending in the task file). Confirmed by reading `evals/run.sh`
(diff against base, lines ~136-224) that the mechanism is coded correctly:

- `EVAL_TRANSCRIPT=""` is defaulted once per scenario before the runner
  branches (set -u safety).
- claude-code real-run branch: `claude -p ... --output-format stream-json
--verbose ... | tee "$EVAL_DIR/session.log"`, then
  `EVAL_TRANSCRIPT="$EVAL_DIR/session.log"` — candidate path set only here.
- Central resolution block (guarded by `[ -z "${EVAL_DRY_RUN:-}" ]`, i.e.
  non-dry-run only): keeps EVAL_TRANSCRIPT if the file is non-empty
  (`[ -n "$EVAL_TRANSCRIPT" ] && [ -s "$EVAL_TRANSCRIPT" ]`), else clears it
  and warns to stderr (`eval: no locatable transcript for '$name'; ...`),
  then `export EVAL_TRANSCRIPT` — this precedes the `assert.sh` invocation
  (export at line 219, assert.sh call at line 226).
- RUNNER_CMD override branch and the non-claude-code runtime branch never
  set the candidate path, so they fall through to the empty+warn case —
  confirmed empirically by runner-selftest.sh's two stderr warnings above
  (its scenarios use RUNNER_CMD).

This matches R1/R2 and the task's Steps 2-4 exactly.

## Append-only task-file diff check

Command: `git diff c596bd8c1bdae18f69c86dfb58f6dac2f534c6f8 -- specs/trajectory-evals/tasks/01-eval-transcript-runner.md`

Diff contains:

1. The `<!-- PLAN (delete at close-out) ... -->` comment block insertion —
   allowed.
2. A one-line whitespace-only change: the acceptance criterion's wrapped
   continuation line
   `  "$EVAL_TRANSCRIPT" ]\` passes...`had its 2-space indent stripped to`"$EVAL_TRANSCRIPT" ]\` passes...` — the literal text/wording of the
   acceptance criterion is unchanged, only leading whitespace on a wrapped
   markdown line.

FINDING (minor, non-blocking): item 2 is technically outside the allowed
edit set (Status line / checkbox ticks / evidence-citation lines / plan
comment block) per the append-only check's letter. It changes no words,
only re-indents a wrapped continuation line (likely an incidental
editor-reformat side effect), so I judge it non-substantive — it does not
alter any criterion's meaning or checkability. Flagging per instructions
rather than silently waiving it.

No Status line change, no checkbox ticks were present to observe (the task
file's acceptance checkboxes remain `- [ ]` unticked — consistent with
`Status: in-progress` still shown in the file, not yet closed out).

## Scope check

`git diff c596bd8c1bdae18f69c86dfb58f6dac2f534c6f8 --name-only`:

```
evals/run.sh
specs/trajectory-evals/tasks/01-eval-transcript-runner.md
```

Only the Touch-listed file (`evals/run.sh`) plus the task file itself were
changed — no edits to `evals/<evalset>/`, `.claude/skills/evals/`,
`antigravity/`, `codex/`, or `.claude-plugin/`. No scope creep found.

## Gates

No repo-wide `scripts/check.sh` was run beyond the acceptance commands
themselves, which are the task's own defined gate (bash -n, greps, dry-run,
selftest) — all green as shown above.

## Overall

All four exercisable acceptance commands pass exactly as specified. The
manual-pending criterion is correctly deferred, not faked, and the coded
mechanism matches the spec's stated design. One minor, non-substantive
whitespace-only diff finding in the task file is noted above but does not
change any criterion's text or meaning.
