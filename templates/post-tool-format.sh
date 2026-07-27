#!/usr/bin/env bash
# Runtime-neutral PostToolUse hook (SPEC R11): auto-format files just touched
# by a native file-edit tool. Self-contained; installed verbatim into the
# active runtime's hook directory. Always fail-open: a missing formatter,
# unmatched stack, or formatter failure never blocks the edit.
set -u

warn() { printf 'post-tool-format: %s\n' "$1" >&2; }

runtime="${AGENTIC_HOOK_RUNTIME:-claude-code}"
case "$runtime" in
  claude|claude-code) runtime=claude-code ;;
  codex|antigravity) ;;
  *) warn "warning: unknown AGENTIC_HOOK_RUNTIME=$runtime; using Claude Code hook semantics"; runtime=claude-code ;;
esac

finish() {
  case "$runtime" in codex|antigravity) printf '{}\n' ;; esac
  exit 0
}

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; nothing to format"
  finish
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; skipping format"
  finish
fi
if ! printf '%s' "$input" | jq -e . >/dev/null 2>&1; then
  warn "warning: malformed hook JSON on stdin; skipping format"
  finish
fi

# Resolve the repo root (for repo-local node_modules/.bin lookups):
# hook JSON cwd if present, else current directory, widened to git toplevel.
hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // .workspacePaths[0] // empty' 2>/dev/null || true)"
if [ -n "$hook_cwd" ] && [ -d "$hook_cwd" ]; then
  cd "$hook_cwd" 2>/dev/null || true
fi
root="$(git rev-parse --show-toplevel 2>/dev/null)" || root="$PWD"

extract_files() {
  case "$runtime" in
    claude-code)
      printf '%s' "$input" | jq -r '.tool_input.file_path // empty'
      ;;
    codex)
      printf '%s' "$input" | jq -r '.tool_input.command // empty' | awk '
        /^\*\*\* (Add|Update|Delete) File: / {
          sub(/^\*\*\* (Add|Update|Delete) File: /, ""); print
        }
        /^\*\*\* Move to: / {
          sub(/^\*\*\* Move to: /, ""); print
        }'
      ;;
    antigravity)
      file="$(printf '%s' "$input" | jq -r '.toolCall.args.TargetFile // empty')"
      if [ -n "$file" ]; then
        printf '%s\n' "$file"
        return
      fi
      # Current Antigravity PostToolUse input omits toolCall. The paired
      # PreToolUse protection hook records the target for this conversation.
      conversation="$(printf '%s' "$input" | jq -r '.conversationId // empty')"
      case "$conversation" in ''|*[!A-Za-z0-9._-]*) return ;; esac
      state="${TMPDIR:-/tmp}/agentic-gate-format-$conversation"
      if [ -r "$state" ]; then
        sed -n '1p' "$state"
        rm -f "$state"
      fi
      ;;
  esac
}

files="$(extract_files 2>/dev/null || true)"
if [ -z "$files" ]; then
  warn "warning: no edited file in hook input; skipping format"
  finish
fi

format_file() { # format_file <path>
  file="$1"
  case "$file" in
    /*) ;;
    *) file="$root/$file" ;;
  esac
  if [ ! -f "$file" ]; then
    warn "warning: $file does not exist; skipping format"
    return
  fi

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
        return
      fi
      ;;
    *.go)
      if command -v gofmt >/dev/null 2>&1; then
        fmt=(gofmt -w)
      else
        warn "warning: gofmt not on PATH; skipping format of $file"
        return
      fi
      ;;
    *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.json|*.css|*.scss|*.html|*.md|*.yaml|*.yml)
      if [ -x "$root/node_modules/.bin/prettier" ]; then
        fmt=("$root/node_modules/.bin/prettier" --write)
      elif command -v npx >/dev/null 2>&1; then
        fmt=(npx --no-install prettier --write)
      else
        warn "warning: no prettier or npx on PATH; skipping format of $file"
        return
      fi
      ;;
    *)
      warn "warning: no formatter matches $file; skipping format"
      return
      ;;
  esac

  if ! "${fmt[@]}" "$file" >/dev/null 2>&1; then
    warn "warning: formatter failed for $file (non-blocking)"
  fi
}

while IFS= read -r file; do
  [ -n "$file" ] && format_file "$file"
done <<EOF
$files
EOF
finish
