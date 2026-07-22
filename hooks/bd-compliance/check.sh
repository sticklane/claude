#!/usr/bin/env bash
# bd-compliance: Stop hook that blocks "done" while bd issues the session
# claimed are still open (specs/beads-daily-skill/SPEC.md, "The compliance
# Stop hook"). The /work skill appends a claimed issue's id to
# .beads/session-claims (one id per line) before starting work on it, and
# removes that line when the issue is closed (.claude/skills/work/SKILL.md,
# steps 2 and 4) — this hook is the mechanical enforcement that a session
# cannot silently drop the tracker.
#
# Contract:
#   - .beads/session-claims absent or empty (no non-blank lines) -> exit 0.
#   - every id listed is closed in bd (checked per id via
#     `bd show <id> --json`, reading the `status` field) -> exit 0.
#   - any listed id is not confirmed closed -> exit 2, naming the open
#     ids, so the Stop hook blocks.
#   - bd itself is not installed on PATH -> exit 0 with a note. This hook
#     must never brick a repo that doesn't have bd — a missing bd binary
#     is a reason to skip the check, never a reason to block "done".
#
# Follows the same Stop-hook stdin contract as templates/stop-gate.sh:
# `.stop_hook_active` (loop protection), `.transcript_path` (sanctioned
# unattended-worker stop verdicts), `.cwd` (repo-root resolution).
set -u

warn() { printf 'bd-compliance: %s\n' "$1" >&2; }

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

# Sanctioned stop: an unattended worker's contractual mid-red stop (a final
# message beginning DEFERRED, BLOCKED, or INCOMPLETE) is let through rather
# than trapped — same convention as templates/stop-gate.sh.
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

claims="$root/.beads/session-claims"
if [ ! -f "$claims" ]; then
  exit 0
fi

# Collect non-blank claimed ids.
ids=()
while IFS= read -r line || [ -n "$line" ]; do
  line="$(printf '%s' "$line" | tr -d '[:space:]' 2>/dev/null || true)"
  [ -n "$line" ] && ids+=("$line")
done < "$claims"

if [ "${#ids[@]}" -eq 0 ]; then
  exit 0
fi

if ! command -v bd >/dev/null 2>&1; then
  warn "note: bd not installed on PATH; skipping bd-compliance check for: ${ids[*]}"
  exit 0
fi

open_ids=()
for id in "${ids[@]}"; do
  out="$(cd "$root" && bd show "$id" --json 2>/dev/null)"
  rc=$?
  status=""
  if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
    status="$(printf '%s' "$out" | jq -r '.[0].status // empty' 2>/dev/null || true)"
  fi
  if [ "$status" != "closed" ]; then
    open_ids+=("$id")
  fi
done

if [ "${#open_ids[@]}" -eq 0 ]; then
  exit 0
fi

{
  printf 'bd-compliance: claimed issue(s) still open — close them before ending the session: %s\n' \
    "${open_ids[*]}"
  printf 'Close with `bd close <id>` and remove the line from .beads/session-claims, or defer/unclaim per the /work skill, then try again.\n'
} >&2
exit 2
