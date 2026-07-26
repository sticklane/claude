#!/usr/bin/env bash
# Grader for the bd-backed drain flow. Under evals/run.sh it inspects the
# actual fixture after the model session, including artifacts, bd state,
# dependency order, and evidence that Codex loaded/announced the drain skill.
# When invoked standalone from the source repo (no .eval-drain-seed), it keeps
# the model-free deterministic bd loop below as a fast contract check.
#
# What it proves about the bd-backed flow:
#   1. bd ready excludes blocked work — a dependent issue is not dispatchable
#      until its blocker closes (dependency propagation).
#   2. the loop drains the ready queue as a rolling window of distinct
#      claim/close admissions (>=3 landings, never one all-at-once barrier).
#   3. dependency ORDER is honored — the dependent issue lands only after its
#      blocker.
#   4. the queue drains to exhaustion — final bd ready is empty and every
#      issue is closed.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
command -v bd >/dev/null 2>&1 || fail "bd not on PATH (bd is the source of truth after the cutover)"

if [ -f .eval-drain-seed ]; then
  read -r A B C < .eval-drain-seed
  [ -n "$A" ] && [ -n "$B" ] && [ -n "$C" ] || fail "fixture seed ids are incomplete"

  status_of() {
    bd show "$1" --json 2>/dev/null |
      python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["status"])'
  }
  [ "$(status_of "$A")" = closed ] || fail "alpha issue was not closed"
  [ "$(status_of "$B")" = closed ] || fail "beta issue was not closed"
  [ "$(status_of "$C")" = closed ] || fail "gamma issue was not closed"

  hex_of() { od -An -t x1 "$1" 2>/dev/null | tr -d ' \n'; }
  [ "$(hex_of alpha.txt)" = 616c7068610a ] || fail "alpha.txt artifact is missing or wrong"
  [ "$(hex_of beta.txt)" = 626574610a ] || fail "beta.txt artifact is missing or wrong"
  [ "$(hex_of gamma.txt)" = 67616d6d610a ] || fail "gamma.txt artifact is missing or wrong"

  ready="$(bd ready --json 2>/dev/null | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
  [ "$ready" -eq 0 ] || fail "bd ready is not empty after live drain"
  [ -z "$(git branch --list 'drain/*')" ] ||
    fail "drain left one or more worker branches behind"
  [ "$(git worktree list --porcelain | grep -c '^worktree ')" -eq 1 ] ||
    fail "drain left one or more worker worktrees behind"
  [ ! -s .beads/session-claims ] || fail "drain left claimed issue bookkeeping behind"
  [ ! -s .beads/session-inflight ] || fail "drain left in-flight issue bookkeeping behind"
  [ -z "$(find .beads -maxdepth 1 -type f -name 'drain-*' -print)" ] ||
    fail "drain left temporary task/input files behind"

  base=eval-drain-base
  git rev-parse -q --verify "$base" >/dev/null || fail "fixture baseline tag is missing"
  landing_commit_for() {
    git log --first-parent --format=%H --diff-filter=A "$base..HEAD" -- "$1" |
      tail -n 1
  }

  alpha_landing="$(landing_commit_for alpha.txt)"
  beta_landing="$(landing_commit_for beta.txt)"
  gamma_landing="$(landing_commit_for gamma.txt)"
  [ -n "$alpha_landing" ] && [ -n "$beta_landing" ] && [ -n "$gamma_landing" ] ||
    fail "one or more first-parent artifact landings are missing"
  distinct_landings="$(printf '%s\n' "$alpha_landing" "$beta_landing" "$gamma_landing" | sort -u | wc -l | tr -d ' ')"
  [ "$distinct_landings" -eq 3 ] || fail "artifacts did not land in 3 distinct commits"

  [ "$alpha_landing" != "$gamma_landing" ] || fail "alpha and gamma collapsed into one landing"
  git merge-base --is-ancestor "$alpha_landing" "$gamma_landing" ||
    fail "gamma landed before its alpha dependency"

  [ -s session.log ] || fail "Codex session.log is missing"
  python3 "$(dirname "$0")/../assert_codex_trajectory.py" session.log rolling ||
    fail "Codex trajectory did not exercise drain orchestration"
  grep -q 'DRAIN_EVAL_COMPLETE' session.log || fail "Codex did not report live drain completion"
  grep -Eiq '(\.agents/skills/drain/SKILL\.md|using (the installed )?`?drain`? skill|drain skill)' session.log ||
    fail "session has no evidence that Codex loaded or announced the drain skill"

  echo "assert: live Codex drain OK (3 isolated workers reviewed and landed, issues closed, dependency order honored, queue empty)"
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
ready_ids() { bd ready --json 2>/dev/null | python3 -c 'import sys,json;print(" ".join(sorted(i["id"] for i in json.load(sys.stdin))))'; }
# --all so closed issues are included (bd list hides them by default).
list_status() { bd list --all --json 2>/dev/null | python3 -c 'import sys,json;print(" ".join(sorted("%s=%s"%(i["id"],i["status"]) for i in json.load(sys.stdin))))'; }

