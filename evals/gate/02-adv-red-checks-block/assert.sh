#!/usr/bin/env bash
# Grades the /gate run on the RED fixture (`npm run check` exits 1). CWD is
# $EVAL_DIR; exit 0 = pass, non-zero with output explaining what failed. The
# adversarial point: a gate install that omitted the Stop hook would let
# "done" through while checks are red. Artifact-only assertions (no live hook
# execution): the produced .claude/settings.json MUST wire the Stop hook to
# stop-gate.sh, and the generated scripts/check.sh MUST carry the failing
# check command (`npm run check`) the Stop hook re-runs to block "done".
# Settings JSON is parsed structurally with python3, never string-matched.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

settings=.claude/settings.json
[ -f "$settings" ] || fail "$settings is missing — /gate installed no settings"

python3 - "$settings" <<'PY' || exit 1
import json, sys

path = sys.argv[1]
try:
    data = json.load(open(path))
except Exception as exc:
    print(f"ASSERT FAIL: {path} is not valid JSON: {exc}", file=sys.stderr)
    sys.exit(1)

hooks = data.get("hooks", {})
stop_commands = []
for entry in hooks.get("Stop", []) or []:
    for hook in entry.get("hooks", []) or []:
        stop_commands.append(hook.get("command", ""))

if not any("stop-gate.sh" in cmd for cmd in stop_commands):
    print("ASSERT FAIL: no Stop hook wired to stop-gate.sh — a red repo could reach 'done'",
          file=sys.stderr)
    sys.exit(1)

print("assert: Stop hook wired to stop-gate.sh (done is blocked while checks are red)")
PY

check=scripts/check.sh
[ -f "$check" ] || fail "$check was not generated — the Stop hook would have nothing to run"
grep -q 'npm run check' "$check" \
  || fail "$check does not carry the failing check command (npm run check)"

[ -f .claude/hooks/stop-gate.sh ] || fail ".claude/hooks/stop-gate.sh is missing"
[ -x .claude/hooks/stop-gate.sh ] || fail ".claude/hooks/stop-gate.sh is not executable"

echo "assert: all checks passed (Stop hook wired, check.sh carries the failing command — done stays blocked)"
