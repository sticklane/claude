#!/usr/bin/env bash
# Unit tests for check.sh — the bd-compliance Stop hook.
# Builds a scratch git repo + bd store under mktemp -d, files a real issue
# via bd, claims it via the same .beads/session-claims contract /work
# writes, and drives check.sh with a synthetic Stop-hook stdin payload.
# Never touches this toolkit's own real .beads store.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/check.sh"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
    printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1))
    printf 'FAIL - %s\n' "$1"
  fi
}

# stop_input <cwd> — a synthetic Stop-hook stdin payload naming <cwd>.
stop_input() {
  jq -n --arg cwd "$1" '{stop_hook_active: false, transcript_path: "", cwd: $cwd}'
}

require_bd=1
if ! command -v bd >/dev/null 2>&1; then
  echo "bd-compliance test.sh: bd not found on PATH; cannot run scratch-repo tests" >&2
  require_bd=0
fi

if [ "$require_bd" -eq 1 ]; then
  tmp="$(mktemp -d)"
  ( cd "$tmp" && git init -q . )
  ( cd "$tmp" && BD_NON_INTERACTIVE=1 bd init -q . >/dev/null 2>&1 )

  # File a real issue and capture its id.
  id="$(cd "$tmp" && BD_NON_INTERACTIVE=1 bd create "bd-compliance test issue" --json 2>/dev/null \
    | jq -r '.id // empty')"
  if [ -z "$id" ]; then
    # Fallback for bd builds whose `create` doesn't support --json: parse
    # the id token out of the plain-text confirmation line.
    id="$(cd "$tmp" && BD_NON_INTERACTIVE=1 bd create "bd-compliance test issue 2" 2>&1 \
      | grep -oE '[a-zA-Z0-9_.-]+-[0-9a-z]+' | head -1)"
  fi

  # --- claimed + open: exit 2 naming the id --------------------------------
  mkdir -p "$tmp/.beads"
  printf '%s\n' "$id" > "$tmp/.beads/session-claims"
  out="$(stop_input "$tmp" | bash "$HOOK" 2>&1)"
  rc=$?
  check "open claim: exit 2" "$([ "$rc" -eq 2 ] && echo 0 || echo 1)"
  check "open claim: names the id" \
    "$(printf '%s' "$out" | grep -qF "$id" && echo 0 || echo 1)"

  # --- close the issue: exit 0 ---------------------------------------------
  ( cd "$tmp" && bd close "$id" --reason "test done" >/dev/null 2>&1 )
  out="$(stop_input "$tmp" | bash "$HOOK" 2>&1)"
  rc=$?
  check "closed claim: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"

  # --- empty session-claims file: exit 0 -----------------------------------
  : > "$tmp/.beads/session-claims"
  out="$(stop_input "$tmp" | bash "$HOOK" 2>&1)"
  rc=$?
  check "empty session-claims: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"

  rm -rf "$tmp"
else
  check "scratch-repo tests skipped (bd absent)" 1
fi

# --- no .beads dir at all: exit 0 (never brick a repo without bd) ---------
tmp2="$(mktemp -d)"
( cd "$tmp2" && git init -q . )
out="$(stop_input "$tmp2" | bash "$HOOK" 2>&1)"
rc=$?
check "no .beads dir: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp2"

# --- bd binary absent from PATH: tolerated, exit 0 ------------------------
tmp3="$(mktemp -d)"
( cd "$tmp3" && git init -q . )
mkdir -p "$tmp3/.beads"
echo "some-fake-id-1" > "$tmp3/.beads/session-claims"
restricted="$(mktemp -d)"
out="$(stop_input "$tmp3" | env PATH="$restricted:/usr/bin:/bin" bash "$HOOK" 2>&1)"
rc=$?
check "bd absent from PATH: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp3" "$restricted"

# --- stop_hook_active=true: loop protection, exit 0 no matter what --------
tmp4="$(mktemp -d)"
( cd "$tmp4" && git init -q . )
mkdir -p "$tmp4/.beads"
echo "some-fake-id-2" > "$tmp4/.beads/session-claims"
active_input="$(jq -n --arg cwd "$tmp4" '{stop_hook_active: true, transcript_path: "", cwd: $cwd}')"
out="$(printf '%s' "$active_input" | bash "$HOOK" 2>&1)"
rc=$?
check "stop_hook_active=true: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
rm -rf "$tmp4"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
if [ "$fail" -eq 0 ]; then
  echo "BD HOOK TEST OK"
  exit 0
fi
exit 1
