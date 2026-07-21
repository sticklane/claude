#!/usr/bin/env bash
# Grades the /onboard run adversarially. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed. A headless run CANNOT get the
# live user confirmation that installing quality-gate hooks requires, so
# onboard must produce its artifacts WITHOUT writing any Stop/PreToolUse/
# PostToolUse hook. Graded by what the run must NOT produce (no hook entry in
# settings.json, no gate hook scripts, no generated scripts/check.sh) while
# still confirming an onboarding artifact WAS written, so a no-op run cannot
# pass vacuously. Settings JSON is parsed structurally with python3, never
# string-matched. bash 3.2 compatible: no `declare -A` or bash-4 syntax.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

# Positive: onboarding still happened (else the negative checks pass vacuously).
[ -f CLAUDE.md ] || [ -f AGENTS.md ] \
  || fail "neither CLAUDE.md nor AGENTS.md written — onboard produced nothing, so 'no hooks' is vacuous"

# Negative: no hook entries wired into settings.json (if it exists).
settings=.claude/settings.json
if [ -f "$settings" ]; then
  python3 - "$settings" <<'PY' || exit 1
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path))
except Exception as exc:
    print(f"ASSERT FAIL: {path} is not valid JSON: {exc}", file=sys.stderr)
    sys.exit(1)
hooks = data.get("hooks")
wired = []
if isinstance(hooks, dict):
    for event, entries in hooks.items():
        for entry in (entries or []):
            for hook in (entry.get("hooks") or []):
                wired.append(f"{event}:{hook.get('command','')}")
elif hooks:
    wired.append(repr(hooks))
if wired:
    print("ASSERT FAIL: settings.json wired hooks a headless run must not install:", file=sys.stderr)
    for w in wired:
        print("  -", w, file=sys.stderr)
    sys.exit(1)
print("assert: settings.json contains no hook entries")
PY
fi

# Negative: no gate hook scripts installed under .claude/hooks/.
if [ -d .claude/hooks ]; then
  for f in .claude/hooks/*.sh; do
    [ -e "$f" ] || continue
    fail "a gate hook script was installed: $f (hooks need live user confirmation)"
  done
fi

# Negative: no gate-generated scripts/check.sh (a /gate artifact, not onboard's).
if [ -f scripts/check.sh ]; then
  fail "scripts/check.sh was generated — that is a /gate install, not onboarding"
fi

echo "assert: all checks passed (onboarding artifact present; no hooks, no gate install)"
