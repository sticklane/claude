#!/usr/bin/env bash
# SPEC R-E: all tracker state is recoverable from ordinary git alone.
# Scratch git repo + committed JSONL fixture: wipe the Dolt store, rebuild it
# with `agentic init` (import), re-export, and diff the two JSONLs with the
# volatile timestamp fields filtered out. A zero-record diff prints ROUNDTRIP OK.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
cd "$T"
git init -q .
git config user.name test
git config user.email test@example.com

# Seed a tracker with a few issues and commit the exported JSONL (the transport).
BD_NON_INTERACTIVE=1 bd init --prefix rt >/dev/null 2>&1
bd create "roundtrip issue A" >/dev/null 2>&1
bd create "roundtrip issue B" >/dev/null 2>&1
bd create "roundtrip issue C" >/dev/null 2>&1
bd export -o .beads/issues.jsonl 2>/dev/null
git add .beads/issues.jsonl
git commit -qm "seed committed jsonl"

# Prove recovery from git alone: drop the Dolt store entirely.
rm -rf .beads/embeddeddolt

"$AGENTIC" init >/dev/null 2>&1 || { echo "agentic init failed"; exit 1; }

# Re-export from the rebuilt store and compare, filtering volatile *_at fields.
bd export -o "$T/reexport.jsonl" 2>/dev/null

normalize() {
  python3 - "$1" <<'PY'
import json, sys
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in sorted(o.items()) if not k.endswith("_at")}
    if isinstance(o, list):
        return [strip(x) for x in o]
    return o
rows = []
with open(sys.argv[1]) as fh:
    for line in fh:
        line = line.strip()
        if line:
            rows.append(strip(json.loads(line)))
rows.sort(key=lambda d: d.get("id", ""))
for r in rows:
    print(json.dumps(r, sort_keys=True))
PY
}

normalize .beads/issues.jsonl > "$T/a.norm"
normalize "$T/reexport.jsonl" > "$T/b.norm"

if diff -u "$T/a.norm" "$T/b.norm"; then
  echo "ROUNDTRIP OK"
else
  echo "ROUNDTRIP FAIL: re-export differs from committed JSONL"
  exit 1
fi
