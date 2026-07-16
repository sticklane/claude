#!/usr/bin/env bash
# Grades the /breakdown run. CWD is $EVAL_DIR; exit 0 = pass, non-zero with
# output explaining what failed. Beyond the R2 artifact checks (task files
# well-formed + a Parallelization section), this scenario adds an R3
# TRAJECTORY check: it inspects EVAL_TRANSCRIPT to confirm /breakdown's
# file-dependency-unclear step (SKILL.md step 2) actually delegated to a
# `scout` agent instead of reading the codebase directly.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

# --- R2 artifact checks (unchanged from the 01 model) ----------------------
shopt -s nullglob
tasks=(specs/toolkit/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -ge 2 ] || fail "expected >=2 specs/toolkit/tasks/NN-*.md files, found ${#tasks[@]}"

for t in "${tasks[@]}"; do
  grep -q "^Status:" "$t" || fail "$t has no Status: line"
  grep -q "^Depends on:" "$t" || fail "$t has no Depends on: line"
  grep -q "^## Acceptance" "$t" || fail "$t has no ## Acceptance section"
  awk '/^## Acceptance/{in_sec=1; next} /^## /{in_sec=0} in_sec' "$t" | grep -q '`' \
    || fail "$t Acceptance section has no backticked command"
done

grep -q "Parallelization" specs/toolkit/SPEC.md \
  || fail "specs/toolkit/SPEC.md gained no Parallelization section"

# --- R3 trajectory check ---------------------------------------------------
# Guard first: an empty or missing EVAL_TRANSCRIPT (the runner's no-locatable-
# transcript warning case) must fail LOUDLY here, never silently pass — a
# trajectory assertion with no transcript to read has proved nothing.
if [ -z "${EVAL_TRANSCRIPT:-}" ] || [ ! -s "$EVAL_TRANSCRIPT" ]; then
  fail "EVAL_TRANSCRIPT is empty or missing; cannot check the scout-delegation trajectory (transcript unavailable)"
fi

# The transcript is the claude-code stream-json JSONL. A /breakdown that
# delegated its file-dependency mapping to a scout emits a Task tool_use
# whose input carries subagent_type "scout". (Assumed JSONL field name;
# see this task's ## Decisions — a human re-confirms it against a real
# transcript and adjusts the pattern if the field is nested differently.)
grep -Eq '"subagent_type"[[:space:]]*:[[:space:]]*"scout"' "$EVAL_TRANSCRIPT" \
  || fail "transcript shows no scout delegation (no '\"subagent_type\":\"scout\"' in $EVAL_TRANSCRIPT); /breakdown appears to have read the codebase directly instead of asking a scout"

echo "assert: all checks passed (${#tasks[@]} task files, scout delegation present)"
