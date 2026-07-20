# Verification: task 04 — admission module

Verdict: PASS

Branch: task/04-admission-module (worktree agent-a5251e7dd0cdfbb15)
Base for diffs: 15a55a9

## Per-criterion

1. Files exist — ✓
   `test -f .claude/skills/drain/admission.py && test -f .claude/skills/_shared/touch_disjoint.py`
   → "BOTH EXIST"

2. `python3 .claude/skills/_shared/test_touch_disjoint.py` — ✓ exit 0
   Output: "all 6 touch_disjoint cases passed"

3. `python3 .claude/skills/drain/test_admission.py` — ✓ exit 0
   Output: "all 10 admission tests passed"

4. Distinct fixture cases (a)-(e), not combined — ✓
   `python3 .claude/skills/drain/test_admission.py | grep -co 'case [a-e]'` → 5
   Read test_admission.py: 5 separately-defined functions
   (case_a_three_disjoint_specs_all_claim … case_e_two_level_cap_throttle),
   each its own assertion block, matching Steps 7-10 (a/b: claim_specs
   disjointness+exclusion; c/d: cross-spec co-admit + per-spec window
   scoping; e: two-level cap throttle 15→10, per-spec ≤5).

5. R14 negative — malformed JSON errors — ✓
   `support_load_frontier_rejects_malformed` (missing key, wrong list types)
   and `support_cli_exits_nonzero_on_malformed_frontier` (subprocess run,
   asserts returncode != 0). Both pass in the green run above.

6. touch_disjoint reads Touch: from fixture files, not JSON — ✓
   `test_footprint_reads_touch_headers_from_disk_not_json` writes two temp
   task-file fixtures with `Touch:` headers and asserts `footprint()` unions
   them by reading from disk (tempfile.TemporaryDirectory + Path.write_text/
   read_text) — no JSON object touched anywhere in the call path.

7. Dedicated ambiguous-prefix test asserts "not disjoint" — ✓
   `test_ambiguous_prefix_resolves_to_not_disjoint`: `pair_conflicts("src/*",
"src/app/main.py") is True`, `entries_disjoint(...) is False` (both
   orderings), never resolving "disjoint".

8. touch_disjoint.py algorithm matches drain_frontier.py's exact predicate — ✓
   Direct comparison of the two files:
   - Both: `_GLOB_META_RE = re.compile(r"[*?\[]")`
   - Both: `literal_prefix` — prefix up to first glob metachar
   - Both: pair-conflict test — `pa.startswith(pb) or pb.startswith(pa)`
     (drain_frontier.py's `_pair_conflicts`, touch_disjoint.py's
     `pair_conflicts`) — identical, ambiguity resolves to conflict/not-disjoint
   - Both: `entries_disjoint(set_a, set_b)` — `not any(pair_conflicts(a,b) ...)`
     Confirmed by grepping drain_frontier.py directly (lines 55, 77-93).

9. Tests are behavioral, not tautological — ✓ (verified by live mutation,
   restored after each check via file backup/copy-back, never `git checkout`)
   - Mutated touch_disjoint.py's `pair_conflicts` from `or` to `and`
     (breaking conservative-ambiguity resolution) → re-ran
     test_touch_disjoint.py → FAILED at "ambiguous prefix resolves to NOT
     disjoint" as expected (exit 1). Restored from backup; re-ran → exit 0.
   - Mutated admission.py's `per_spec_ceiling = min(w, 5)` to `= 999`
     (breaking the per-spec cap) → re-ran test_admission.py → FAILED at
     "case d: window-empty is per-spec, not global" (exit 1), which also
     would have caught case (e)'s cap throttle had it run. Restored from
     backup; re-ran → all 10 pass, exit 0.
     This demonstrates case (b)/(d)/(e) and the ambiguity test genuinely
     exercise behavior, not tautologies.

## docs/TASKS.md tech-debt entry

Pre-existing, confirmed present at lines 117-124 (added 2026-07-19, before
base commit 15a55a9): notes `touch_disjoint.py` and `drain_frontier.py` as
two independent implementations of the same algorithm, recommending a
future convergence. Task correctly did NOT re-edit it (out of Touch).
`git diff 15a55a9..HEAD -- docs/TASKS.md` → empty.

## Append-only task-file check

`git diff 15a55a9..HEAD -- specs/drain-multi-spec-swarm/tasks/` shows only:

- `Status: pending` → `Status: in-progress`
- An added `<!-- PLAN ... -->` HTML comment block (marked "deleted at
  close-out")
  No other task file changed; Goal/Steps/Touch/Budget/Acceptance text is
  byte-identical to base. Acceptance checkboxes remain unticked `[ ]` as
  expected (close-out ticks them after this report).

## Touch-scope check

`git diff --name-only 15a55a9..HEAD`:

```
.claude/skills/_shared/test_touch_disjoint.py
.claude/skills/_shared/touch_disjoint.py
.claude/skills/drain/admission.py
.claude/skills/drain/test_admission.py
specs/drain-multi-spec-swarm/tasks/04-admission-module.md
```

Exactly the two Touch-scoped modules, their two unit-test files, and the
task file itself. No SKILL.md, reference.md, token-discipline.md,
mirror/plugin files, drain_frontier.py, or docs/TASKS.md touched — matches
the Touch header and the task's explicit "do not touch" list.

## Criteria-adequacy (per requirement)

- R1 (greedy footprint-disjoint spec claim, cap 3): cases (a)/(b) are L2
  behavioral unit tests exercising `claim_specs` directly with real
  fixture task files on disk — entails the requirement. PASS, L2.
- R2 (two-level admission cap, per-spec W≤5 + global≤10): cases (c)/(d)/(e)
  are L2 behavioral tests, confirmed non-tautological by live mutation
  (see criterion 9) — entails the requirement. PASS, L2.
- R14 (composition boundary + negative constraint): dedicated tests for
  both halves (disk-sourced Touch footprint; non-zero exit on malformed
  JSON, exercised via subprocess for the CLI path) — L2/L3 (subprocess
  test is L3, exercising the actual CLI entry point end-to-end). PASS.
- Algorithm-pinning (round-10 critique fix): direct side-by-side source
  comparison of touch_disjoint.py vs drain_frontier.py — L1 structural
  match plus L2 behavioral confirmation (the ambiguous-prefix test) that
  both resolve identically. PASS.
- Lease-claim CAS (R6/R17, reference.md protocol): `claim_decision` pure-
  function tests are L2; `git_cas_claim` happy-path test actually runs git
  init/commit and confirms round-trip via a real repo — L2/L3 for the
  happy path only. The FRESH-collision/reclaim git-level race path is
  explicitly deferred to task 05 per this task's Goal section — correctly
  out of this task's scope, not a gap in this task's own claim.

## Scope-creep check

No scope creep found. Diff is exactly Touch-listed modules + their test
files + the task file's Status/PLAN-comment update.

## Gates

No repo-wide `scripts/check.sh` was run separately; both self-running unit
test scripts are this task's canonical gate and both pass (exit 0), matching
the task's "no central pytest runner" design.
