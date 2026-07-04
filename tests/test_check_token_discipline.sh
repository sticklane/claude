#!/usr/bin/env bash
# Tests for bin/check-token-discipline (SPEC R6). The tests ARE the contract:
# fixtures encode drain's real retry paragraph (must PASS the loop check
# unmodified), the four prose lines the check must NOT flag, the two wrapped
# dispatches that must be SEEN, drain's max-generations paragraph (a named
# generation cap counts as a bound), plus positive and negative controls.
# Runs against throwaway fixture files in a temp dir via the CHECK_TD_FILES
# env override, so it never touches the real tree.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHECK="$TOOLKIT_DIR/bin/check-token-discipline"

pass=0
fail=0

# run_check <fixture-file> — sets RC_OUT / RC_EXIT for the given single file
run_check() {
  RC_OUT="$(CHECK_TD_FILES="$1" "$CHECK" 2>&1)"
  RC_EXIT=$?
}

# assert_marker <desc> <present|absent> <marker> — the check-marker line
# ([dispatch]/[loop]/[budget]) is present or absent in RC_OUT.
assert_marker() {
  local desc="$1" mode="$2" marker="$3"
  if printf '%s' "$RC_OUT" | grep -qF "$marker"; then
    if [ "$mode" = present ]; then pass=$((pass+1)); else
      fail=$((fail+1)); echo "FAIL: $desc (marker '$marker' present, expected absent)" >&2; fi
  else
    if [ "$mode" = absent ]; then pass=$((pass+1)); else
      fail=$((fail+1)); echo "FAIL: $desc (marker '$marker' absent, expected present)" >&2; fi
  fi
}

assert() { # assert <desc> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then pass=$((pass+1)); else
    fail=$((fail+1)); echo "FAIL: $desc" >&2; fi
}

