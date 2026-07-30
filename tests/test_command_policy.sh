#!/usr/bin/env bash
# Fixture suite for bin/command-policy, the single D11 command policy
# (specs/drain-economy task 00). Every hostile case runs through the
# executing entry point and is proved harmless by observation: each fixture
# plants a command that would create a sentinel file, and the case asserts
# the sentinel never appeared and the fixture's file census is unchanged.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY="$ROOT/bin/command-policy"
RULE=".claude/rules/file-sourced-commands.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
SLOW_SLEEP=3771
REJECT_CODES=""
REJECT_CASES=0
OUT=""
STATUS=0

ok() {
  pass=$((pass + 1))
  printf 'ok   - %s\n' "$1"
}

nope() {
  fail=$((fail + 1))
  printf 'FAIL - %s\n' "$1"
}

file_census() {
  (cd "$1" && find . -type f -not -path './.git/*' | wc -l | tr -d ' ')
}

json_field() {
  printf '%s' "$1" | python3 -c '
import json
import sys

field = sys.argv[1]
lines = [line for line in sys.stdin.read().splitlines() if line.strip()]
for line in reversed(lines):
    try:
        parsed = json.loads(line)
    except ValueError:
        continue
    value = parsed.get(field)
    print("" if value is None else value)
    break
else:
    print("")
' "$2"
}

new_fixture() {
  local fixture="$TMP/$1"
  mkdir -p "$fixture/bin"
  printf '%s\n' '#!/usr/bin/env bash' 'printf marker >MARKER' \
    >"$fixture/bin/make-marker"
  printf '%s\n' '#!/usr/bin/env bash' 'exit 3' >"$fixture/bin/exit-three"
  printf '%s\n' '#!/usr/bin/env bash' "sleep $SLOW_SLEEP" 'touch SENTINEL' \
    >"$fixture/bin/slow"
  chmod 755 "$fixture/bin/"*
  printf '%s\n' '#!/usr/bin/env bash' 'touch SENTINEL' >"$fixture/bin/inert"
  chmod 644 "$fixture/bin/inert"
  printf '%s\n' '#!/usr/bin/env bash' 'touch SENTINEL' >"$fixture/outside-tool"
  chmod 755 "$fixture/outside-tool"
  git -C "$fixture" init -q
  git -C "$fixture" config core.hooksPath /dev/null
  printf '%s' "$fixture"
}

run_policy() {
  local fixture="$1"
  shift
  OUT="$(cd "$fixture" && "$POLICY" "$@" 2>&1)"
  STATUS=$?
}

expect_reject() {
  local desc="$1" fixture="$2" expected="$3"
  shift 3
  local before after verdict reason
  before="$(file_census "$fixture")"
  run_policy "$fixture" "$@"
  after="$(file_census "$fixture")"
  verdict="$(json_field "$OUT" verdict)"
  reason="$(json_field "$OUT" reason)"
  REJECT_CASES=$((REJECT_CASES + 1))
  REJECT_CODES="$REJECT_CODES$reason
"
  if [ "$verdict" = "reject" ]; then
    ok "$desc: verdict is reject"
  else
    nope "$desc: verdict is reject (got '$verdict')"
  fi
  if [ "$reason" = "$expected" ]; then
    ok "$desc: reason code is $expected"
  else
    nope "$desc: reason code is $expected (got '$reason')"
  fi
  if [ "$STATUS" -ne 0 ]; then
    ok "$desc: exits nonzero"
  else
    nope "$desc: exits nonzero (got 0)"
  fi
  if [ "$(json_field "$OUT" executed)" = "False" ]; then
    ok "$desc: reports the command was never executed"
  else
    nope "$desc: reports the command was never executed"
  fi
  if [ "$before" = "$after" ]; then
    ok "$desc: fixture file census unchanged"
  else
    nope "$desc: fixture file census unchanged ($before then $after)"
  fi
}

# --- accept: an allowlisted repo-root command runs and has its effect
accepted="$(new_fixture accepted)"
run_policy "$accepted" bin/make-marker
if [ "$STATUS" -eq 0 ]; then
  ok "allowlisted repo bin/ command exits 0"
else
  nope "allowlisted repo bin/ command exits 0 (got $STATUS)"
fi
if [ "$(json_field "$OUT" verdict)" = "accept" ]; then
  ok "allowlisted repo bin/ command is accepted"
else
  nope "allowlisted repo bin/ command is accepted"
fi
if [ -f "$accepted/MARKER" ]; then
  ok "accepted command ran with the repository root as its cwd"
else
  nope "accepted command ran with the repository root as its cwd"
fi

# --- accept: an allowlisted named tool outside the repo
named="$(new_fixture named-tool)"
run_policy "$named" /bin/echo hi
if [ "$STATUS" -eq 0 ]; then
  ok "allowlisted named tool /bin/echo exits 0"
else
  nope "allowlisted named tool /bin/echo exits 0 (got $STATUS)"
fi
case "$OUT" in
  *hi*) ok "allowlisted named tool produced its output" ;;
  *) nope "allowlisted named tool produced its output" ;;
esac

