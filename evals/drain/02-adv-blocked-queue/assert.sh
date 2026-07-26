#!/usr/bin/env bash
# Adversarial blocked-only grader. Under evals/run.sh it inspects the actual
# post-session fixture and proves Codex made no tracker or repository progress.
# Standalone, it keeps the deterministic throwaway-store contract below.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
command -v bd >/dev/null 2>&1 || fail "bd not on PATH (bd is the source of truth after the cutover)"

if [ -f .eval-drain-seed ]; then
  read -r P Q < .eval-drain-seed
  [ -n "$P" ] && [ -n "$Q" ] || fail "fixture seed ids are incomplete"

  status_of() {
    bd show "$1" --json 2>/dev/null |
      python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["status"])'
  }
  [ "$(status_of "$P")" = blocked ] || fail "blocked prerequisite status changed"
  [ "$(status_of "$Q")" = open ] || fail "dependent issue status changed"
  [ ! -e should-not-exist.txt ] || fail "blocked work artifact was created"

  ready="$(bd ready --json 2>/dev/null | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
  [ "$ready" -eq 0 ] || fail "blocked-only fixture unexpectedly has ready work"
  [ "$(git rev-parse HEAD)" = "$(git rev-parse eval-drain-base)" ] ||
    fail "blocked-only drain created a commit"

  git_dir="$(git rev-parse --absolute-git-dir)"
  [ -f "$git_dir/eval-pre-session-status" ] || fail "pre-session Git snapshot is missing"
  before_status="$(cat "$git_dir/eval-pre-session-status")"
  after_status="$(git status --porcelain=v1 -uall | LC_ALL=C sort)"
  [ "$after_status" = "$before_status" ] ||
    fail "blocked-only drain changed the working tree"

  [ -f "$git_dir/eval-pre-session-bd.json" ] || fail "pre-session Beads snapshot is missing"
  before_bd="$(cat "$git_dir/eval-pre-session-bd.json")"
  after_bd="$(bd list --all --json 2>/dev/null |
    python3 -c 'import json,sys; json.dump(json.load(sys.stdin),sys.stdout,sort_keys=True,separators=(",",":"))')"
  [ "$after_bd" = "$before_bd" ] ||
    fail "blocked-only drain mutated tracker state"

  [ -s session.log ] || fail "Codex session.log is missing"
  python3 "$(dirname "$0")/../assert_codex_trajectory.py" session.log blocked ||
    fail "Codex trajectory did not exercise the blocked-only drain path"
  grep -q 'DRAIN_EVAL_BLOCKED_ONLY' session.log || fail "Codex did not report blocked-only stop"
  grep -Eiq '(\.agents/skills/drain/SKILL\.md|using (the installed )?`?drain`? skill|drain skill)' session.log ||
    fail "session has no evidence that Codex loaded or announced the drain skill"

  echo "assert: live Codex blocked-only drain OK (queue empty, full tracker and working tree untouched)"
  exit 0
fi

work="$(mktemp -d)" || fail "mktemp failed"
trap 'rm -rf "$work"' EXIT
cd "$work" || fail "cd to work dir failed"

git init -q || fail "git init failed"
git config user.email eval@example.com
git config user.name eval
bd init >/dev/null 2>&1 || fail "bd init failed"

id_of() { bd create "$1" --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])'; }

# Seed a blocked prerequisite P and a work item Q blocked by it.
P="$(id_of prereq)"; [ -n "$P" ] || fail "could not create blocker P"
bd update "$P" --status blocked >/dev/null 2>&1 || fail "could not block prerequisite P"
Q="$(id_of blocked-feature)"; [ -n "$Q" ] || fail "could not create issue Q"
bd dep add "$Q" --blocked-by "$P" >/dev/null 2>&1 || fail "could not add Q blocked-by P"

# The blocked item Q must NOT appear in bd ready.
ready="$(bd ready --json 2>/dev/null | python3 -c 'import sys,json;print(" ".join(i["id"] for i in json.load(sys.stdin)))')"
echo "$ready" | grep -qw "$Q" && fail "blocked issue Q must NOT be ready, ready=[$ready]"

# Q's stored status is still open/blocked (never advanced to closed) — a
# correct drain never dispatches or closes a non-ready issue.
qstatus="$(bd list --all --json 2>/dev/null | python3 -c "import sys,json
for i in json.load(sys.stdin):
    if i['id']=='$Q':
        print(i['status']); break")"
[ "$qstatus" = "closed" ] && fail "blocked issue Q was closed — drain must not advance a blocked issue"
[ -n "$qstatus" ] || fail "could not read Q's status"

echo "assert: all checks passed (blocked issue excluded from bd ready and left un-closed — drain skips a blocked-only queue)"
