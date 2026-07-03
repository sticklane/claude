# Verification evidence: task 03 — evals runner parameterization

Verdict: PASS
Verified: 2026-07-03, worktree /Users/sjaconette/claude/.claude/worktrees/agent-a64df8f7f596f2da8, branch task/03-evals-runner-params, HEAD a3607c8, working tree clean.
Verifier: independent (did not write this code).

## Criterion 1 — run.sh mentions overrides and parses

Command:
```
grep -q "RUNNER_CMD" evals/run.sh && grep -q "EVALS_ROOT" evals/run.sh && grep -q "ALLOWED_TOOLS" evals/run.sh && bash -n evals/run.sh
```
Result: exit 0. ✓

## Criterion 2 — stub + selftest executable and parse

Command:
```
test -x evals/stub-cli.sh && test -x evals/runner-selftest.sh && bash -n evals/stub-cli.sh && bash -n evals/runner-selftest.sh
```
Result: exit 0. ✓

## Criterion 3 — selftest passes with no model access

Command:
```
./evals/runner-selftest.sh
```
Output:
```
runner selftest: OK (PASS and FAIL plumbing verified with /Users/sjaconette/claude/.claude/worktrees/agent-a64df8f7f596f2da8/evals/stub-cli.sh)
```
Exit 0. ✓ Uses the shipped stub by default (RUNNER_CMD unset in my shell). The selftest asserts both paths: PASS line + exit 0 on a passing assert, FAIL line + exit 1 on a deliberately failing assert (fixture reclaimed via `kept_fixture` in the trap).

## Criterion 4 — end-to-end breakdown eval with both vars unset

Command:
```
env -u RUNNER_CMD -u EVALS_ROOT ./evals/run.sh breakdown
```
Output tail (real headless claude session, ran ~4 min):
```
assert: all checks passed (2 task files)
PASS  breakdown/01-small-spec
----
1/1 scenarios passed
C4 exit: 0
```
Exit 0. ✓ Selftest (criterion 3) separately proved a non-Claude command drives the same harness; its scenarios live only under `mktemp -d` and committed `evals/` contains only `breakdown/01-small-spec` plus the runner scripts — never discoverable by a plain `./evals/run.sh`.

## Step-level implementation checks

- RUNNER_CMD: word-split via `read -r -a runner <<<"$RUNNER_CMD"`, executed inside `(cd "$EVAL_DIR" && ALLOWED_TOOLS="$allowed" timeout 900 "${runner[@]}" "$(cat "$scenario/prompt.txt")" ...)` — prompt is the final arg, allowlist exported as ALLOWED_TOOLS, documented in a comment including the PATH-resolvable/absolute-first-word note (run.sh lines 69–79). ✓
- EVALS_ROOT: redirects only the discovery glob (`for scenario in "$EVALS_ROOT"/*/[0-9][0-9]-*/`); provisioning still copies from `$ROOT/.claude/skills/$skill` and `$ROOT/.claude/agents` (toolkit checkout). Default `$ROOT/evals` matches main's glob. ✓
- Unset-vars invocation vs `git show main:evals/run.sh`: the `claude -p ... --permission-mode dontAsk --max-turns 40 --allowed-tools "$allowed"` line is byte-identical; only the surrounding control flow changed from `if ! (...)` to `|| session_rc=$?` + rc check — behaviorally equivalent, and criterion 4 confirms empirically. ✓
- plugin.json NOT bumped: `git diff main -- .claude-plugin/plugin.json` empty; version still 0.6.1. ✓

## Scope creep

None. `git diff main --stat` touches exactly the Touch list: evals/run.sh, evals/stub-cli.sh (new), evals/runner-selftest.sh (new). No changes outside evals/.

## Overfitting check

Test files (selftest + stub) committed first in e7983eb ("fails: overrides not implemented") and NOT modified by the implementation commit a3607c8 (which touched only evals/run.sh). Proper TDD red-green order; no test tampering. The run.sh implementation is generic (any word-split command, any scenario tree), not special-cased to the stub's inputs.
