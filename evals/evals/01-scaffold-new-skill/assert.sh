#!/usr/bin/env bash
# Grades the /evals run. CWD is $EVAL_DIR; exit 0 = pass, non-zero with
# output explaining what failed.
#
# Checks the scaffold path only (SKILL.md step 1: "If evals/<skill>/ has
# no scenario, create evals/<skill>/01-<name>/ with the four files"),
# never the run path — that would fire a nested paid headless session
# from inside this already-headless eval. Content is checked structurally
# (non-empty, executable where the contract requires it, prompt names the
# target skill) rather than for exact wording, per the toolkit's own
# testing rubric.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob
scenarios=(evals/greet/[0-9][0-9]-*/)
[ "${#scenarios[@]}" -ge 1 ] || fail "expected >=1 evals/greet/NN-*/ scenario directory, found ${#scenarios[@]}"
scenario="${scenarios[0]%/}"

for f in setup.sh prompt.txt assert.sh; do
  [ -s "$scenario/$f" ] || fail "$scenario/$f is missing or empty"
done

for f in setup.sh assert.sh; do
  [ -x "$scenario/$f" ] || fail "$scenario/$f is not executable"
done

grep -qi 'greet' "$scenario/prompt.txt" \
  || fail "$scenario/prompt.txt does not reference the greet skill"

echo "assert: all checks passed (evals/greet/*/ scaffolded with the four-file contract)"
