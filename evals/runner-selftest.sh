#!/usr/bin/env bash
# Self-test for the runner's RUNNER_CMD / EVALS_ROOT overrides.
#
# Builds throwaway scenario trees under mktemp -d (never discoverable by
# a plain ./evals/run.sh) naming a real toolkit skill so provisioning
# succeeds, then drives run.sh with a non-Claude command — the shipped
# stub by default, or whatever RUNNER_CMD is set to — and asserts both
# plumbing paths: a passing assert yields the PASS line with exit 0, a
# deliberately failing assert yields the FAIL line with exit 1.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL=handoff
RUNNER_CMD="${RUNNER_CMD:-$ROOT/evals/stub-cli.sh}"

TMP="$(mktemp -d)"
kept_fixture=""
trap 'rm -rf "$TMP" "$kept_fixture"' EXIT

make_scenario() { # <tree> <name> <assert-body>
  local dir="$1/$SKILL/$2"
  mkdir -p "$dir"
  printf '%s\n' "exit 0" > "$dir/setup.sh"
  printf '%s\n' "selftest prompt: write the artifact" > "$dir/prompt.txt"
  printf '%s\n' "$3" > "$dir/assert.sh"
}

# PASS path: the stub writes stub-output.txt; the assert finds it.
make_scenario "$TMP/pass" 01-pass 'grep -q "selftest prompt" stub-output.txt'
out="$(EVALS_ROOT="$TMP/pass" RUNNER_CMD="$RUNNER_CMD" "$ROOT/evals/run.sh" "$SKILL")" || {
  echo "SELFTEST FAIL: expected exit 0 on the PASS path; output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
}
printf '%s\n' "$out" | grep -q "^PASS  $SKILL/01-pass" || {
  echo "SELFTEST FAIL: PASS line missing; output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
}

# FAIL path: a deliberately failing assert must produce the FAIL line
# and a non-zero runner exit. run.sh keeps failed fixtures; reclaim it.
make_scenario "$TMP/fail" 01-fail 'exit 1'
rc=0
out="$(EVALS_ROOT="$TMP/fail" RUNNER_CMD="$RUNNER_CMD" "$ROOT/evals/run.sh" "$SKILL")" || rc=$?
kept_fixture="$(printf '%s\n' "$out" | sed -n 's/.*fixture kept: //p')"
[ "$rc" -eq 1 ] || {
  echo "SELFTEST FAIL: expected exit 1 on the FAIL path, got $rc; output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
}
printf '%s\n' "$out" | grep -q "^FAIL  $SKILL/01-fail" || {
  echo "SELFTEST FAIL: FAIL line missing; output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
}

echo "runner selftest: OK (PASS and FAIL plumbing verified with $RUNNER_CMD)"
