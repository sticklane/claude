#!/usr/bin/env bash
# Tests for changed-stack scoping in templates/check.sh.tmpl (agentic-cs8u).
#
# run_scoped_stage runs a single-language stage only when CHECK_SCOPE names a
# path that stage could read. CHECK_SCOPE is supplied by stop-gate.sh from
# `git status`; unset means "scope unknown" and MUST run everything, so a
# manual or CI invocation of check.sh keeps full coverage.
#
# Integration stages (a .ts change is what breaks the browser suite) stay on
# plain run_stage and are never scoped — that property is asserted here too.
set -u

TOOLKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMPL="$TOOLKIT_DIR/templates/check.sh.tmpl"

pass=0
fail=0
assert() { # assert <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1)); printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1)); printf 'FAIL - %s\n' "$1"
  fi
}
is() { [ "$1" = "$2" ] && echo 0 || echo 1; }
has() { printf '%s' "$1" | grep -q -- "$2" && echo 0 || echo 1; }
hasnt() { printf '%s' "$1" | grep -q -- "$2" && echo 1 || echo 0; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# render <stages> — writes a runnable check.sh from the template. Echoes path.
render() {
  local d="$TMP/repo.$RANDOM" ; mkdir -p "$d/scripts"
  printf '%s\n' "$1" > "$d/stages.txt"
  awk -v f="$d/stages.txt" \
    '{ if ($0 == "@STAGES@") { while ((getline l < f) > 0) print l } else print }' \
    "$TMPL" > "$d/scripts/check.sh"
  chmod 755 "$d/scripts/check.sh"
  printf '%s' "$d/scripts/check.sh"
}

STAGES='run_scoped_stage "*.py" "pytests" true
run_stage "e2e" true'

CHECK="$(render "$STAGES")"

# --- unset CHECK_SCOPE runs everything (manual / CI invocation) --------------
OUT="$(bash "$CHECK" 2>&1)"; RC=$?
assert "unset CHECK_SCOPE: exits 0" "$(is "$RC" 0)"
assert "unset CHECK_SCOPE: scoped stage runs" "$(has "$OUT" 'pytests ok')"
assert "unset CHECK_SCOPE: unscoped stage runs" "$(has "$OUT" 'e2e ok')"

# --- empty CHECK_SCOPE also runs everything (fail-safe) ---------------------
OUT="$(CHECK_SCOPE='' bash "$CHECK" 2>&1)"; RC=$?
assert "empty CHECK_SCOPE: exits 0" "$(is "$RC" 0)"
assert "empty CHECK_SCOPE: scoped stage still runs" "$(has "$OUT" 'pytests ok')"

# --- out-of-scope change skips the scoped stage only ------------------------
OUT="$(CHECK_SCOPE='README.md' bash "$CHECK" 2>&1)"; RC=$?
assert "out-of-scope: exits 0" "$(is "$RC" 0)"
assert "out-of-scope: scoped stage skipped" "$(hasnt "$OUT" 'pytests ok')"
assert "out-of-scope: skip is reported, not silent" "$(has "$OUT" 'pytests skipped')"
assert "out-of-scope: unscoped stage still runs" "$(has "$OUT" 'e2e ok')"

# --- in-scope change runs the scoped stage ----------------------------------
OUT="$(CHECK_SCOPE='src/app.py' bash "$CHECK" 2>&1)"
assert "in-scope nested path: scoped stage runs" "$(has "$OUT" 'pytests ok')"

OUT="$(CHECK_SCOPE='README.md
src/deep/mod.py
web/app.ts' bash "$CHECK" 2>&1)"
assert "in-scope among many: scoped stage runs" "$(has "$OUT" 'pytests ok')"

# --- multiple patterns per stage --------------------------------------------
MULTI="$(render 'run_scoped_stage "*.go go.mod" "gotests" true')"
OUT="$(CHECK_SCOPE='go.mod' bash "$MULTI" 2>&1)"
assert "second pattern matches: stage runs" "$(has "$OUT" 'gotests ok')"
OUT="$(CHECK_SCOPE='web/app.ts' bash "$MULTI" 2>&1)"
assert "no pattern matches: stage skipped" "$(has "$OUT" 'gotests skipped')"

# --- scoping never weakens a failure --------------------------------------
RED="$(render 'run_scoped_stage "*.py" "pytests" false')"
OUT="$(CHECK_SCOPE='src/app.py' bash "$RED" 2>&1)"; RC=$?
assert "in-scope failing stage fails the suite" "$(is "$RC" 1)"
OUT="$(bash "$RED" 2>&1)"; RC=$?
assert "unset scope: failing stage still fails the suite" "$(is "$RC" 1)"

# --- a path that merely contains the pattern text must not match ------------
OUT="$(CHECK_SCOPE='docs/python-notes.md' bash "$CHECK" 2>&1)"
assert "substring is not a match: scoped stage skipped" "$(has "$OUT" 'pytests skipped')"

printf '\n%s: %d passed, %d failed\n' "$(basename "$0")" "$pass" "$fail"
[ "$fail" -eq 0 ]
