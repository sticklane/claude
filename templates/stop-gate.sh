#!/usr/bin/env bash
# Claude Code Stop hook (SPEC R10): run the repo's canonical check before
# allowing the session to stop. Self-contained; installed verbatim into
# .claude/hooks/. Fail-open ONLY when scripts/check.sh is missing/unreadable;
# any non-zero exit from an existing check script exits 2 with its output.
set -u

warn() { printf 'stop-gate: %s\n' "$1" >&2; }

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; skipping check"
  exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; skipping check"
  exit 0
fi
if ! active="$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)"; then
  warn "warning: malformed hook JSON on stdin; skipping check"
  exit 0
fi
if [ "$active" = "true" ]; then
  exit 0  # loop protection: a previous Stop-hook rejection is already active
fi

# Resolve the repo root: hook JSON cwd if present, else current directory,
# widened to the enclosing git toplevel when available.
hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"
if [ -n "$hook_cwd" ] && [ -d "$hook_cwd" ]; then
  cd "$hook_cwd" || { warn "warning: cannot cd to $hook_cwd; skipping check"; exit 0; }
fi
root="$(git rev-parse --show-toplevel 2>/dev/null)" || root="$PWD"

check="$root/scripts/check.sh"
if [ ! -f "$check" ] || [ ! -r "$check" ]; then
  warn "warning: $check missing or unreadable; skipping check (fail-open)"
  exit 0
fi

output="$(cd "$root" && bash "$check" 2>&1)"
status=$?
if [ "$status" -ne 0 ]; then
  printf '%s\n' "$output" >&2
  exit 2
fi
exit 0
