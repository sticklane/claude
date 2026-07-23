#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty dir the runner provides): a git
# repo with a bd (beads) store seeded with a tiny dependency graph — two
# dependency-free ready issues (alpha, beta) and one (gamma) blocked by alpha,
# so a bd-backed /drain works them as a rolling window in dependency order.
#
# After the agentic-core-redesign cutover bd is the source of truth and drain
# is a mechanical bd ready -> claim -> close loop, so this scenario's grader
# (assert.sh) asserts that bd-backed flow DETERMINISTICALLY against a throwaway
# store of its own — it does not grade a model trajectory. This setup seeds a
# coherent store for the live-session path; the deterministic assert is the
# authority.
set -eu

cd "$EVAL_DIR"
git init -q
git config user.email eval@example.com
git config user.name eval

if command -v bd >/dev/null 2>&1; then
  bd init >/dev/null 2>&1 || true
  A="$(bd create "alpha" --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' || true)"
  bd create "beta" >/dev/null 2>&1 || true
  C="$(bd create "gamma" --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' || true)"
  if [ -n "${A:-}" ] && [ -n "${C:-}" ]; then
    bd dep add "$C" --blocked-by "$A" >/dev/null 2>&1 || true
  fi
fi

git add -A >/dev/null 2>&1 || true
git commit -qm "fixture: bd store with a rolling-window dependency graph" >/dev/null 2>&1 || true
