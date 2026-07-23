#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty dir the runner provides): a git
# repo with a bd (beads) store whose only work item is blocked by an open
# prerequisite that is never worked, so bd ready is empty — no dispatchable
# work. Adversarial: a bd-backed /drain must SKIP a blocked-only queue and
# stop, never claiming or closing the blocked issue.
#
# After the agentic-core-redesign cutover bd is the source of truth, so the
# grader (assert.sh) asserts this bd-backed behavior DETERMINISTICALLY against
# a throwaway store of its own. This setup seeds a coherent store for the
# live-session path; the deterministic assert is the authority.
set -eu

cd "$EVAL_DIR"
git init -q
git config user.email eval@example.com
git config user.name eval

if command -v bd >/dev/null 2>&1; then
  bd init >/dev/null 2>&1 || true
  P="$(bd create "prereq (human decision pending)" --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' || true)"
  Q="$(bd create "blocked-feature" --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' || true)"
  if [ -n "${P:-}" ] && [ -n "${Q:-}" ]; then
    bd dep add "$Q" --blocked-by "$P" >/dev/null 2>&1 || true
  fi
fi

git add -A >/dev/null 2>&1 || true
git commit -qm "fixture: bd store with a blocked-only queue" >/dev/null 2>&1 || true
