#!/usr/bin/env bash
# Skill eval runner. Usage: evals/run.sh [skill-name]
#
# For each scenario evals/<skill>/<NN-name>/ (optionally filtered to one
# skill): build a fresh fixture via setup.sh, provision the skill under
# test plus the toolkit's agents into it, run the scenario prompt
# headlessly, then grade with assert.sh. Prints one pass/fail line per
# scenario and a summary; exits non-zero if any scenario failed.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Fixed default allowlist — deliberately no Task; fan-out skills add it
# via their scenario's allowed-tools.txt.
DEFAULT_ALLOWED='Read,Edit,Write,Glob,Grep,Bash(git *)'

filter="${1:-}"
pass=0
fail=0

for scenario in "$ROOT"/evals/*/[0-9][0-9]-*/; do
  scenario="${scenario%/}"
  skill="$(basename "$(dirname "$scenario")")"
  name="$skill/$(basename "$scenario")"
  [ -n "$filter" ] && [ "$skill" != "$filter" ] && continue

  EVAL_DIR="$(mktemp -d)"
  verdict="FAIL"
  if ! EVAL_DIR="$EVAL_DIR" bash "$scenario/setup.sh"; then
    reason="setup.sh failed"
  else
    # Provision the skill under test (real skill text is the point of
    # the eval) and the toolkit's agents, which fan-out skills spawn.
    mkdir -p "$EVAL_DIR/.claude/skills"
    cp -r "$ROOT/.claude/skills/$skill" "$EVAL_DIR/.claude/skills/"
    cp -r "$ROOT/.claude/agents" "$EVAL_DIR/.claude/"

    allowed="$DEFAULT_ALLOWED"
    [ -f "$scenario/allowed-tools.txt" ] && allowed="$(head -n 1 "$scenario/allowed-tools.txt")"

    if ! (cd "$EVAL_DIR" && timeout 900 claude -p "$(cat "$scenario/prompt.txt")" \
        --permission-mode dontAsk --max-turns 40 --allowed-tools "$allowed"); then
      reason="session failed (timeout or non-zero exit)"
    elif ! (cd "$EVAL_DIR" && bash "$scenario/assert.sh"); then
      reason="assert.sh failed"
    else
      verdict="PASS"
      reason=""
    fi
  fi
  rm -rf "$EVAL_DIR"

  if [ "$verdict" = "PASS" ]; then
    pass=$((pass + 1))
    echo "PASS  $name"
  else
    fail=$((fail + 1))
    echo "FAIL  $name ($reason)"
  fi
done

total=$((pass + fail))
if [ "$total" -eq 0 ]; then
  echo "no scenarios found${filter:+ for skill '$filter'}" >&2
  exit 1
fi
echo "----"
echo "$pass/$total scenarios passed"
[ "$fail" -eq 0 ]
