#!/usr/bin/env bash
# test_status_cutover.sh — proves specs/status.sh reports bd's numbers, not
# markdown's, after the agentic-core-redesign cutover (Migration step 4).
#
# The assertion is a COMPUTED EQUALITY, not a recording: status.sh's total
# must equal the `bd ready --json` count plus every non-ready status reported
# by `bd list --json`. Independently recomputes both sides from bd and fails
# loudly on any divergence; prints `CUTOVER OK` only when they match.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

command -v bd >/dev/null 2>&1 \
  || fail "bd not on PATH; bd is the source of truth after the cutover"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Independently derive bd's expected partition: ready count + non-ready count.
exp="$(python3 - <<'PY'
import json
import subprocess


def bd_json(*args):
    out = subprocess.run(
        ["bd", *args, "--json"], capture_output=True, text=True
    ).stdout or "[]"
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        data = []
    return data if isinstance(data, list) else []


ready = bd_json("ready")
items = bd_json("list")
ready_ids = {i.get("id") for i in ready}
nonready = sum(1 for i in items if i.get("id") not in ready_ids)
print(len(ready_ids), nonready, len(items))
PY
)"
exp_ready="$(printf '%s' "$exp" | awk '{print $1}')"
exp_nonready="$(printf '%s' "$exp" | awk '{print $2}')"
exp_all="$(printf '%s' "$exp" | awk '{print $3}')"

[ -n "$exp_all" ] || fail "could not compute bd counts"

# The partition must sum to the whole (ready is a subset of list).
[ "$((exp_ready + exp_nonready))" = "$exp_all" ] \
  || fail "bd ready($exp_ready) + non-ready($exp_nonready) != bd list total($exp_all)"

# status.sh's own reported 'all' total, and its 'ready' bucket.
sh_out="$(sh "$ROOT/specs/status.sh")" || fail "specs/status.sh exited non-zero"
sh_all="$(printf '%s\n' "$sh_out" | sed -n 's/^  all: //p')"
sh_ready="$(printf '%s\n' "$sh_out" | sed -n 's/^  ready: //p')"
[ -z "$sh_ready" ] && sh_ready=0

[ -n "$sh_all" ] || fail "specs/status.sh printed no 'all:' total"

# The cutover equality: status.sh total == bd ready + non-ready == bd list.
[ "$sh_all" = "$exp_all" ] \
  || fail "status.sh all ($sh_all) != bd ready+non-ready ($exp_all)"
[ "$sh_ready" = "$exp_ready" ] \
  || fail "status.sh ready bucket ($sh_ready) != bd ready count ($exp_ready)"

echo "CUTOVER OK (status.sh all=$sh_all = bd ready $exp_ready + non-ready $exp_nonready)"
