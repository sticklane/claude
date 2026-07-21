#!/usr/bin/env bash
# Grades the /onboard run on the un-onboarded fixture. CWD is $EVAL_DIR;
# exit 0 = pass, non-zero with output explaining what failed. Artifact-only
# (no live rerun): assert the orientation split was written (CLAUDE.md +
# AGENTS.md), both docs are size-bounded (<=200 lines each), the verified
# check command was captured into the orientation docs, and a
# .claude/settings.json permission allowlist was produced. Settings JSON is
# parsed structurally with python3, never string-matched against exact output.
# bash 3.2 compatible: no `declare -A` or bash-4 syntax.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

[ -f CLAUDE.md ] || fail "CLAUDE.md was not written"
[ -f AGENTS.md ] || fail "AGENTS.md was not written (onboard's default is the orientation split)"

# Size bound: onboard targets both files well under 200 lines.
claude_lines="$(wc -l < CLAUDE.md | tr -d '[:space:]')"
agents_lines="$(wc -l < AGENTS.md | tr -d '[:space:]')"
[ "$claude_lines" -le 200 ] || fail "CLAUDE.md is $claude_lines lines (>200)"
[ "$agents_lines" -le 200 ] || fail "AGENTS.md is $agents_lines lines (>200)"

# The verified command must appear in the orientation docs: onboard RUNS it in
# step 2 and records it in AGENTS.md's ## Commands (or CLAUDE.md) in step 3.
grep -q 'run-tests.sh' AGENTS.md CLAUDE.md \
  || fail "the verified check command (run-tests.sh) is in neither AGENTS.md nor CLAUDE.md"

settings=.claude/settings.json
[ -f "$settings" ] || fail "$settings is missing — onboard added no permission allowlist"

python3 - "$settings" <<'PY' || exit 1
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path))
except Exception as exc:
    print(f"ASSERT FAIL: {path} is not valid JSON: {exc}", file=sys.stderr)
    sys.exit(1)
allow = (data.get("permissions") or {}).get("allow")
if not isinstance(allow, list) or not allow:
    print("ASSERT FAIL: settings.json has no non-empty permissions.allow allowlist", file=sys.stderr)
    sys.exit(1)
print("assert: settings.json carries a non-empty permissions.allow allowlist")
PY

echo "assert: all checks passed (orientation split written + size-bounded, command captured, allowlist present)"
