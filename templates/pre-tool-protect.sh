#!/usr/bin/env bash
# Runtime-neutral PreToolUse hook (SPEC R12): deny native file-edit tools from
# touching .env*, lockfiles, or anything under .git/. Self-contained and
# installed verbatim into the active runtime's hook directory.
set -u

warn() { printf 'pre-tool-protect: %s\n' "$1" >&2; }

runtime="${AGENTIC_HOOK_RUNTIME:-claude-code}"
case "$runtime" in
  claude|claude-code) runtime=claude-code ;;
  codex|antigravity) ;;
  *) warn "warning: unknown AGENTIC_HOOK_RUNTIME=$runtime; using Claude Code hook semantics"; runtime=claude-code ;;
esac

allow_tool() {
  if [ "$runtime" = antigravity ]; then
    printf '{"decision":"allow"}\n'
  fi
  exit 0
}

deny() { # deny <reason>
  case "$runtime" in
    claude-code)
      printf 'pre-tool-protect: %s\n' "$1" >&2
      exit 2
      ;;
    codex)
      jq -n --arg reason "$1" \
        '{hookSpecificOutput:{hookEventName:"PreToolUse",
          permissionDecision:"deny",permissionDecisionReason:$reason}}'
      exit 0
      ;;
    antigravity)
      jq -n --arg reason "$1" '{decision:"deny",reason:$reason}'
      exit 0
      ;;
  esac
}

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; allowing"
  allow_tool
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; allowing"
  allow_tool
fi
if ! printf '%s' "$input" | jq -e . >/dev/null 2>&1; then
  warn "warning: malformed hook JSON on stdin; allowing"
  allow_tool
fi

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
      printf '%s' "$input" | jq -r '.toolCall.args.TargetFile // empty'
      ;;
  esac
}

files="$(extract_files 2>/dev/null || true)"
if [ -z "$files" ]; then
  warn "warning: no edited file in hook input; allowing"
  allow_tool
fi

while IFS= read -r file; do
  [ -n "$file" ] || continue
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
done <<EOF
$files
EOF

# Antigravity PostToolUse does not currently include toolCall. Record the
# allowed TargetFile for the paired formatter, scoped by conversation id.
if [ "$runtime" = antigravity ]; then
  conversation="$(printf '%s' "$input" | jq -r '.conversationId // empty')"
  case "$conversation" in
    ''|*[!A-Za-z0-9._-]*) ;;
    *)
      state="${TMPDIR:-/tmp}/agentic-gate-format-$conversation"
      first="$(printf '%s\n' "$files" | sed -n '1p')"
      [ -n "$first" ] && printf '%s\n' "$first" > "$state"
      ;;
  esac
fi

allow_tool
