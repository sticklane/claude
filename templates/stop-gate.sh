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

# Sanctioned stop: unattended workers are contractually required to stop
# mid-red with a final message beginning with a verdict line (DEFERRED,
# BLOCKED, or the verifier's INCOMPLETE) — let such a stop through instead
# of trapping the worker in a block loop.
transcript="$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null || true)"
if [ -n "$transcript" ] && [ -r "$transcript" ]; then
  last="$(tail -50 "$transcript" \
    | jq -rs '[.[] | select(.type == "assistant")] | last
              | .message.content[]? | select(.type == "text") | .text' \
    2>/dev/null || true)"
  if printf '%s' "$last" | head -1 | grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'; then
    exit 0
  fi
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

# docs-only diff scoping: when every file changed since the last commit
# matches CLAUDE.md's paths-ignore globs (**.md, docs/**, specs/**,
# .claude/**), skip the full check — the same convention CLAUDE.md states for
# push-triggered CI, applied to the local Stop-hook gate. A change that
# touches any non-docs path still runs scripts/check.sh in full; this is a
# scoping optimization, never a blanket skip. No change since HEAD (a clean
# tree) is NOT docs-only and runs the check.
docs_only_diff() { # docs_only_diff <repo-root>
  local changed line path
  changed="$(git -C "$1" status --porcelain --untracked-files=all 2>/dev/null)" \
    || return 1
  [ -n "$changed" ] || return 1
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    path="${line:3}"                                # strip "XY " status prefix
    case "$path" in *" -> "*) path="${path##* -> }" ;; esac  # rename: destination
    path="${path#\"}"; path="${path%\"}"            # unquote paths with specials
    case "$path" in
      *.md|docs/*|specs/*|.claude/*) : ;;           # docs path: keep scanning
      *) return 1 ;;                                 # non-docs change: run check
    esac
  done <<EOF
$changed
EOF
  return 0
}

if docs_only_diff "$root"; then
  warn "docs-only diff since last commit; skipping check"
  exit 0
fi

output="$(cd "$root" && bash "$check" 2>&1)"
status=$?
if [ "$status" -ne 0 ]; then
  printf '%s\n' "$output" >&2
  exit 2
fi
exit 0
