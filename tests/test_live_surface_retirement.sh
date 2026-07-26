#!/usr/bin/env bash
# R4 live-surface retirement contract. The frozen baseline is authoritative:
# only its four retire-dead workflows may disappear, while retained execution
# surfaces and historical evidence stay available.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASELINE="$ROOT/specs/toolkit-core-simplification/BASELINE.json"

pass=0
fail=0

assert() { # assert <description> <command...>
  local description="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $description" >&2
  fi
}

refute() { # refute <description> <command...>
  local description="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $description" >&2
  else
    pass=$((pass + 1))
  fi
}

retire_dead_paths() {
  python3 - "$BASELINE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    baseline = json.load(handle)
for surface in baseline["surfaces"]:
    if surface["disposition"] == "retire-dead":
        print(surface["path"])
PY
}

expected_retire_dead='.claude/workflows/cross-repo-beads-adoption.js
.claude/workflows/full-cutover-and-health-check.js
.claude/workflows/ultracode-queue-sweep.js
.claude/workflows/ultracode-queue-sweep-phase2.js'
actual_retire_dead="$(retire_dead_paths)"
assert "baseline has exactly the four approved retire-dead workflow rows" \
  test "$actual_retire_dead" = "$expected_retire_dead"

while IFS= read -r path; do
  assert "retire-dead workflow is absent: $path" test ! -e "$ROOT/$path"
done <<EOF
$actual_retire_dead
EOF

assert "deep-research workflow remains live" \
  test -f "$ROOT/.claude/workflows/deep-research.js"
assert "standalone ctx implementation remains live" \
  test -f "$ROOT/context-tree/Cargo.toml"
assert "native orchestration remains documented for Claude Code" \
  grep -qF '## Orchestration' "$ROOT/runtimes/claude-code.md"
assert "native orchestration remains documented for Codex" \
  grep -qF 'Codex collaboration subagents' "$ROOT/runtimes/codex.md"
assert "native orchestration remains documented for Antigravity" \
  grep -qF 'Native subagents' "$ROOT/runtimes/antigravity.md"

live_discovery_files="$ROOT/.claude/rules/token-discipline.md
$ROOT/bin/check-token-discipline
$ROOT/runtimes/antigravity.md
$ROOT/runtimes/claude-code.md
$ROOT/runtimes/codex.md
$ROOT/antigravity/README.md
$ROOT/codex/README.md
$ROOT/docs/agent-dashboards.md
$ROOT/docs/decisions/orchestration.md
$ROOT/docs/decisions/orchestrator-context.md"

while IFS= read -r workflow; do
  refute "live discovery does not name retired workflow: $workflow" \
    grep -F "$workflow" $live_discovery_files
done <<'EOF'
cross-repo-beads-adoption
full-cutover-and-health-check
ultracode-queue-sweep
ultracode-queue-sweep-phase2
EOF

refute "live guidance does not recommend deleted drain_frontier.py" \
  grep -F 'drain_frontier.py' $live_discovery_files
refute "audit no longer recommends the retired composer" \
  grep -E 'compose-bypass|agentic compose' \
    "$ROOT/agentic/audit.py" "$ROOT/tests/test_agentic_audit.py"
refute "runtime profiles do not claim retired mirrored ports are live" \
  grep -Ei 'reference port|port root|mirrored runtimes' \
    "$ROOT/runtimes/antigravity.md" \
    "$ROOT/runtimes/claude-code.md" \
    "$ROOT/runtimes/codex.md"

live_install_and_frontier_files="$ROOT/README.md
$ROOT/docs/porting.md
$ROOT/runtimes/README.md
$ROOT/agentic/frontier.py
$ROOT/agentic/ready.py"

refute "live install and frontier guidance does not name retired surfaces" \
  grep -Ei \
    'reference port|mirrored port|mirror tree|antigravity/\.agents|antigravity/AGENTS\.md|drain_frontier\.py' \
    $live_install_and_frontier_files

assert "historical architecture record still names the retired composer" \
  grep -qF 'agentic compose' "$ROOT/docs/architecture-pivot-2026-07-22.md"
assert "historical task-tracking research remains readable" \
  grep -qF 'Status: research complete' \
    "$ROOT/docs/task-tracking-design-research-2026-07.md"

echo "test_live_surface_retirement: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
