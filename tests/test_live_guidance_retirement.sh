#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pass=0
fail=0

refute() {
  local description="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $description" >&2
  else
    pass=$((pass + 1))
  fi
}

live_guidance_files="$ROOT/README.md
$ROOT/docs/porting.md
$ROOT/runtimes/README.md
$ROOT/runtimes/antigravity.md
$ROOT/runtimes/codex.md
$ROOT/agentic/frontier.py
$ROOT/agentic/ready.py"

refute "live guidance does not name retired runtime surfaces" \
  grep -Ei \
    'reference port|mirrored port|mirror tree|antigravity/\.agents|antigravity/AGENTS\.md|drain_frontier\.py|launch-gated skills|allow_implicit_invocation|What degrades on Codex' \
    $live_guidance_files

echo "test_live_guidance_retirement: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
