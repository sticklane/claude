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
#   - a listed id that is `in_progress` in bd AND carries a fresh line in
#     .beads/session-inflight is work in flight, not abandoned work -> it
#     satisfies the check without being closed. A drain orchestrator ends a
#     turn every time it awaits a dispatched worker, and closing an issue
#     whose work has not returned would record a completion that did not
#     happen (agentic-85d).
#   - any other listed id -> exit 2, naming the open ids, so the Stop hook
#     blocks.
#   - bd itself is not installed on PATH -> exit 0 with a note. This hook
#     must never brick a repo that doesn't have bd — a missing bd binary
#     is a reason to skip the check, never a reason to block "done".
#
# .beads/session-inflight (runtime-only, gitignored like session-claims) holds
# one `<id> <dispatched-at-epoch-seconds>` line per issue with a worker in
# flight; the dispatcher writes it at dispatch and drops it when it collects
# the verdict. It is not a bypass switch: the exemption is per-id, expires
# after BD_COMPLIANCE_INFLIGHT_TTL seconds (default 3600) so a session that
# crashes mid-dispatch leaves no lasting immunity, and holds only while bd
# itself reports the id `in_progress` — a marker on an issue nobody claimed
# in bd exempts nothing.
#
# The block message below DELIBERATELY does not mention the marker: a session
# that abandoned claimed work is already `in_progress`, so telling it the file
# name would hand it a one-line self-exemption. Do not add it back.
#
# Follows the runtime-neutral Stop-hook contract in templates/stop-gate.sh.
set -u

warn() { printf 'bd-compliance: %s\n' "$1" >&2; }

runtime="${AGENTIC_HOOK_RUNTIME:-claude-code}"
case "$runtime" in
  claude|claude-code) runtime=claude-code ;;
  codex|antigravity) ;;
  *) warn "warning: unknown AGENTIC_HOOK_RUNTIME=$runtime; using Claude Code hook semantics"; runtime=claude-code ;;
esac

allow_stop() {
  case "$runtime" in
    codex) printf '{}\n' ;;
    antigravity) printf '{"decision":"allow"}\n' ;;
  esac
  exit 0
}

block_stop() { # block_stop <reason>
  case "$runtime" in
    claude-code) printf '%s\n' "$1" >&2; exit 2 ;;
    codex) jq -n --arg reason "$1" '{decision:"block", reason:$reason}'; exit 0 ;;
    antigravity) jq -n --arg reason "$1" '{decision:"continue", reason:$reason}'; exit 0 ;;
  esac
}

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; skipping check"
  allow_stop
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; skipping check"
  allow_stop
fi
if ! active="$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)"; then
  warn "warning: malformed hook JSON on stdin; skipping check"
  allow_stop
fi
if [ "$active" = "true" ]; then
  allow_stop
fi
if [ "$runtime" = antigravity ]; then
  fully_idle="$(printf '%s' "$input" | jq -r \
    'if has("fullyIdle") then .fullyIdle else true end' 2>/dev/null || true)"
  execution_num="$(printf '%s' "$input" | jq -r '.executionNum // 0' 2>/dev/null || true)"
  [ "$fully_idle" = "true" ] || allow_stop
  case "$execution_num" in ''|*[!0-9]*) execution_num=0 ;; esac
  [ "$execution_num" -le 1 ] || allow_stop
fi

# Sanctioned stop: an unattended worker's contractual mid-red stop (a final
# message beginning DEFERRED, BLOCKED, or INCOMPLETE) is let through rather
# than trapped — same convention as templates/stop-gate.sh.
last="$(printf '%s' "$input" | jq -r '.last_assistant_message // empty' 2>/dev/null || true)"
transcript="$(printf '%s' "$input" | jq -r '.transcript_path // .transcriptPath // empty' 2>/dev/null || true)"
if [ -n "$transcript" ] && [ -r "$transcript" ]; then
  transcript_last="$(tail -50 "$transcript" \
    | jq -rs '[.[] | select(.type == "assistant")] | last
              | .message.content[]? | select(.type == "text") | .text' \
    2>/dev/null || true)"
  [ -n "$transcript_last" ] && last="$transcript_last"
fi
if printf '%s' "$last" | head -1 | grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'; then
  allow_stop
fi

# Resolve the repo root: hook JSON cwd if present, else current directory,
# widened to the enclosing git toplevel when available.
hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // .workspacePaths[0] // empty' 2>/dev/null || true)"
if [ -n "$hook_cwd" ] && [ -d "$hook_cwd" ]; then
  cd "$hook_cwd" || { warn "warning: cannot cd to $hook_cwd; skipping check"; allow_stop; }
fi
root="$(git rev-parse --show-toplevel 2>/dev/null)" || root="$PWD"

claims="$root/.beads/session-claims"
if [ ! -f "$claims" ]; then
  allow_stop
fi

# Collect non-blank claimed ids.
ids=()
while IFS= read -r line || [ -n "$line" ]; do
  line="$(printf '%s' "$line" | tr -d '[:space:]' 2>/dev/null || true)"
  [ -n "$line" ] && ids+=("$line")
done < "$claims"

if [ "${#ids[@]}" -eq 0 ]; then
  allow_stop
fi

if ! command -v bd >/dev/null 2>&1; then
  warn "note: bd not installed on PATH; skipping bd-compliance check for: ${ids[*]}"
  allow_stop
fi

inflight="$root/.beads/session-inflight"
ttl="${BD_COMPLIANCE_INFLIGHT_TTL:-3600}"
case "$ttl" in
  '' | *[!0-9]*) ttl=3600 ;;
esac
now="$(date +%s 2>/dev/null || echo 0)"

has_live_dispatch() { # has_live_dispatch <id>
  [ -f "$inflight" ] || return 1
  local stamp age
  stamp="$(awk -v want="$1" '$1 == want { s = $2 } END { print s }' "$inflight" 2>/dev/null || true)"
  case "$stamp" in
    '' | *[!0-9]*) return 1 ;;
  esac
  age=$(( now - stamp ))
  [ "$age" -ge 0 ] && [ "$age" -lt "$ttl" ]
}

open_ids=()
for id in "${ids[@]}"; do
  out="$(cd "$root" && bd show "$id" --json 2>/dev/null)"
  rc=$?
  status=""
  if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
    status="$(printf '%s' "$out" | jq -r '.[0].status // empty' 2>/dev/null || true)"
  fi
  [ "$status" = "closed" ] && continue
  if [ "$status" = "in_progress" ] && has_live_dispatch "$id"; then
    continue
  fi
  open_ids+=("$id")
done

if [ "${#open_ids[@]}" -eq 0 ]; then
  allow_stop
fi

reason="$(printf 'bd-compliance: claimed issue(s) neither closed nor in flight: %s\nIf the work is done: `bd close <id>` and remove the line from .beads/session-claims. Otherwise defer or unclaim it per the /work skill.' "${open_ids[*]}")"
block_stop "$reason"
