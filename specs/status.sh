#!/bin/sh
# specs/status.sh — live work-state dashboard, derived from bd (beads).
#
# After the agentic-core-redesign cutover (Migration step 4) bd is the
# source of truth for task state; the markdown `Status:` headers are frozen
# display, no longer scanned here. This script is a thin display wrapper over
# `bd ready --json` (the unblocked, dispatchable queue) and `bd list --json`
# (every issue). It prints one "<bucket> <id> <title>" row per issue, then a
# TOTAL section whose counts are: the ready count, plus a count of every
# non-ready bd status. Read-only; requires bd on PATH. No arguments.
set -u

if ! command -v bd >/dev/null 2>&1; then
  echo "bd not found on PATH; bd is the source of truth after the cutover." >&2
  exit 1
fi

python3 <<'PY'
import collections
import json
import subprocess
import sys


def bd_json(*args):
    proc = subprocess.run(
        ["bd", *args, "--json"], capture_output=True, text=True
    )
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        data = []
    return data if isinstance(data, list) else []


ready = bd_json("ready")
items = bd_json("list")
ready_ids = {i.get("id") for i in ready}

if not items:
    print("Queue is empty: bd reports no issues.")
    sys.exit(0)

buckets = collections.Counter()
rows = []
for it in items:
    iid = it.get("id")
    # A ready issue is bucketed 'ready'; everything else by its bd status.
    bucket = "ready" if iid in ready_ids else (it.get("status") or "none")
    buckets[bucket] += 1
    rows.append((bucket, iid or "", it.get("title") or ""))

for bucket, iid, title in rows:
    print("%-12s %-16s %s" % (bucket, iid, title))

print("")
print("TOTAL")
for bucket in sorted(buckets):
    print("  %s: %d" % (bucket, buckets[bucket]))
print("  all: %d" % sum(buckets.values()))
PY