# Seed: A, B dependency-free; C blocked by A.
A="$(id_of alpha)"; [ -n "$A" ] || fail "could not create issue A"
B="$(id_of beta)";  [ -n "$B" ] || fail "could not create issue B"
C="$(id_of gamma)"; [ -n "$C" ] || fail "could not create issue C"
bd dep add "$C" --blocked-by "$A" >/dev/null 2>&1 || fail "could not add C blocked-by A"

# Check 1: initial ready excludes the blocked issue C.
init_ready="$(ready_ids)"
echo "$init_ready" | grep -qw "$A" || fail "A should be ready initially, ready=[$init_ready]"
echo "$init_ready" | grep -qw "$B" || fail "B should be ready initially, ready=[$init_ready]"
echo "$init_ready" | grep -qw "$C" && fail "C is blocked by A and must NOT be ready, ready=[$init_ready]"

# Drive the drain loop: take bd ready's first id, claim, close; repeat until
# the ready queue is empty. Record the close ORDER as distinct landings.
order=""
landings=0
i=0
while [ "$i" -lt 20 ]; do
  top="$(bd ready --json 2>/dev/null | python3 -c 'import sys,json
d=json.load(sys.stdin)
print(d[0]["id"] if d else "")')"
  [ -n "$top" ] || break
  bd update "$top" --claim >/dev/null 2>&1 || fail "claim of $top failed"
  bd close "$top" >/dev/null 2>&1 || fail "close of $top failed"
  order="$order $top"
  landings=$((landings + 1))
  i=$((i + 1))
done

# Check 2: rolling window of distinct admissions, never one barrier.
[ "$landings" -ge 3 ] || fail "expected >=3 distinct claim/close landings, got $landings (order:$order)"

# Check 3: dependency order — C (blocked by A) landed strictly after A.
posA=0; posC=0; n=0
for id in $order; do
  n=$((n + 1))
  [ "$id" = "$A" ] && posA="$n"
  [ "$id" = "$C" ] && posC="$n"
done
[ "$posA" -gt 0 ] || fail "A never landed (order:$order)"
[ "$posC" -gt 0 ] || fail "C never landed (order:$order)"
[ "$posC" -gt "$posA" ] || fail "C (blocked by A) landed at $posC, not after A at $posA — dependency order broken"

# Check 4: queue drained to exhaustion; every issue closed.
final_ready="$(ready_ids)"
[ -z "$final_ready" ] || fail "bd ready not empty after drain: [$final_ready]"
final="$(list_status)"
echo "$final" | grep -q "$A=closed" || fail "A not closed: [$final]"
echo "$final" | grep -q "$B=closed" || fail "B not closed: [$final]"
echo "$final" | grep -q "$C=closed" || fail "C not closed: [$final]"

echo "assert: bd-backed drain flow OK ($landings landings, blocked C excluded until A closed, dependency order honored, queue drained to empty)"
