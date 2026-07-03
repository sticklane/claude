#!/usr/bin/env bash
# Skill eval runner. Usage: evals/run.sh [skill-name]
#
# For each scenario evals/<skill>/<NN-name>/ (optionally filtered to one
# skill): build a fresh fixture via setup.sh, provision the skill under
# test plus the toolkit's agents into it, run the scenario prompt
# headlessly, then grade with assert.sh. Prints one pass/fail line per
# scenario and a summary; exits non-zero if any scenario failed.
# Failed fixtures are kept (path printed) for forensics; passing ones
# are deleted.
set -u -o pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Fixed default allowlist — deliberately no Task; fan-out skills add it
# via their scenario's allowed-tools.txt.
DEFAULT_ALLOWED='Read,Edit,Write,Glob,Grep,Bash(git *)'

# Isolate git from the user's global config (signing, hooks, templates)
# for every setup.sh and claude invocation: null the global config and
# inject commit.gpgsign=false via GIT_CONFIG_COUNT so git commands run
# inside the claude session never try to sign.
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false

filter="${1:-}"
if [ -n "$filter" ] && [ ! -d "$ROOT/.claude/skills/$filter" ]; then
  echo "unknown skill: $filter" >&2
  exit 1
fi

# Clean up the in-flight fixture on exit or interrupt; kept-on-FAIL
# fixtures set EVAL_DIR="" first so the trap never removes them.
EVAL_DIR=""
trap 'rm -rf "$EVAL_DIR"' EXIT
trap 'exit 130' INT TERM

pass=0
fail=0

for scenario in "$ROOT"/evals/*/[0-9][0-9]-*/; do
  scenario="${scenario%/}"
  skill="$(basename "$(dirname "$scenario")")"
  name="$skill/$(basename "$scenario")"
  [ -n "$filter" ] && [ "$skill" != "$filter" ] && continue

  EVAL_DIR="$(mktemp -d)"
  verdict="FAIL"
  if [ ! -d "$ROOT/.claude/skills/$skill" ]; then
    reason="unknown skill"
  elif ! EVAL_DIR="$EVAL_DIR" bash "$scenario/setup.sh"; then
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
        --permission-mode dontAsk --max-turns 40 --allowed-tools "$allowed" 2>&1 \
        | tee "$EVAL_DIR/session.log"); then
      reason="session failed (timeout or non-zero exit)"
    elif ! (cd "$EVAL_DIR" && bash "$scenario/assert.sh"); then
      reason="assert.sh failed"
    else
      verdict="PASS"
      reason=""
    fi
  fi

  if [ "$verdict" = "PASS" ]; then
    rm -rf "$EVAL_DIR"
    pass=$((pass + 1))
    echo "PASS  $name"
  else
    fail=$((fail + 1))
    echo "FAIL  $name ($reason) — fixture kept: $EVAL_DIR"
  fi
  EVAL_DIR=""
done

total=$((pass + fail))
if [ "$total" -eq 0 ]; then
  echo "no scenarios found${filter:+ for skill '$filter'}" >&2
  exit 1
fi
echo "----"
echo "$pass/$total scenarios passed"
[ "$fail" -eq 0 ]
