# Task 01: evals/run.sh sets EVAL_TRANSCRIPT

Status: done
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: evals/run.sh

## Goal

`evals/run.sh` exposes a JSONL session transcript to each scenario's
`assert.sh` via a new environment variable, `EVAL_TRANSCRIPT` — an
absolute path to the headless run's transcript. Every existing evalset
still passes with no edits of its own.

## Touch

Only `evals/run.sh` changes in this task. Do not touch any file under
`evals/<evalset>/` (task 02), `.claude/skills/evals/` (task 03), or
`antigravity/`/`codex/`/`.claude-plugin/` (task 04).

## Steps

1. Read `evals/run.sh` in full, focusing on the two runner branches
   around lines 138-193 (the `RUNNER_CMD` override branch and the
   default `claude -p` / other-runtime branch) and the `assert.sh`
   invocation at line 199.
2. Write a failing test first: add a minimal scenario (or extend
   `evals/evals/01-scaffold-new-skill` temporarily, then revert) whose
   `assert.sh` does `[ -n "$EVAL_TRANSCRIPT" ] || exit 1` and confirm it
   fails before your change (env var unset).
3. Implement: for the default Claude-Code runner branch, add
   `--output-format stream-json --verbose` to the `claude -p` invocation.
   This changes what the existing `tee "$EVAL_DIR/session.log"` captures
   from plaintext to JSONL — a single invocation cannot emit both formats
   at once, so don't try to keep a separate plaintext copy: `session.log`
   becomes the JSONL transcript itself, and `EVAL_TRANSCRIPT` points at
   that same path (no new file, no dual-output requirement). Export
   `EVAL_TRANSCRIPT="$EVAL_DIR/session.log"` before invoking `assert.sh`
   when the file was actually produced and is non-empty;
   otherwise set `EVAL_TRANSCRIPT=""` and print a runner warning to
   stderr (R1 — "no locatable transcript" case, e.g. `RUNNER_CMD`
   override branch, or a runtime whose headless template has no
   `stream-json`-equivalent flag). Do this for the `RUNNER_CMD` override
   branch and the non-claude-code runtime branch too, falling back to
   empty+warning in both since neither branch has a defined stream-json
   mechanism today.
4. Confirm no other line in `evals/run.sh` needs updating for
   `assert.sh`'s invocation itself (it already runs with `$EVAL_DIR` as
   CWD; `EVAL_TRANSCRIPT` just needs to be an exported/inherited env var
   at that point).
5. Run `EVAL_DRY_RUN=1 bash evals/run.sh breakdown` and a real
   (non-dry-run) `bash evals/run.sh breakdown` to confirm existing
   scenarios still pass unchanged and `EVAL_TRANSCRIPT` is set and
   points at a real, non-empty file after a real run.

## Acceptance

- [x] `grep -q "EVAL_TRANSCRIPT" evals/run.sh && bash -n evals/run.sh`
      — exit 0 (verifier evidence/01-eval-transcript-runner.md).
- [x] `grep -q "stream-json" evals/run.sh` — exit 0 (verifier report).
- [ ] **Manual-pending** (paid headless run, human-launched — a drained/
      unattended worker cannot launch `claude -p`, only `EVAL_DRY_RUN=1`,
      which produces no transcript; docs/memory/unattended-worker-tool-limits.md):
      `./evals/run.sh breakdown` passes with no edits to `evals/breakdown/`,
      and a one-off scenario asserting `[ -n "$EVAL_TRANSCRIPT" ] && [ -s
"$EVAL_TRANSCRIPT" ]` passes when run against this changed `run.sh`
      (the committed trajectory-assertion scenario is task 02's job, not
      this one's — this is just confirming the mechanism itself works).

## Decisions

- The repo's markdown-formatter PostToolUse hook stripped the 2-space
  indent from the wrapped continuation of the manual-pending acceptance
  criterion (line 68) on every write; it re-applies on each save, so
  hand-reverting is futile. Whitespace-only, no criterion meaning or
  runnability changed. Reverse (if ever needed) by disabling the hook and
  restoring the leading 2 spaces on that line.
