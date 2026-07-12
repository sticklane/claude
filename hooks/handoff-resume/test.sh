#!/usr/bin/env bash
# Unit tests for resume-check.sh — the handoff-resume SessionStart hook.
# Builds throwaway project trees under mktemp -d, never touches real
# session data or a real HANDOFF.md.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/resume-check.sh"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1"
  fi
}

# --- no HANDOFF.md anywhere: silent no-op ---------------------------------
tmp="$(mktemp -d)"
out="$(CLAUDE_PROJECT_DIR="$tmp" bash "$HOOK" </dev/null)"
rc=$?
check "no-handoff: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-handoff: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp"

# --- one HANDOFF.md at .claude/HANDOFF.md: names it, instructs resume ----
tmp="$(mktemp -d)"
mkdir -p "$tmp/.claude"
echo "fixture handoff" > "$tmp/.claude/HANDOFF.md"
out="$(CLAUDE_PROJECT_DIR="$tmp" bash "$HOOK" </dev/null)"
rc=$?
check "one-handoff: mentions the path" \
  "$(printf '%s' "$out" | grep -qF "$tmp/.claude/HANDOFF.md" && echo 0 || echo 1)"
check "one-handoff: instructs to continue" \
  "$(printf '%s' "$out" | grep -qi "continue" && echo 0 || echo 1)"
check "one-handoff: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp"

# --- two HANDOFF.md files: lists both, asks the session to pick ----------
tmp="$(mktemp -d)"
mkdir -p "$tmp/.claude" "$tmp/specs/demo"
echo "a" > "$tmp/.claude/HANDOFF.md"
echo "b" > "$tmp/specs/demo/HANDOFF.md"
out="$(CLAUDE_PROJECT_DIR="$tmp" bash "$HOOK" </dev/null)"
rc=$?
check "two-handoffs: mentions both paths" \
  "$(printf '%s' "$out" | grep -qF "$tmp/.claude/HANDOFF.md" \
     && printf '%s' "$out" | grep -qF "$tmp/specs/demo/HANDOFF.md" \
     && echo 0 || echo 1)"
check "two-handoffs: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp"

# --- a HANDOFF.md that only exists inside a worktree copy: ignored -------
tmp="$(mktemp -d)"
mkdir -p "$tmp/.claude/worktrees/agent-x"
echo "throwaway" > "$tmp/.claude/worktrees/agent-x/HANDOFF.md"
out="$(CLAUDE_PROJECT_DIR="$tmp" bash "$HOOK" </dev/null)"
rc=$?
check "worktree-only: empty stdout (excluded)" "$([ -z "$out" ] && echo 0 || echo 1)"
check "worktree-only: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp"

# --- a HANDOFF.md that only exists inside a fixtures dir: ignored --------
tmp="$(mktemp -d)"
mkdir -p "$tmp/tests/fixtures/demo-repo"
echo "fixture double" > "$tmp/tests/fixtures/demo-repo/HANDOFF.md"
out="$(CLAUDE_PROJECT_DIR="$tmp" bash "$HOOK" </dev/null)"
rc=$?
check "fixtures-only: empty stdout (excluded)" "$([ -z "$out" ] && echo 0 || echo 1)"
check "fixtures-only: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp"

echo "----"
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
