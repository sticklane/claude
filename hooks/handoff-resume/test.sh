#!/usr/bin/env bash
# Unit tests for resume-check.sh — the handoff-resume SessionStart hook.
# Builds a scratch git repo + real bd store under mktemp -d and files real
# handoff-labeled issues there, the same way hooks/bd-compliance/test.sh
# does. Never touches this toolkit's own .beads store.
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

new_issue() { # new_issue <repo> <title> [label] — prints the created id
  local repo="$1" title="$2" label="${3:-}"
  if [ -n "$label" ]; then
    BD_NON_INTERACTIVE=1 bd -C "$repo" create "$title" --labels "$label" \
      --type=task --json 2>/dev/null | jq -r '.id // empty'
  else
    BD_NON_INTERACTIVE=1 bd -C "$repo" create "$title" --type=task --json \
      2>/dev/null | jq -r '.id // empty'
  fi
}

if command -v bd >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  repo="$(mktemp -d)"
  ( cd "$repo" && git init -q . )
  ( cd "$repo" && BD_NON_INTERACTIVE=1 bd init -q . >/dev/null 2>&1 )

  # --- open issues but none labeled handoff: silent no-op ------------------
  new_issue "$repo" "unrelated open work" >/dev/null
  out="$(CLAUDE_PROJECT_DIR="$repo" bash "$HOOK" </dev/null)"
  rc=$?
  check "no-handoff-label: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
  check "no-handoff-label: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"

  # --- one open handoff issue: names it, instructs resume ------------------
  first="$(new_issue "$repo" "Session handoff: drain hub" handoff)"
  out="$(CLAUDE_PROJECT_DIR="$repo" bash "$HOOK" </dev/null)"
  rc=$?
  check "one-handoff: mentions the issue id" \
    "$(printf '%s' "$out" | grep -qF "$first" && echo 0 || echo 1)"
  check "one-handoff: mentions the issue title" \
    "$(printf '%s' "$out" | grep -qF "Session handoff: drain hub" && echo 0 || echo 1)"
  check "one-handoff: instructs to continue" \
    "$(printf '%s' "$out" | grep -qi "continue" && echo 0 || echo 1)"
  check "one-handoff: names the resume-handoff skill" \
    "$(printf '%s' "$out" | grep -qi "resume-handoff" && echo 0 || echo 1)"
  check "one-handoff: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"

  # --- two open handoff issues: lists both, asks the session to pick -------
  second="$(new_issue "$repo" "Session handoff: eval sandbox" handoff)"
  out="$(CLAUDE_PROJECT_DIR="$repo" bash "$HOOK" </dev/null)"
  rc=$?
  check "two-handoffs: mentions both issue ids" \
    "$(printf '%s' "$out" | grep -qF "$first" \
       && printf '%s' "$out" | grep -qF "$second" \
       && echo 0 || echo 1)"
  check "two-handoffs: names the resume-handoff skill" \
    "$(printf '%s' "$out" | grep -qi "resume-handoff" && echo 0 || echo 1)"
  check "two-handoffs: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"

  # --- every handoff issue closed: silent again ----------------------------
  BD_NON_INTERACTIVE=1 bd -C "$repo" close "$first" --reason "resumed" >/dev/null 2>&1
  BD_NON_INTERACTIVE=1 bd -C "$repo" close "$second" --reason "resumed" >/dev/null 2>&1
  out="$(CLAUDE_PROJECT_DIR="$repo" bash "$HOOK" </dev/null)"
  rc=$?
  check "closed-handoffs: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
  check "closed-handoffs: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"

  # --- bd absent from PATH while a handoff issue is open: silent no-op -----
  live="$(new_issue "$repo" "Session handoff: path check" handoff)"
  check "path-check fixture: issue created" \
    "$([ -n "$live" ] && echo 0 || echo 1)"
  restricted="$(mktemp -d)"
  out="$(CLAUDE_PROJECT_DIR="$repo" env PATH="$restricted:/usr/bin:/bin" \
    bash "$HOOK" </dev/null 2>/dev/null)"
  rc=$?
  check "bd-absent: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
  check "bd-absent: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
  rm -rf "$restricted"

  rm -rf "$repo"
else
  check "scratch-repo tests skipped (bd or jq absent)" 1
fi

# --- bd present but the project has no .beads store: silent no-op ---------
bare="$(mktemp -d)"
( cd "$bare" && git init -q . )
out="$(CLAUDE_PROJECT_DIR="$bare" bash "$HOOK" </dev/null 2>/dev/null)"
rc=$?
check "no-beads-store: empty stdout" "$([ -z "$out" ] && echo 0 || echo 1)"
check "no-beads-store: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$bare"

echo "----"
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
