# Evidence: Task 06 — evals runner robustness

Verified: 2026-07-03, branch task/06-evals-runner-robustness
Verifier: independent (did not write this code)
Verdict: **PASS**

All commands run from /Users/sjaconette/claude/.claude/worktrees/agent-a53f5a7878e5ff644.
This overwrites the prior report; every criterion was re-executed against the
current code (split-trap revision: `trap 'rm -rf "$EVAL_DIR"' EXIT` +
`trap 'exit 130' INT TERM`).

## Acceptance criteria

1. ✓ `bash -n evals/run.sh` → exit 0
2. ✓ `grep -q "shopt -s nullglob" evals/run.sh` → exit 0 (line 12)
3. ✓ `grep -q "unknown skill" evals/run.sh && grep -qF '.claude/skills/$skill' evals/run.sh` → exit 0
   (guard at lines 27-30 for the CLI filter arg, plus per-scenario guard at line 49)
4. ✓ `grep -q "GIT_CONFIG_GLOBAL=/dev/null" evals/run.sh && grep -q "commit.gpgsign=false" evals/run.sh` → exit 0
5. ✓ `grep -qE "trap .rm -rf .\\\$EVAL_DIR" evals/run.sh` → exit 0 (line 35)
6. ✓ `grep -q "tee" evals/run.sh` → exit 0 (session teed to `$EVAL_DIR/session.log`, line 65)
7. ✓ `grep -qF "Bash(ls *)" evals/breakdown/01-small-spec/allowed-tools.txt && grep -qF "Bash(wc *)" ...` → exit 0
   File now reads: `Read,Edit,Write,Glob,Grep,Bash(git *),Bash(ls *),Bash(wc *),Task`
8. ✓ FAIL path exercised with the runner's actual CLI:
   ```
   $ bash evals/run.sh no-such-skill; echo exit=$?
   unknown skill: no-such-skill
   exit=1
   ```
   Exits before the scenario loop: no claude session ran, no fixture created.

## Semantic checks (not just grep)

**Git isolation reaches subprocesses.** Lines 23-24 use `export`, so
`GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false` are inherited by
setup.sh and the claude invocation. End-to-end test: in a fresh repo with
`commit.gpgsign=true` set locally, exporting exactly these vars made
`git config --get commit.gpgsign` report `false` (GIT_CONFIG_COUNT injection
has command-line precedence) and `git commit` succeeded unsigned.

**Trap semantics.** Code: `trap 'rm -rf "$EVAL_DIR"' EXIT` +
`trap 'exit 130' INT TERM`; `EVAL_DIR=""` initially and reset to `""` at the
end of each loop iteration (line 83), after the "fixture kept" message.
Behavioral harness replicating this exact structure:
- Interrupt mid-scenario → rc=130, in-flight mktemp dir removed (INT trap
  exits 130, which fires the EXIT cleanup trap).
- FAIL path (EVAL_DIR reset to "" after kept-message, then exit) → kept
  fixture dir survives; `rm -rf ""` is a no-op.
- PASS path deletes the fixture explicitly (line 76).

**tee does not mask session failure.** `set -o pipefail` was added alongside
the `| tee "$EVAL_DIR/session.log"` pipeline, so a claude timeout/non-zero
exit still trips the `session failed` branch. The log lives inside the
fixture, so it is kept on FAIL and deleted on PASS with the fixture.

**nullglob.** With no matching scenarios the loop body never runs; total=0
hits the "no scenarios found" guard → exit 1. The unknown-skill CLI guard
fires even earlier for a bogus skill name.

## Standard gates

`bash -n evals/run.sh` clean. No project-wide build/lint/test suite applies
to this shell script; repo CLAUDE.md prescribes skill-behavior testing via
this very runner.

## Scope check

`git diff --stat` touches exactly:
- `evals/run.sh` (in Touch list)
- `evals/breakdown/01-small-spec/allowed-tools.txt` (in Touch list)
- `specs/review-fixes/tasks/06-evals-runner-robustness.md` — status
  `pending` → `in-progress` only (task bookkeeping, not scope creep)

No test files were modified to fit the implementation; each grep target was
exercised behaviorally above, so the acceptance greps match real code paths.
No overfitting detected.
