#!/usr/bin/env bash
# Self-test for the runner's cost ledger and budget ceiling.
#
# Builds throwaway scenario trees under mktemp -d and drives run.sh with a
# stub runner that prints a chosen total_cost_usd, so the accounting is
# exercised without a paid session. Asserts: every scenario appends one
# priced ledger row, a run whose cumulative cost reaches EVAL_BUDGET_USD
# stops rather than launching the next scenario, and a transcript carrying no
# cost is recorded as unknown rather than as zero. Same self-test pattern as
# evals/runner-selftest.sh.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL=distill

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# A stub headless runner emitting a Claude Code-shaped result line, so the
# runner's cost extraction reads the same field it reads in a live run.
priced_stub() { # <cost-usd>
  local path="$TMP/stub-$1.sh"
  cat > "$path" <<STUB
#!/usr/bin/env bash
set -eu
printf '%s\n' '{"type":"result","subtype":"success","total_cost_usd":$1}'
printf 'ran\n' > stub-output.txt
STUB
  chmod +x "$path"
  printf '%s' "$path"
}

silent_stub() {
  local path="$TMP/stub-silent.sh"
  cat > "$path" <<'STUB'
#!/usr/bin/env bash
set -eu
printf '%s\n' 'no cost field here'
printf 'ran\n' > stub-output.txt
STUB
  chmod +x "$path"
  printf '%s' "$path"
}

make_scenario() { # <evals-root> <NN-name>
  local d="$1/$SKILL/$2"
  mkdir -p "$d"
  printf 'true\n' > "$d/setup.sh"
  printf 'do the thing\n' > "$d/prompt.txt"
  printf 'test -s stub-output.txt\n' > "$d/assert.sh"
}

fail() { echo "SELFTEST FAIL: $1" >&2; [ -n "${2:-}" ] && printf '%s\n' "$2" >&2; exit 1; }

# --- every scenario appends one priced ledger row ---------------------------
make_scenario "$TMP/ledger" 01-a
make_scenario "$TMP/ledger" 02-b
ledger="$TMP/ledger.jsonl"
EVALS_ROOT="$TMP/ledger" EVAL_LEDGER="$ledger" EVAL_BUDGET_USD=10 \
  RUNNER_CMD="$(priced_stub 0.25)" "$ROOT/evals/run.sh" "$SKILL" >/dev/null ||
  fail "priced run exited non-zero"
rows="$(wc -l < "$ledger" | tr -d ' ')"
[ "$rows" = 2 ] || fail "ledger rows = $rows, want 2" "$(cat "$ledger")"
grep -q '"cost_usd":0.25' "$ledger" || fail "ledger row is missing the scenario cost" "$(cat "$ledger")"
grep -q "\"skill\":\"$SKILL\"" "$ledger" || fail "ledger row is missing the skill" "$(cat "$ledger")"

# --- the budget stops the run before the next scenario launches -------------
make_scenario "$TMP/budget" 01-a
make_scenario "$TMP/budget" 02-b
make_scenario "$TMP/budget" 03-c
rc=0
out="$(EVALS_ROOT="$TMP/budget" EVAL_LEDGER="$TMP/budget.jsonl" EVAL_BUDGET_USD=0.60 \
  RUNNER_CMD="$(priced_stub 0.25)" "$ROOT/evals/run.sh" "$SKILL")" || rc=$?
[ "$rc" -ne 0 ] || fail "over-budget run exited 0, want non-zero" "$out"
case "$out" in
  *"budget"*) : ;;
  *) fail "over-budget run never named the budget" "$out" ;;
esac
launched="$(wc -l < "$TMP/budget.jsonl" | tr -d ' ')"
[ "$launched" -lt 3 ] || fail "budget did not stop the run: $launched scenarios launched" "$out"

# --- a transcript with no cost field records unknown, never zero ------------
make_scenario "$TMP/unknown" 01-a
EVALS_ROOT="$TMP/unknown" EVAL_LEDGER="$TMP/unknown.jsonl" EVAL_BUDGET_USD=10 \
  RUNNER_CMD="$(silent_stub)" "$ROOT/evals/run.sh" "$SKILL" >/dev/null ||
  fail "unpriced run exited non-zero"
grep -q '"cost_usd":null' "$TMP/unknown.jsonl" ||
  fail "an unpriced run must record null, not 0" "$(cat "$TMP/unknown.jsonl")"

# --- a scenario's max-turns.txt reaches the runner command ------------------
make_scenario "$TMP/turns" 01-a
printf '3\n' > "$TMP/turns/$SKILL/01-a/max-turns.txt"
out="$(EVALS_ROOT="$TMP/turns" EVAL_DRY_RUN=1 EVAL_RUNTIME=claude-code "$ROOT/evals/run.sh" "$SKILL")" ||
  fail "dry run exited non-zero" "$out"
case "$out" in
  *"--max-turns 3"*) : ;;
  *) fail "max-turns.txt did not reach the runner command" "$out" ;;
esac

out="$(EVALS_ROOT="$TMP/turns" EVAL_DRY_RUN=1 MAX_TURNS=25 EVAL_RUNTIME=claude-code "$ROOT/evals/run.sh" "$SKILL")" ||
  fail "dry run with MAX_TURNS exited non-zero" "$out"
case "$out" in
  *"--max-turns 25"*) : ;;
  *) fail "an explicit MAX_TURNS must override max-turns.txt" "$out" ;;
esac

echo "budget selftest: OK (ledger rows, budget ceiling, unpriced run, turn cap)"
