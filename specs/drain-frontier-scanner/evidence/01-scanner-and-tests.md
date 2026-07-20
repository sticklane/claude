# Verification: 01-scanner-and-tests

Verdict: FAIL (append-only violation on the task file; all functional
criteria pass)

## Criterion 1 — test suite exits 0, one test per R2 incident class

Command: `python3 .claude/skills/drain/test_drain_frontier.py -v`

Result: exit 0. 22 tests, `OK`. One TestCase class per named incident
class: DependencyGating, OrderingTriple (3 subtests: priority order,
unblocking-power tie-break, lexicographic final tie-break),
TouchDisjointPerSpec, GroupCoAdmissibility (incl. ungrouped-runs-alone),
ClaimedCollision (incl. `min(N, candidates)` explicit test), GlobPrefix
(overlap / non-overlap / ambiguous-conservative), UnresolvedExternalDep,
ParseSemantics (missing Status/Priority defaults exit 0 w/ diagnostics vs
malformed Status non-zero, both via CLI and in-process), WindowTruncation,
ExcludedStatus (blocked/deferred/needs-verification excluded from
dispatchable), GoldenFixture.

✓ PASS on the literal command.

**Coverage gap found (not a functional bug):** `TouchDisjointPerSpecTestCase`
has a docstring claiming "computed per-spec not globally" but its only test
(`test_touch_collision_keeps_task_dispatchable_but_out_of_admissible`) uses
a single spec dir — it does not distinguish per-spec from global behavior
(an incorrectly-global implementation would pass the same test). I manually
verified the underlying implementation IS correct (per-spec) by invoking the
CLI against two temp spec dirs with an identical `Touch:` path in each —
both tasks landed in `admissible` (see command below), confirming
`compute_frontier`'s per-spec reset of `admitted_touch` is right. So this is
a test-coverage nitpick, not an implementation defect, and the criterion's
literal bar ("at least one test per R2 incident class") is met since a test
class for the incident class exists and passes.

```
$ python3 .claude/skills/drain/drain_frontier.py <specA> <specB>   # identical Touch: src/shared.py in each
# both 01-a.md (specA) and 01-b.md (specB) appear in "admissible" — confirms per-spec, not global
```

## Criterion 2 — golden fixture JSON matches EXPECTED.md

Command:
`python3 .claude/skills/drain/drain_frontier.py .claude/skills/drain/fixtures/basic-window --window 2`

Exit 0. Output `admissible` = `["...02-alpha.md", "...03-beta.md"]`,
exactly matching `fixtures/basic-window/EXPECTED.md`'s documented
"Expected admissible under `--window 2`: 02-alpha.md, 03-beta.md".
`dispatchable` = [02-alpha, 03-beta, 04-gamma] (all P1, alpha has
unblocking-power 1 via 05's dep on 02, so alpha sorts first); `blocked`
= [05-delta, reason unmet-deps, deps [02]].

✓ PASS.

## Criterion 3 — fixture lives only under the skill dir

Command:
`[ ! -d specs/basic-window ] && ! ls .claude/skills/drain/fixtures/ | grep -qv basic-window`

Exit 0 (`specs/basic-window` does not exist; `fixtures/` contains only
`basic-window`).

✓ PASS.

## R1 pinned-semantics spot checks (against SPEC.md)

- `dispatchable ⊇ admissible`: structurally true — `admissible_tasks` is
  built only from `dispatchable_tasks` (drain_frontier.py:322-344).
- `--claimed` filters Touch only, no live-slot subtraction; `admissible`
  length = `min(N, candidates)`: confirmed by
  `test_admissible_is_min_window_candidates_not_reduced_by_claimed` (a
  claim disjoint from all 3 candidates still yields `len(admissible) == 2`
  under `--window 2`, not `2 - 1`), and by code: `claim_touch` only unions
  into `admitted_touch`, `window` only slices the final list.
- Read-only, stdlib-only: only `argparse, json, re, sys, pathlib` imported;
  only `Path.read_text`/`.glob` used, no writes anywhere in the file.
- Per-spec windows, never interleaved: confirmed by code (`for sd in
spec_dirs:` loop resets `admitted_touch = set(claim_touch)` per spec) and
  by a manual multi-spec probe (two spec dirs, identical `Touch:` path in
  each, both tasks landed in `admissible` — proving disjointness is
  evaluated within each spec's own scope, not globally).

No correctness concerns found in R1 semantics.

## Append-only task-file diff check

Command: `git diff 51aae98 -- 'specs/*/tasks/*.md'`

The diff touches only `specs/drain-frontier-scanner/tasks/01-scanner-and-tests.md`
(no other task file). Within it:

- Added a `<!-- PLAN (worker, task 01) ... -->` comment block — sanctioned
  (plan-block maintenance).
- **Status: line unchanged** (`in-progress` in both base and HEAD) — no
  checkboxes were ticked (`- [ ]` unchanged in all three acceptance lines)
  despite all three criteria passing on the current tree.
- **Two acceptance-criterion body lines had leading whitespace stripped**
  (continuation lines of criteria 2 and 3's command backticks: ` .claude/skills/drain/fixtures/basic-window --window 2\`` →`.claude/skills/drain/fixtures/basic-window --window 2\``, and similarly
for criterion 3's `| grep -qv basic-window` line). This is a content edit
  to the acceptance-criterion text itself — not a Status flip, checkbox
  tick, evidence-citation addition, or plan-block edit. Per the append-only
  contract stated in the task file's own header comment and per this
  verification's instructions ("Anything else — criterion text... — is an
  automatic FAIL finding"), this is a violation, even though it is
  whitespace-only and does not change the criterion's meaning.

✗ FAIL — append-only violation (whitespace-only edit to two acceptance
criteria's command text, outside the sanctioned edit set).

## Touch-scope check

Command: `git diff --stat 51aae98 HEAD`

Files changed: `.claude/skills/drain/drain_frontier.py`,
`.claude/skills/drain/test_drain_frontier.py`,
`.claude/skills/drain/fixtures/basic-window/{SPEC.md,EXPECTED.md,tasks/*.md}`,
and `specs/drain-frontier-scanner/tasks/01-scanner-and-tests.md` (task file
itself). `git status --porcelain` on the worktree is clean (no uncommitted
changes). No evidence file existed prior to this verification run.

✓ PASS — matches the task's `Touch:` list
(`.claude/skills/drain/drain_frontier.py, .claude/skills/drain/test_drain_frontier.py,
.claude/skills/drain/fixtures/`) plus the task file itself. No scope creep.

## Overfitting check

Tests were written first (`3921f81 test: failing drain_frontier scanner
tests (RED)`, then `7c67da5 feat: ... (GREEN)`) — a real RED→GREEN split
per git log. Reviewed the implementation for special-casing: dependency
resolution, ordering, Touch-prefix conflict, and Group co-admissibility are
all general algorithms operating on parsed structure, not literal
fixture-path or fixture-content matches. The one GoldenFixtureTestCase does
assert against the specific fixture's expected paths, which is appropriate
(it's the golden-fixture check itself, mirrored by the task's own
acceptance criterion 2). No evidence of gaming.

## Gates

No repo-wide `scripts/check.sh` was run beyond the task's own three
acceptance commands per the task's own scope; the test suite itself is the
gate for this Python addition and it is green.
