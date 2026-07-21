#!/usr/bin/env bash
# Grades the /gate run on the GREEN fixture. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed. Artifact-only checks (no live
# hook execution — evals grade what a run produced): the produced
# .claude/settings.json wires all three gate hooks, the hook scripts exist
# and are executable, and scripts/check.sh was generated. Settings JSON is
# parsed structurally with python3 (json.load + key checks), never
# string-matched against exact output.
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

def commands(event):
    result = []
    for entry in hooks.get(event, []) or []:
        for hook in entry.get("hooks", []) or []:
            result.append(hook.get("command", ""))
    return result

def wired(event, needle):
    return any(needle in cmd for cmd in commands(event))

errors = []
if not wired("Stop", "stop-gate.sh"):
    errors.append("Stop hook not wired to stop-gate.sh")
if not wired("PostToolUse", "post-tool-format.sh"):
    errors.append("PostToolUse hook not wired to post-tool-format.sh")
if not wired("PreToolUse", "pre-tool-protect.sh"):
    errors.append("PreToolUse hook not wired to pre-tool-protect.sh")

if errors:
    for err in errors:
        print("ASSERT FAIL:", err, file=sys.stderr)
    sys.exit(1)

print("assert: settings.json wires Stop + PostToolUse + PreToolUse gate hooks")
PY

for hook in stop-gate post-tool-format pre-tool-protect; do
  file=".claude/hooks/$hook.sh"
  [ -f "$file" ] || fail "$file is missing"
  [ -x "$file" ] || fail "$file is not executable"
done

[ -f scripts/check.sh ] || fail "scripts/check.sh was not generated"

echo "assert: all checks passed (three gate hooks wired, hook scripts present+executable, check.sh generated)"
