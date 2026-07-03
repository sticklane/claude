#!/usr/bin/env bash
# Claude Code PostToolUse hook (SPEC R11): auto-format the single file just
# touched by Edit/Write. Self-contained; installed verbatim into
# .claude/hooks/. Always fail-open (exit 0): a missing formatter, unmatched
# stack, or formatter failure never blocks the edit.
set -u

warn() { printf 'post-tool-format: %s\n' "$1" >&2; }

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; nothing to format"
  exit 0
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; skipping format"
  exit 0
fi
if ! file="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"; then
  warn "warning: malformed hook JSON on stdin; skipping format"
  exit 0
fi
if [ -z "$file" ]; then
  warn "warning: no file_path in hook input; skipping format"
  exit 0
fi
if [ ! -f "$file" ]; then
  warn "warning: $file does not exist; skipping format"
  exit 0
fi

# Resolve the repo root (for repo-local node_modules/.bin lookups):
# hook JSON cwd if present, else current directory, widened to git toplevel.
hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"
if [ -n "$hook_cwd" ] && [ -d "$hook_cwd" ]; then
  cd "$hook_cwd" 2>/dev/null || true
fi
root="$(git rev-parse --show-toplevel 2>/dev/null)" || root="$PWD"

# Formatter provisioning rules (see SPEC "Tool provisioning"): plain ruff if
# on PATH else uvx ruff; repo-local prettier else `npx --no-install prettier`
# (never bare npx); gofmt for Go.
case "$file" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      fmt=(ruff format)
    elif command -v uvx >/dev/null 2>&1; then
      fmt=(uvx ruff format)
    else
      warn "warning: no ruff or uvx on PATH; skipping format of $file"
      exit 0
    fi
    ;;
  *.go)
    if command -v gofmt >/dev/null 2>&1; then
      fmt=(gofmt -w)
    else
      warn "warning: gofmt not on PATH; skipping format of $file"
      exit 0
    fi
    ;;
  *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.json|*.css|*.scss|*.html|*.md|*.yaml|*.yml)
    if [ -x "$root/node_modules/.bin/prettier" ]; then
      fmt=("$root/node_modules/.bin/prettier" --write)
    elif command -v npx >/dev/null 2>&1; then
      fmt=(npx --no-install prettier --write)
    else
      warn "warning: no prettier or npx on PATH; skipping format of $file"
      exit 0
    fi
    ;;
  *)
    warn "warning: no formatter matches $file; skipping format"
    exit 0
    ;;
esac

if ! "${fmt[@]}" "$file" >/dev/null 2>&1; then
  warn "warning: formatter failed for $file (non-blocking)"
fi
exit 0
