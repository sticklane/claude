#!/usr/bin/env bash
# screen-stub.sh — deterministic injection screen for drain's stub intake.
#
# The HARD layer of stub intake (docs/human-gates.md reason 4): before any
# model reads a Status: draft stub as a promotion candidate, this script runs
# its PINNED regex list against the stub file. A stub whose Goal/body matches
# instruction-shaped text is refused promotion this run and lands on the exit
# checklist flagged for a human — never assessed, never gated — so promotion
# of injectable text can never rest on a model's judgment of it.
#
#   Usage:  screen-stub.sh <stub-file>
#   Exit 0  = clean (no instruction-shaped match)
#   Exit 1  = refused (a pinned pattern matched)
#   Exit 2  = usage error (missing/absent file)
#
# The four pinned categories (from specs/draft-auto-promotion/SPEC.md Solution):
#   1. "ignore / disregard … instructions"  (and prompt/rules/previous/system)
#   2. imperatives addressed to an agent     (you must, act as, pretend, …)
#   3. tool-invocation directives            (git push, rm -rf, curl, <invoke …)
#   4. absolute paths outside the repo       (/etc/, /root/, ~/ , …)
#
# POSIX-friendly ERE (grep -iE). Word-boundary guards use (^|[^[:alnum:]]) so a
# mid-word occurrence (e.g. "prettierignore") does NOT trip the ignore pattern.
set -u

file="${1:-}"
if [ -z "$file" ] || [ ! -f "$file" ]; then
  echo "screen-stub: usage: screen-stub.sh <stub-file>" >&2
  exit 2
fi

# 1. ignore/disregard … instructions
re_ignore='(^|[^[:alnum:]])(ignore|disregard|forget|override|bypass)[[:space:]][^.]{0,40}(instruction|previous|prompt|rule|guardrail|system)'
# 2. imperatives addressed to an agent
re_agent='(^|[^[:alnum:]])(you[[:space:]]+(must|should|will|shall|are[[:space:]]to)|as[[:space:]]an[[:space:]]ai|act[[:space:]]as|pretend[[:space:]]+(to|you)|new[[:space:]]+instructions|do[[:space:]]not[[:space:]]tell|reveal[[:space:]]+your)'
# 3. tool-invocation directives
re_tool='(push[[:space:]]+to[[:space:]]+(main|master)|git[[:space:]]+push|rm[[:space:]]+-rf|sudo[[:space:]]|curl[[:space:]]|wget[[:space:]]|bash[[:space:]]+-c|eval[[:space:]]|exec[[:space:]]|<tool_use|<invoke[[:space:]]|invoke[[:space:]]+name=)'
# 4. absolute paths outside the repo
re_abspath='(^|[^[:alnum:]])(/etc/|/root/|/var/|/usr/|/bin/|/sbin/|/sys/|/proc/|/dev/|~/)'

matched=""
check() { grep -iEq "$2" "$file" && matched="$matched $1"; }
check "ignore-instructions"    "$re_ignore"
check "agent-imperative"       "$re_agent"
check "tool-invocation"        "$re_tool"
check "abs-path-outside-repo"  "$re_abspath"

if [ -n "$matched" ]; then
  echo "screen-stub: REFUSED — instruction-shaped Goal matched:$matched" >&2
  exit 1
fi
echo "screen-stub: clean"
exit 0
