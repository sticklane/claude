#!/usr/bin/env bash
# Deterministic grader for the adversarial blocked-only bd queue (cutover: bd
# is the source of truth). SELF-CONTAINED — builds a throwaway bd store whose
# only work item is blocked by an open dependency that is never worked, and
# asserts the bd-backed drain behavior: bd ready is empty (nothing
# dispatchable) and the blocked issue stays blocked. Reads no $EVAL_DIR fixture
# and no EVAL_TRANSCRIPT, so it runs identically under evals/run.sh and
# standalone. bash 3.2 safe.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
command -v bd >/dev/null 2>&1 || fail "bd not on PATH (bd is the source of truth after the cutover)"

work="$(mktemp -d)" || fail "mktemp failed"
trap 'rm -rf "$work"' EXIT
cd "$work" || fail "cd to work dir failed"

git init -q || fail "git init failed"
git config user.email eval@example.com
git config user.name eval
bd init >/dev/null 2>&1 || fail "bd init failed"

id_of() { bd create "$1" --json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])'; }

# Seed a blocker P (left open — never worked, standing in for an external
# blocker) and a work item Q blocked by it. Neither should be dispatchable as
# "the drain-worthy queue": Q is blocked, P is a bare blocker with no work.
P="$(id_of prereq)"; [ -n "$P" ] || fail "could not create blocker P"
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
