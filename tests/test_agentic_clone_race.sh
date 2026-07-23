#!/usr/bin/env bash
# SPEC R-C (b) / D9: git is the only transport; two clones writing near-
# simultaneously serialize on push order. The loser pulls, re-imports the
# remote JSONL, and re-applies its semantic operation — landing after a retry
# (distinct tasks) or failing cleanly with "already claimed" (same task). The
# remote's committed JSONL must contain every surviving operation.
#
# Prints `RACE OK` on success; exits nonzero otherwise.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

command -v bd >/dev/null 2>&1 || { echo "SKIP: bd not installed"; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- source repo + bare remote --------------------------------------------
SRC="$WORK/src"
mkdir -p "$SRC"; cd "$SRC"
git init -q .; git config user.name test; git config user.email test@example.com
BD_NON_INTERACTIVE=1 bd init --prefix rc >/dev/null 2>&1
cat > seed.jsonl <<'JSONL'
{"id":"rc-x","title":"task x","status":"open","priority":1,"issue_type":"task","metadata":{"touch":["x.py"]}}
{"id":"rc-y","title":"task y","status":"open","priority":1,"issue_type":"task","metadata":{"touch":["y.py"]}}
{"id":"rc-z","title":"task z","status":"open","priority":1,"issue_type":"task","metadata":{"touch":["z.py"]}}
JSONL
bd import seed.jsonl >/dev/null 2>&1
bd export -o .beads/issues.jsonl >/dev/null 2>&1
git add .beads/issues.jsonl .beads/config.yaml >/dev/null 2>&1
git commit -qm "seed tracker"

REMOTE="$WORK/remote.git"
git clone -q --bare "$SRC" "$REMOTE" 2>/dev/null

setup_clone() {  # $1 = dir
  git clone -q "$REMOTE" "$1" 2>/dev/null
  cd "$1"
  git config user.name test; git config user.email test@example.com
  BD_NON_INTERACTIVE=1 "$AGENTIC" init >/dev/null 2>&1 || { echo "init failed in $1"; exit 1; }
}

C1="$WORK/c1"; C2="$WORK/c2"
setup_clone "$C1"
setup_clone "$C2"

remote_status() {  # $1 = issue id -> its status in the remote's committed JSONL
  git -C "$REMOTE" show HEAD:.beads/issues.jsonl 2>/dev/null | python3 -c '
import json,sys
want=sys.argv[1]
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    o=json.loads(line)
    if o.get("id")==want:
        print(o.get("status")); break
' "$1"
}

# --- scenario A: distinct tasks, both must land ----------------------------
( cd "$C1" && BD_ACTOR=alice BD_NON_INTERACTIVE=1 "$AGENTIC" claim rc-x ) >"$WORK/a1.log" 2>&1 &
P1=$!
( cd "$C2" && BD_ACTOR=bob BD_NON_INTERACTIVE=1 "$AGENTIC" claim rc-y ) >"$WORK/a2.log" 2>&1 &
P2=$!
wait $P1; RA1=$?
wait $P2; RA2=$?
if [ "$RA1" -ne 0 ] || [ "$RA2" -ne 0 ]; then
  echo "RACE FAIL (distinct): rc-x=$RA1 rc-y=$RA2"
  echo "--- a1 ---"; cat "$WORK/a1.log"; echo "--- a2 ---"; cat "$WORK/a2.log"
  exit 1
fi
SX="$(remote_status rc-x)"; SY="$(remote_status rc-y)"
if [ "$SX" != "in_progress" ] || [ "$SY" != "in_progress" ]; then
  echo "RACE FAIL (distinct): remote JSONL x=$SX y=$SY (expected both in_progress)"
  exit 1
fi

# --- scenario B: same task, exactly one wins; loser fails cleanly ----------
( cd "$C1" && BD_ACTOR=alice BD_NON_INTERACTIVE=1 "$AGENTIC" claim rc-z ) >"$WORK/b1.log" 2>&1 &
Q1=$!
( cd "$C2" && BD_ACTOR=bob BD_NON_INTERACTIVE=1 "$AGENTIC" claim rc-z ) >"$WORK/b2.log" 2>&1 &
Q2=$!
wait $Q1; RB1=$?
wait $Q2; RB2=$?
WINS=$(( (RB1==0) + (RB2==0) ))
if [ "$WINS" -ne 1 ]; then
  echo "RACE FAIL (same task): expected exactly one winner, got $WINS (rc-z: c1=$RB1 c2=$RB2)"
  echo "--- b1 ---"; cat "$WORK/b1.log"; echo "--- b2 ---"; cat "$WORK/b2.log"
  exit 1
fi
# The loser's message names the clean semantic failure.
LOSER_LOG="$WORK/b1.log"; [ "$RB1" -eq 0 ] && LOSER_LOG="$WORK/b2.log"
if ! grep -qi "already claimed" "$LOSER_LOG"; then
  echo "RACE FAIL (same task): loser did not report 'already claimed'"
  cat "$LOSER_LOG"
  exit 1
fi
SZ="$(remote_status rc-z)"
if [ "$SZ" != "in_progress" ]; then
  echo "RACE FAIL (same task): remote JSONL z=$SZ (expected in_progress)"
  exit 1
fi

echo "RACE OK"
