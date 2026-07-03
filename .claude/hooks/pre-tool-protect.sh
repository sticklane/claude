#!/usr/bin/env bash
# Claude Code PreToolUse hook (SPEC R12): deny Edit/Write to protected files
# (.env*, lockfiles, anything under .git/) with an actionable one-line reason
# on stderr and exit 2. Self-contained; installed verbatim into .claude/hooks/.
# Fails open (exit 0 + warning) on unparseable input, but always denies a
# protected path it can parse (SPEC R13).
set -u

warn() { printf 'pre-tool-protect: %s\n' "$1" >&2; }
deny() { printf 'pre-tool-protect: %s\n' "$1" >&2; exit 2; }

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; allowing"
  exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; allowing"
  exit 0
fi
if ! file="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"; then
  warn "warning: malformed hook JSON on stdin; allowing"
  exit 0
fi
if [ -z "$file" ]; then
  warn "warning: no file_path in hook input; allowing"
  exit 0
fi

case "$file" in
  .git|.git/*|*/.git|*/.git/*)
    deny "blocked: $file is under .git/ — never edit git internals directly; use git commands"
    ;;
esac

base="$(basename "$file")"
case "$base" in
  .env*)
    deny "blocked: $file matches .env* (likely secrets) — edit a .env.example instead, or ask the user to change it"
    ;;
  package-lock.json|pnpm-lock.yaml|*.lock)
    deny "blocked: $file is a lockfile — regenerate it with the package manager instead of editing"
    ;;
esac

exit 0