# --- accept: the child's exit code is the policy's exit code
passthrough="$(new_fixture exit-passthrough)"
run_policy "$passthrough" bin/exit-three
if [ "$STATUS" -eq 3 ]; then
  ok "accepted command's exit code passes through"
else
  nope "accepted command's exit code passes through (got $STATUS)"
fi

# --- accept decision without execution
checkonly="$(new_fixture check-only)"
run_policy "$checkonly" --check-only bin/make-marker
if [ "$STATUS" -eq 0 ] && [ "$(json_field "$OUT" verdict)" = "accept" ]; then
  ok "--check-only accepts without running"
else
  nope "--check-only accepts without running (status $STATUS)"
fi
if [ ! -e "$checkonly/MARKER" ]; then
  ok "--check-only left no trace of execution"
else
  nope "--check-only left no trace of execution"
fi

# --- reject cases, one distinct reason code each
expect_reject "argv-0 resolving nowhere" \
  "$(new_fixture unresolved)" unresolved-argv0 no-such-tool-xyzzy hi

expect_reject "argv-0 outside the allowlisted roots" \
  "$(new_fixture outside)" outside-allowlist ./outside-tool

expect_reject "shell metacharacter reaching argv" \
  "$(new_fixture metacharacter)" shell-metacharacter \
  --command '/bin/echo hi; touch SENTINEL'

expect_reject "ASCII control character in an argument" \
  "$(new_fixture control)" control-character \
  /bin/echo "$(printf 'hi\001there')"

expect_reject "unbalanced quote in the command string" \
  "$(new_fixture quote)" unbalanced-quote \
  --command '/bin/echo "unclosed'

many_fixture="$(new_fixture many-arguments)"
many_arguments=()
for _ in $(seq 1 200); do many_arguments+=(hi); done
expect_reject "argument count over the bound" \
  "$many_fixture" too-many-arguments /bin/echo "${many_arguments[@]}"

long_argument="$(python3 -c 'print("a" * 9000)')"
expect_reject "argument length over the bound" \
  "$(new_fixture long-argument)" argument-too-long /bin/echo "$long_argument"

expect_reject "allowlisted path that is not executable" \
  "$(new_fixture inert)" not-executable bin/inert

# --- timeout: bounded execution, killed before its effect lands
slow="$(new_fixture slow)"
slow_before="$(file_census "$slow")"
run_policy "$slow" --timeout 1 bin/slow
slow_after="$(file_census "$slow")"
slow_reason="$(json_field "$OUT" reason)"
REJECT_CASES=$((REJECT_CASES + 1))
REJECT_CODES="$REJECT_CODES$slow_reason
"
if [ "$slow_reason" = "timeout" ]; then
  ok "command over the timeout reports the timeout reason code"
else
  nope "command over the timeout reports the timeout reason code (got '$slow_reason')"
fi
if [ "$STATUS" -ne 0 ]; then
  ok "command over the timeout exits nonzero"
else
  nope "command over the timeout exits nonzero"
fi
if [ "$slow_before" = "$slow_after" ]; then
  ok "timed-out command left the fixture census unchanged"
else
  nope "timed-out command left the fixture census unchanged"
fi

# --- further hostile spellings reuse the metacharacter code
expect_metacharacter() {
  local desc="$1" fixture="$2"
  shift 2
  local before after
  before="$(file_census "$fixture")"
  run_policy "$fixture" "$@"
  after="$(file_census "$fixture")"
  if [ "$(json_field "$OUT" reason)" = "shell-metacharacter" ] &&
    [ "$before" = "$after" ]; then
    ok "$desc"
  else
    nope "$desc"
  fi
}

expect_metacharacter "command substitution is refused, unexecuted" \
  "$(new_fixture substitution)" --command '/bin/echo $(touch SENTINEL)'
expect_metacharacter "backtick substitution is refused, unexecuted" \
  "$(new_fixture backtick)" --command '/bin/echo `touch SENTINEL`'
expect_metacharacter "pipeline is refused, unexecuted" \
  "$(new_fixture pipeline)" --command '/bin/echo hi | touch SENTINEL'

# --- every reject case carries its own reason code
distinct="$(printf '%s' "$REJECT_CODES" | sort -u | wc -l | tr -d ' ')"
if [ "$distinct" = "$REJECT_CASES" ]; then
  ok "each reject case returned a distinct reason code ($distinct of $REJECT_CASES)"
else
  nope "each reject case returned a distinct reason code ($distinct of $REJECT_CASES)"
fi

# --- no hostile fixture ever created its sentinel
planted="$(find "$TMP" -name SENTINEL -print -quit)"
if [ -z "$planted" ]; then
  ok "no hostile fixture created its sentinel file"
else
  nope "no hostile fixture created its sentinel file"
fi

# --- the rule both consumers cite exists and names the policy
grep -q 'command-policy' "$ROOT/.claude/rules/file-sourced-commands.md" || nope "$RULE names bin/command-policy"
if grep -q 'command-policy' "$ROOT/.claude/rules/file-sourced-commands.md"; then
  ok "$RULE names bin/command-policy"
fi

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
