#!/usr/bin/env bash
# SPEC R-L: `agentic ready` stays O(1) in tracker calls as the queue grows.
#
# Seeds >=500 issues into a scratch bd store, then asserts two things:
#   1. PRIMARY, deterministic: `agentic ready` invokes the `bd` binary a
#      constant handful of times, not once per issue. Counted by putting a
#      recording shim named `bd` ahead of the real one on PATH; every tracker
#      call in the toolkit goes through agentic/bd.py's `shutil.which("bd")`,
#      so the shim sees all of them.
#   2. SECONDARY, wall clock: the median of 5 `agentic ready` runs stays under
#      a ceiling with real headroom, so a gross performance blowup the call
#      count cannot see still surfaces.
#
# The wall-clock arm used to be the only assertion, at a 1s ceiling. That
# ceiling was calibrated at idle and had no headroom: measured medians were
# 0.721s on a quiet host but 4.364s under ordinary background activity and
# 2.058-5.522s with four drain workers sharing the host, so it reddened
# `scripts/check.sh` repo-wide whenever anything else ran.
# docs/memory/wall-clock-perf-assertions.md records the decision and the
# measurements behind the 60s replacement, which is a catastrophe backstop
# rather than a performance budget.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

MAX_BD_CALLS=5
CEILING_SECONDS=60

if ! command -v bd >/dev/null 2>&1; then
  echo "SKIP: bd not installed"
  exit 0
fi
REAL_BD="$(command -v bd)"

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

mkdir -p "$T/shim"
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*" >> "%s/bd-calls.log"\nexec "%s" "$@"\n' \
  "$T" "$REAL_BD" > "$T/shim/bd"
chmod +x "$T/shim/bd"
: > "$T/bd-calls.log"

PATH="$T/shim:$PATH" "$AGENTIC" ready >/dev/null 2>&1 \
  || { echo "FAIL: agentic ready exited nonzero"; exit 1; }
calls="$(wc -l < "$T/bd-calls.log" | tr -d ' ')"
if [ "$calls" -gt "$MAX_BD_CALLS" ]; then
  echo "FAIL: agentic ready made $calls bd calls at $count issues (> $MAX_BD_CALLS) — per-issue tracker calls"
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
$(python3 - "$CEILING_SECONDS" "${times[@]}" <<'PY'
import sys
ceiling = float(sys.argv[1])
xs = sorted(float(x) for x in sys.argv[2:])
med = xs[len(xs) // 2]
print(f"{med:.3f}", "OK" if med < ceiling else "SLOW")
PY
)
EOF

if [ "$ok" = "OK" ]; then
  echo "BD-CALLS ${calls} (<= ${MAX_BD_CALLS}) OK; MEDIAN ${median}s (< ${CEILING_SECONDS}s) OK ($count issues seeded)"
  exit 0
fi
echo "FAIL: MEDIAN ${median}s exceeds ${CEILING_SECONDS}s ceiling ($count issues)"
exit 1
