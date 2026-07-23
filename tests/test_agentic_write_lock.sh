#!/usr/bin/env bash
# SPEC R-C (a) / D8: tracker writes are serialized by a repo-level lock, not by
# convention. Two concurrent `agentic verdict` commands in ONE checkout must
# both be recorded with no lost JSONL export (the lock serializes their
# pull→apply→export→commit sequences). Then a STALE lock (dead PID, old mtime)
# must be taken over by a later write command after the stale timeout — D8's
# recovery is a tested behavior, not a promise.
#
# Prints `LOCK OK` and `STALE TAKEOVER OK` on success; exits nonzero otherwise.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

command -v bd >/dev/null 2>&1 || { echo "SKIP: bd not installed"; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

STORE="$WORK/store"
mkdir -p "$STORE"
cd "$STORE"
git init -q .
git config user.name test
git config user.email test@example.com
BD_NON_INTERACTIVE=1 bd init --prefix lk >/dev/null 2>&1

# Seed two open tasks via a committed JSONL import (the same transport agentic
# uses). Distinct IDs and Touch so both verdicts are independent writes.
cat > seed.jsonl <<'JSONL'
{"id":"lk-a","title":"task a","status":"open","priority":1,"issue_type":"task","metadata":{"touch":["a.py"]}}
{"id":"lk-b","title":"task b","status":"open","priority":1,"issue_type":"task","metadata":{"touch":["b.py"]}}
JSONL
bd import seed.jsonl >/dev/null 2>&1
bd export -o .beads/issues.jsonl >/dev/null 2>&1
git add .beads/issues.jsonl .beads/config.yaml >/dev/null 2>&1
git commit -qm "seed tracker"

echo '{"status":"DONE","summary":"a done"}' > va.json
echo '{"status":"DONE","summary":"b done"}' > vb.json

# --- concurrent writes -----------------------------------------------------
BD_NON_INTERACTIVE=1 "$AGENTIC" verdict lk-a --file va.json >"$WORK/a.log" 2>&1 &
PID_A=$!
BD_NON_INTERACTIVE=1 "$AGENTIC" verdict lk-b --file vb.json >"$WORK/b.log" 2>&1 &
PID_B=$!
wait $PID_A; RC_A=$?
wait $PID_B; RC_B=$?

if [ "$RC_A" -ne 0 ] || [ "$RC_B" -ne 0 ]; then
  echo "LOCK FAIL: a=$RC_A b=$RC_B"
  echo "--- a.log ---"; cat "$WORK/a.log"
  echo "--- b.log ---"; cat "$WORK/b.log"
  exit 1
fi

# Both recorded in bd.
STATUS_A="$(bd show lk-a --json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["status"])')"
STATUS_B="$(bd show lk-b --json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["status"])')"
if [ "$STATUS_A" != "closed" ] || [ "$STATUS_B" != "closed" ]; then
  echo "LOCK FAIL: bd status a=$STATUS_A b=$STATUS_B (expected both closed)"
  exit 1
fi

# The FINAL committed JSONL contains BOTH closes — no export was clobbered.
COMMITTED="$(git show HEAD:.beads/issues.jsonl 2>/dev/null)"
CLOSED_COUNT="$(printf '%s\n' "$COMMITTED" | python3 -c '
import json,sys
c=0
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    o=json.loads(line)
    if o.get("id") in ("lk-a","lk-b") and o.get("status")=="closed":
        c+=1
print(c)')"
if [ "$CLOSED_COUNT" != "2" ]; then
  echo "LOCK FAIL: committed JSONL has $CLOSED_COUNT/2 closed (lost export)"
  exit 1
fi
echo "LOCK OK"

# --- stale-lock takeover ---------------------------------------------------
# Plant a lock owned by a dead PID with an old mtime, then run a write with a
# short stale timeout; it must reclaim the lock and record the verdict.
LOCK="$STORE/.beads/agentic.lock"
DEAD_PID=999999
while kill -0 "$DEAD_PID" 2>/dev/null; do DEAD_PID=$((DEAD_PID+1)); done
printf '{"pid": %s, "host": "otherhost", "time": 0}' "$DEAD_PID" > "$LOCK"
# Age the lock file well past the stale timeout.
touch -t 202001010000 "$LOCK"

echo '{"status":"DONE","summary":"c after takeover"}' > vc.json
cat > seed2.jsonl <<'JSONL'
{"id":"lk-c","title":"task c","status":"open","priority":1,"issue_type":"task","metadata":{"touch":["c.py"]}}
JSONL
bd import seed2.jsonl >/dev/null 2>&1

AGENTIC_LOCK_STALE_SECS=1 BD_NON_INTERACTIVE=1 "$AGENTIC" verdict lk-c --file vc.json >"$WORK/c.log" 2>&1
RC_C=$?
if [ "$RC_C" -ne 0 ]; then
  echo "STALE TAKEOVER FAIL: verdict exited $RC_C"
  cat "$WORK/c.log"
  exit 1
fi
STATUS_C="$(bd show lk-c --json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["status"])')"
if [ "$STATUS_C" != "closed" ]; then
  echo "STALE TAKEOVER FAIL: lk-c status=$STATUS_C (expected closed)"
  exit 1
fi
echo "STALE TAKEOVER OK"
