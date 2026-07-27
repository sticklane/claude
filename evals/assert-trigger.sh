#!/usr/bin/env bash
# Grades whether a skill activated in a headless run, for trigger scenarios
# whose prompt deliberately never names the skill.
#
# Usage, from a scenario's assert.sh:
#   bash "$EVALS_LIB/assert-trigger.sh" fired     <skill>   # positive case
#   bash "$EVALS_LIB/assert-trigger.sh" not-fired <skill>   # negative case
#
# Activation is read from EVAL_TRANSCRIPT, whose evidence differs per harness:
# Claude Code emits a Skill tool call naming the skill, while Codex and
# Antigravity leave a read of the skill's SKILL.md. Both shapes count, so one
# scenario grades the same way whichever runtime ran it.
#
# A missing or empty transcript fails loudly rather than passing: a trigger
# scenario with nothing to read has graded nothing.
set -eu

expectation="${1:-}"
skill="${2:-}"
case "$expectation" in
  fired|not-fired) : ;;
  *) echo "assert-trigger: expectation must be 'fired' or 'not-fired', got '${expectation}'" >&2; exit 2 ;;
esac
[ -n "$skill" ] || { echo "assert-trigger: no skill named" >&2; exit 2; }

if [ -z "${EVAL_TRANSCRIPT:-}" ] || [ ! -s "$EVAL_TRANSCRIPT" ]; then
  echo "assert-trigger: no transcript to grade (EVAL_TRANSCRIPT empty)" >&2
  exit 1
fi

# The plugin namespace a harness prepends when it resolves the skill from an
# installed plugin rather than a checkout is not part of the skill's identity.
bare="${skill##*:}"

activated=no
if grep -q "\"name\":\"Skill\"" "$EVAL_TRANSCRIPT" &&
   grep -q "\"skill\":\"\(.*:\)\?$bare\"" "$EVAL_TRANSCRIPT"; then
  activated=yes
elif grep -q "skills/$bare/SKILL\.md" "$EVAL_TRANSCRIPT"; then
  activated=yes
fi

if [ "$expectation" = fired ] && [ "$activated" = no ]; then
  echo "assert-trigger: '$bare' did not activate — the description did not match a task it owns" >&2
  exit 1
fi
if [ "$expectation" = not-fired ] && [ "$activated" = yes ]; then
  echo "assert-trigger: '$bare' activated on a task it does not own — the description over-reaches" >&2
  exit 1
fi
