#!/usr/bin/env bash
# SPEC R-L: per-command tracker latency ceiling is 1s, re-measured at scale.
# Seeds >=500 issues into a scratch bd store, runs `agentic ready` 5 times,
# and asserts the MEDIAN wall time is under 1s. Prints `MEDIAN <n>s OK`.
#
# `agentic ready` makes a single `bd export` read plus in-process frontier
# math, so latency is dominated by one bd call; this guards against a
# regression to per-issue bd calls.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

if ! command -v bd >/dev/null 2>&1; then
  echo "SKIP: bd not installed"
  exit 0
fi

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
cd "$T"
git init -q .
git config user.name test
git config user.email test@example.com

BD_NON_INTERACTIVE=1 bd init --prefix lat >/dev/null 2>&1

# Seed 600 issues (>= 500) in one bulk import: a spread of priorities and a
# distinct Touch path each so most are co-admissible.
python3 - "$T/seed.jsonl" <<'PY'
import json, sys
rows = []
for n in range(600):
    rows.append({
        "id": f"lat-{n:04d}",
        "title": f"seeded task {n}",
        "status": "open",
        "priority": n % 4,
        "issue_type": "task",
        "metadata": {"touch": [f"src/mod{n:04d}.py"]},
    })
with open(sys.argv[1], "w") as fh:
    fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
PY

bd import "$T/seed.jsonl" >/dev/null 2>&1

count="$(bd list --all --json 2>/dev/null | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))')"
if [ "$count" -lt 500 ]; then
  echo "FAIL: seeded only $count issues (< 500)"
  exit 1
fi

# Time 5 runs; compute the median in Python for a robust central measure.
times=()
for _ in 1 2 3 4 5; do
  start="$(python3 -c 'import time;print(time.time())')"
  "$AGENTIC" ready >/dev/null 2>&1 || { echo "FAIL: agentic ready exited nonzero"; exit 1; }
  end="$(python3 -c 'import time;print(time.time())')"
  times+=("$(python3 -c "print($end - $start)")")
done

read -r median ok <<EOF
$(python3 - "${times[@]}" <<'PY'
import sys
xs = sorted(float(x) for x in sys.argv[1:])
med = xs[len(xs) // 2]
print(f"{med:.3f}", "OK" if med < 1.0 else "SLOW")
PY
)
EOF

if [ "$ok" = "OK" ]; then
  echo "MEDIAN ${median}s OK ($count issues seeded)"
  exit 0
fi
echo "FAIL: MEDIAN ${median}s exceeds 1s ceiling ($count issues)"
exit 1
