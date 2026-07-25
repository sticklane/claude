#!/usr/bin/env bash
# Tests for scripts/check.sh — the canonical repo suite runner.
#
# check.sh resolves its root as "$(dirname "$0")/..", so copying it into a
# fixture tree at <fix>/scripts/check.sh makes it operate on <fix>/tests —
# the real script under test, driven against synthetic tests.
set -u

TOOLKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK="$TOOLKIT_DIR/scripts/check.sh"

pass=0
fail=0
assert() { # assert <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1)); printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1)); printf 'FAIL - %s\n' "$1"
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# new_fixture <name> — a fixture repo with check.sh installed. Echoes its path.
new_fixture() {
  local d="$TMP/$1"
  mkdir -p "$d/scripts" "$d/tests"
  cp "$CHECK" "$d/scripts/check.sh"
  chmod 755 "$d/scripts/check.sh"
  printf '%s' "$d"
}

# run_check <fixture-dir> [env...] — sets OUT, RC, SECS.
run_check() {
  local d="$1"; shift
  local start end
  start="$(date +%s)"
  OUT="$(env "$@" bash "$d/scripts/check.sh" 2>&1)"
  RC=$?
  end="$(date +%s)"
  SECS=$((end - start))
}

# --- all-green suite exits 0 -------------------------------------------------
FIX="$(new_fixture green)"
printf '#!/usr/bin/env bash\nexit 0\n' > "$FIX/tests/test_a.sh"
printf '#!/usr/bin/env bash\nexit 0\n' > "$FIX/tests/test_b.sh"
run_check "$FIX"
assert "green suite exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"
assert "green suite reports green" \
  "$(printf '%s' "$OUT" | grep -q 'check.sh: green' && echo 0 || echo 1)"

# --- a failing test fails the suite and its output is relayed ----------------
FIX="$(new_fixture red)"
printf '#!/usr/bin/env bash\nexit 0\n' > "$FIX/tests/test_a.sh"
printf '#!/usr/bin/env bash\necho DISTINCTIVE_FAILURE_MARKER\nexit 1\n' > "$FIX/tests/test_b.sh"
run_check "$FIX"
assert "failing test exits 1" "$([ "$RC" -eq 1 ] && echo 0 || echo 1)"
assert "failing test's output is relayed" \
  "$(printf '%s' "$OUT" | grep -q 'DISTINCTIVE_FAILURE_MARKER' && echo 0 || echo 1)"
assert "failing test is named in the report" \
  "$(printf '%s' "$OUT" | grep -q 'test_b.sh' && echo 0 || echo 1)"

# --- a passing test's chatter is NOT relayed (only failures print) -----------
FIX="$(new_fixture quiet)"
printf '#!/usr/bin/env bash\necho NOISY_PASSING_CHATTER\nexit 0\n' > "$FIX/tests/test_a.sh"
run_check "$FIX"
assert "passing test's stdout is not relayed" \
  "$(printf '%s' "$OUT" | grep -q 'NOISY_PASSING_CHATTER' && echo 1 || echo 0)"

# --- quarantined failing test does not fail the suite ------------------------
FIX="$(new_fixture quarantined)"
printf '#!/usr/bin/env bash\nexit 1\n' > "$FIX/tests/test_eval_coverage_lint.sh"
printf '#!/usr/bin/env bash\nexit 0\n' > "$FIX/tests/test_a.sh"
run_check "$FIX"
assert "quarantined failure does not fail the suite" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"
assert "quarantined test is still reported visibly" \
  "$(printf '%s' "$OUT" | grep -q 'quarantined' && echo 0 || echo 1)"

# --- tests run in PARALLEL: wall clock well under the sequential sum ---------
# Four tests sleeping 3s each: sequential is >=12s, parallel is ~3s.
FIX="$(new_fixture parallel)"
for n in a b c d; do
  printf '#!/usr/bin/env bash\nsleep 3\nexit 0\n' > "$FIX/tests/test_$n.sh"
done
run_check "$FIX"
assert "parallel suite still exits 0" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"
assert "4x3s tests complete in under 8s (parallel, not 12s sequential)" \
  "$([ "$SECS" -lt 8 ] && echo 0 || echo 1)"

# --- a test whose recorded exit status is lost must NOT read as success ------
# A truncated rc write (a full disk mid-run) once printed FAIL and still
# exited green — the worst failure mode a gate has.
FIX="$(new_fixture lostrc)"
printf '#!/usr/bin/env bash\nexit 1\n' > "$FIX/tests/test_a.sh"
CORRUPT="$FIX/scripts/check.sh"
# Blank every rc file just before collection, simulating the truncated write.
awk '{ print }
     /^# --- collect/ { print "for f in \"$workdir\"/*.rc; do [ -e \"$f\" ] && : > \"$f\"; done" }' \
  "$CORRUPT" > "$CORRUPT.tmp" && mv "$CORRUPT.tmp" "$CORRUPT"
chmod 755 "$CORRUPT"
run_check "$FIX"
assert "an unreadable exit status fails the suite rather than reading green" \
  "$([ "$RC" -ne 0 ] && echo 0 || echo 1)"

# --- a hanging test is killed by the per-test timeout, not left to stall -----
# Skipped without GNU timeout(1), which check.sh tolerates being absent.
if command -v timeout >/dev/null 2>&1 || command -v gtimeout >/dev/null 2>&1; then
  FIX="$(new_fixture hang)"
  printf '#!/usr/bin/env bash\nsleep 30\n' > "$FIX/tests/test_hang.sh"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$FIX/tests/test_a.sh"
  run_check "$FIX" CHECK_TEST_TIMEOUT=3
  assert "hanging test is killed within the timeout (suite under 20s)" \
    "$([ "$SECS" -lt 20 ] && echo 0 || echo 1)"
  assert "hanging test fails the suite rather than passing silently" \
    "$([ "$RC" -eq 1 ] && echo 0 || echo 1)"
  assert "timed-out test is reported as such" \
    "$(printf '%s' "$OUT" | grep -qi 'timeout' && echo 0 || echo 1)"
else
  printf 'skip - timeout(1) absent; per-test timeout assertions not run\n'
fi

printf '\npassed: %d, failed: %d\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