assert_eq() { # assert_eq <desc> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then pass=$((pass+1)); else
    fail=$((fail+1)); echo "FAIL: $desc (expected '$expected', got '$actual')" >&2; fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ---------------------------------------------------------------------------
# 0. The checker exists, is executable, and is valid bash.
# ---------------------------------------------------------------------------
assert "bin/check-token-discipline exists and is executable" test -x "$CHECK"
assert "bin/check-token-discipline is valid bash (bash -n)" bash -n "$CHECK"

# ---------------------------------------------------------------------------
# LOOP CHECK — drain's actual retry paragraph must PASS unmodified.
# (verbatim from .claude/skills/drain/SKILL.md; "relaunch once" states the
# bound, so the loop check must not flag it.)
# ---------------------------------------------------------------------------
F="$TMP/drain_retry.md"
cat > "$F" <<'EOF'
  If the merge or gates fail: run `git merge --abort` first (a failed
  merge leaves the checkout wedged in a conflicted state), then slot
  machine — discard the branch, relaunch once with the failure evidence
  in the prompt. A second failure routes
  into one tournament (at most one per task per drain run; procedure in
  reference.md "Tournament") instead of straight to `Status: failed`.
EOF
run_check "$F"
assert_marker "drain retry paragraph passes the loop check unmodified" absent "[loop]"

# ---------------------------------------------------------------------------
# LOOP CHECK — drain's max-generations paragraph must PASS. A named
# generation cap ("max-generations cap of 10") is a stated bound even though
# the numeral exceeds 4 (SPEC amendment 2026-07-03).
# ---------------------------------------------------------------------------
F="$TMP/drain_maxgen.md"
cat > "$F" <<'EOF'
At each safe boundary (a verdict just recorded and committed) evaluate the relaunch **trigger**:
a generation budget — hand off every 4 recorded verdicts this session (default; a
`Relaunch-every: N` header in the drained spec's SPEC.md header block overrides N) — or a
**degradation override** on re-reading files already read. On fire: spawn a fresh detached
generation via that relaunch command. A **max-generations cap of
10** stops with the baton written + a needs-attention note instead of respawning.
EOF
run_check "$F"
assert_marker "drain max-generations paragraph passes the loop check" absent "[loop]"

# ---------------------------------------------------------------------------
# LOOP CHECK — the four spec-named prose lines must NOT be flagged.
# ---------------------------------------------------------------------------

# (1) drain/SKILL.md tournament cleanup — `tournament` is not a loop trigger.
F="$TMP/tournament.md"
cat > "$F" <<'EOF'
Sweep any leftover `task/NN-<slug>-t*` branches and worktrees a prior
tournament left behind before starting the tournament for this task.
EOF
run_check "$F"
assert_marker "tournament-cleanup line is not flagged as an unbounded loop" absent "[loop]"

# (2) drain/reference.md "no relaunch" — relaunch preceded by `no`.
F="$TMP/no_relaunch.md"
cat > "$F" <<'EOF'
A verifier that fails a merged candidate twice routes to merge →
`Status: failed`, no relaunch.
EOF
run_check "$F"
assert_marker "'no relaunch' line is not flagged as an unbounded loop" absent "[loop]"

# (3) autopilot/reference.md "relaunch clean" — one-shot benign state modifier.
F="$TMP/relaunch_clean.md"
cat > "$F" <<'EOF'
A failed autonomous run is evidence about the task file, not a debugging
invitation: fix the spec/task, discard the branch, relaunch clean.
EOF
run_check "$F"
assert_marker "'relaunch clean' line is not flagged as an unbounded loop" absent "[loop]"

# (4) design/SKILL.md "3× the tokens" — bare cost commentary must NOT satisfy
# the OUTPUT-BUDGET check (a file whose only tokens/words mention is this must
# still fail the budget check).
F="$TMP/three_x_tokens.md"
cat > "$F" <<'EOF'
Note the cost before launching each candidate investigator, so 3 candidates
≈ 3× the tokens of deciding from a survey — worth it only when the decision
is expensive to reverse.
EOF
run_check "$F"
assert_marker "'3× the tokens' does not satisfy the output-budget check" present "[budget]"

# ---------------------------------------------------------------------------
# DISPATCH CHECK — the two wrapped dispatches must be SEEN as dispatches.
# Each fixture wraps the dispatch verb and the agent noun across two physical
# lines and carries NO tier token, so being SEEN == being flagged for a
# missing tier.
# ---------------------------------------------------------------------------

# (a) drain/SKILL.md:68-69 — "launch ONE background ... agent".
F="$TMP/drain_dispatch.md"
cat > "$F" <<'EOF'
Then launch ONE background `general-purpose`
agent with `isolation: worktree` using the worker prompt in reference.md.
EOF
run_check "$F"
assert_marker "drain wrapped dispatch is SEEN (flagged for missing tier)" present "[dispatch]"

# (b) design/SKILL.md — "launching: ... prototype agent" wrapped.
F="$TMP/design_dispatch.md"
cat > "$F" <<'EOF'
For choices where reading isn't enough, prototype instead: one background
agent per candidate with `isolation: worktree`, timeboxed to a small fixed
scope, each returning a short report. Note the cost before launching: each
investigator or prototype agent pays its own full context.
EOF
run_check "$F"
assert_marker "design wrapped dispatch is SEEN (flagged for missing tier)" present "[dispatch]"

# ---------------------------------------------------------------------------
# DISPATCH CHECK — incidental co-occurrence must NOT be seen as a dispatch.
# "dispatch order" and "worker's lock" in one prose paragraph are far apart.
# ---------------------------------------------------------------------------
F="$TMP/incidental.md"
cat > "$F" <<'EOF'
Report the plan in one block: dispatch order, what's already done, what's
deferred/blocked and why. An `in-progress` task is a dead worker's lock only
after the liveness check confirms it.
EOF
run_check "$F"
assert_marker "incidental dispatch/worker co-occurrence is not a dispatch" absent "[dispatch]"

# ---------------------------------------------------------------------------
# DISPATCH CHECK — a tiered dispatch PASSES; adjacent-paragraph tier counts.
# ---------------------------------------------------------------------------
F="$TMP/tiered_dispatch.md"
cat > "$F" <<'EOF'
Launch one background scout agent to map the subsystem, running on
`haiku` at `effort: low`, capped at 300 words.
EOF
run_check "$F"
assert_marker "tiered dispatch is not flagged" absent "[dispatch]"

F="$TMP/tier_adjacent.md"
cat > "$F" <<'EOF'
Dispatch one worker agent per task in dependency order.

Each such worker runs on the session model at raised effort and returns a
capped verdict of no more than 300 words.
EOF
run_check "$F"
assert_marker "dispatch with tier in an adjacent paragraph is not flagged" absent "[dispatch]"

# ---------------------------------------------------------------------------
# NEGATIVE CONTROLS — the checks actually fire.
# ---------------------------------------------------------------------------

# Bare unbounded re-dispatch → loop check fires.
F="$TMP/unbounded_loop.md"
cat > "$F" <<'EOF'
On failure, retry the worker with fresh evidence until the gates pass.
EOF
run_check "$F"
assert_marker "bare unbounded retry is flagged by the loop check" present "[loop]"

# LOOP CHECK — a stray numeral is not a bound (wte-07). These paragraphs were
# surfaced by an adversarial pass: each is a genuinely unbounded loop that the
# permissive matcher wrongly passed because a stray numeric token (a range not
# naming a cycle, or a digit glued to a non-cycle noun) fooled the bound regex.
# All must be FLAGGED.
i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  F="$TMP/fn_$i.md"; printf '%s\n' "$line" > "$F"; i=$((i+1))
  run_check "$F"
  assert_marker "stray-numeral false-negative is flagged: $(printf '%s' "$line" | cut -c1-45)" present "[loop]"
done <<'EOF'
When the verifier rejects a candidate, retry the same worker and keep retrying; each rerun re-reads lines 2-4 of the failing assertion.
The harness will re-dispatch the scout to pull the page again, and keeps relaunching it every time the request logs 2 timeouts back-to-back.
The critic must revise its verdict and cycle the diff back, repeating the loop as long as the suite reports fewer than 2 passing checks.
Re-dispatch the researcher whenever a source 404s and iterate on the query until it resolves; this has spun across days 2-4 with no bound on attempts.
Keep retrying the ingest agent until the manifest validates; every retry stamps 2 timestamps into the audit log, and there is no ceiling on re-runs.
On failure, retry the worker with fresh evidence, capping each report at 2k tokens.
EOF

# LOOP CHECK — genuine bounds in varied phrasing (spelled numbers, ranges,
# "single", quantifiers) must all PASS. Surfaced by the same adversarial pass as
# false positives the first tightening introduced; the robust matcher accepts
# them. All must be ABSENT of [loop].
i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  F="$TMP/fp_$i.md"; printf '%s\n' "$line" > "$F"; i=$((i+1))
  run_check "$F"
  assert_marker "genuine bound is not flagged: $(printf '%s' "$line" | cut -c1-45)" absent "[loop]"
done <<'EOF'
The reviewer will iterate up to four rounds before stopping.
Allow no more than two retries on a failed step.
Run two-to-three cycles of critique.
Set a cap of three relaunches for the worker.
Cap retries at three attempts, max.
Iterate two rounds and stop.
Revise the answer up to three times.
Cap the cycle at a single relaunch, no more.
Bound the evaluator-optimizer loop to 2-4 cycles before accepting the result.
On failure, retry the worker with fresh evidence at most 3 times before routing to failed.
EOF

# ---------------------------------------------------------------------------
# LOOP CHECK — wte-08 residual classes, flag-when-unsure verdict.
# Three false-negative classes must be FLAGGED (the phantom bound is rejected):
# glued/hyphenated compounds, quantifier+count on a NON-cycle noun, and a
# temporal "once/twice" (a subordinating clause, not a repeat count).
# ---------------------------------------------------------------------------
i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  F="$TMP/r8fn_$i.md"; printf '%s\n' "$line" > "$F"; i=$((i+1))
  run_check "$F"
  assert_marker "wte-08 residual false-negative is flagged: $(printf '%s' "$line" | cut -c1-45)" present "[loop]"
done <<'EOF'
On failure, retry the worker onetime and then move on.
The critic will revise the draft one-pass before returning it.
Relaunch the ingest worker twotime, then stop.
Re-dispatch the crawler to pull up to four sources until they all resolve.
Keep re-dispatching the fetcher for up to four shards, unbounded.
Capped at two dashboards, the loader keeps retrying with no ceiling.
Relaunch the orchestrator once a downstream check goes red.
Relaunch once the gate flips red, and keep relaunching.
EOF

# ---------------------------------------------------------------------------
# LOOP CHECK — wte-08 false-positive classes must PASS (the bound is seen):
# a single interposed count-adjective, and the added noun/form vocabulary
# (loop(s), hyphenated re-dispatches, ordinals). All must be ABSENT of [loop].
# ---------------------------------------------------------------------------
i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  F="$TMP/r8fp_$i.md"; printf '%s\n' "$line" > "$F"; i=$((i+1))
  run_check "$F"
  assert_marker "wte-08 count-adjective/vocabulary bound is not flagged: $(printf '%s' "$line" | cut -c1-45)" absent "[loop]"
done <<'EOF'
On failure, retry the worker two additional attempts, then route to failed.
The critic will revise the diff three further cycles before accepting it.
Relaunch the worker two more times, then stop.
Iterate two consecutive rounds and stop.
Retry the step, capping the run at three loops total.
Keep re-dispatching, but at most two re-dispatches in all.
Relaunch the worker, stopping at the third attempt.
Revise the draft, capped at the third pass.
EOF

# Un-tiered dispatch → dispatch check fires.
F="$TMP/untiered_dispatch.md"
cat > "$F" <<'EOF'
Spawn three background workers to implement the task in parallel.
EOF
run_check "$F"
assert_marker "un-tiered dispatch is flagged by the dispatch check" present "[dispatch]"

# File with no output budget → budget check fires.
F="$TMP/no_budget.md"
cat > "$F" <<'EOF'
This file mentions no budget at all, only prose about the work to be done.
EOF
run_check "$F"
assert_marker "file lacking an output-budget statement is flagged" present "[budget]"

# File WITH a valid output budget → budget check does not fire.
F="$TMP/has_budget.md"
cat > "$F" <<'EOF'
The reviewer returns a structured verdict capped at 2k tokens, never the
transcript.
EOF
run_check "$F"
assert_marker "file with a valid output budget passes the budget check" absent "[budget]"

# ---------------------------------------------------------------------------
# EXIT CODES — a clean file exits 0; a violating file exits 1 and names it.
# ---------------------------------------------------------------------------
F="$TMP/clean.md"
cat > "$F" <<'EOF'
Launch one scout agent on `haiku` at `effort: low` to locate the config,
returning no more than 300 words.

If it comes back empty, relaunch it once with a broader glob.
EOF
run_check "$F"
assert_eq "a fully-conformant file exits 0" 0 "$RC_EXIT"
assert_marker "clean file: no dispatch failure" absent "[dispatch]"
assert_marker "clean file: no loop failure" absent "[loop]"
assert_marker "clean file: no budget failure" absent "[budget]"

F="$TMP/violating.md"
cat > "$F" <<'EOF'
Spawn three background workers to grind on the task, and retry each until it
finally passes.
EOF
run_check "$F"
assert_eq "a violating file exits 1" 1 "$RC_EXIT"
assert "violating-file report names the file" \
  sh -c "printf '%s' \"$RC_OUT\" | grep -qF 'violating.md'"

# ---------------------------------------------------------------------------
echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
