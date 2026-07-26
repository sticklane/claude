#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty dir the runner provides): a git
# repo with a bd (beads) store whose prerequisite is explicitly blocked and
# whose dependent work item therefore cannot enter bd ready. A real drain run
# must stop without claiming, closing, reopening, or editing either issue.
set -eu

cd "$EVAL_DIR"
git init -q
git config user.email eval@example.com
git config user.name eval

command -v bd >/dev/null 2>&1
bd init >/dev/null 2>&1
P="$(bd create "prereq (synthetic upstream unavailable)" \
  --description "Fixture-owned non-human upstream sentinel; deliberately not dispatchable and exposes no human action." \
  --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')"
bd update "$P" --status blocked >/dev/null
Q="$(bd create "blocked-feature" \
  --description "Must remain untouched until the blocked prerequisite closes." \
  --acceptance 'test -f should-not-exist.txt' \
  --metadata '{"touch":["should-not-exist.txt"],"rigor":"small"}' \
  --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')"
bd dep add "$Q" --blocked-by "$P" >/dev/null
printf '%s %s\n' "$P" "$Q" > .eval-drain-seed

git add -A >/dev/null 2>&1 || true
git commit -qm "fixture: blocked-only queue"
git tag eval-drain-base
