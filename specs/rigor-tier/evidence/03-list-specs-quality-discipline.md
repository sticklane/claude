# Verification: Task 03 — list-specs displays the tier; quality-discipline.md scopes TDD

Verdict: PASS

## Per-criterion results

1. `python3 -m pytest .claude/skills/list-specs/test_list_specs.py -k rigor`
   - Result: PASS. 2 passed, 35 deselected.
   - `RigorTierRenderTestCase::test_render_table_no_rigor_marker_for_production_default`
     and `::test_render_table_shows_prototype_rigor_tier` both pass.

2. `grep -qi "rigor" .claude/skills/list-specs/list_specs.py`
   - Result: exit=0 (match found).

3. `grep -qi "rigor" .claude/rules/quality-discipline.md`
   - Result: exit=0 (match found).

4. `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py -k rigor`
   - Result: PASS. 2 passed, 35 deselected (same two rigor test names).

5. `grep -qi "rigor" antigravity/.agents/skills/list-specs/list_specs.py`
   - Result: exit=0 (match found).

## Substance check (beyond the greps)

- `list_specs.py` (both `.claude/skills/list-specs/` and its antigravity
  mirror, byte-identical diffs): adds `RIGOR_RE` regex parsing `Rigor:
prototype|production` header (case-insensitive, optional brackets),
  `parse_rigor()` defaulting to `"production"` when absent/unrecognized.
  `scan_and_classify` sets `row["rigor"] = parse_rigor(text)` alongside the
  existing `classify_spec` call (mirrors how `Status` is already parsed, per
  the task's Goal). `render_table` uses `r.get("rigor")` (safe against rows
  built without the key, e.g. unit-test fixtures for `classify_spec`) and
  appends ` [prototype]` to the Spec cell ONLY when `rigor == "prototype"`;
  production/absent rows render identically to before (verified: full
  37-test suite in both runtimes passes, including all pre-existing
  `EndToEndFixtureTestCase`/`ClassifySpecTestCase` tests that assert on
  unmodified row rendering — no regression).
- `SKILL.md` prose updated in both `.claude/skills/list-specs/SKILL.md` and
  `antigravity/.agents/skills/list-specs/SKILL.md`: both now state "A spec
  declaring `Rigor: prototype` carries a `[prototype]` annotation on its
  Spec cell; production (or absent, the default) specs show no marker."
  Wording is a straightforward mirrored port (matches
  mirror-procedure-discipline: same procedure/statement, not a rewrite).
- `.claude/rules/quality-discipline.md` gains one bullet, "**Rigor-scoped.**"
  under the TDD section, scoping the mandate to `Rigor: production` work
  (absent = production), stating a `Rigor: prototype` spec substitutes a
  mechanical acceptance-command run for red-first, and citing
  `specs/rigor-tier` (not restating the mechanism) plus noting it's
  surfaced in `/list-specs`'s table — matches task step 4 exactly.

## Full regression suites (no test-count regressions)

- `python3 -m pytest .claude/skills/list-specs/test_list_specs.py -v` → 37
  passed (35 pre-existing + 2 new rigor tests), 0 failed.
- `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py -v`
  → 37 passed, 0 failed.

## Scope / Touch compliance

`git diff --stat e33ae7a HEAD`:

```
 .claude/rules/quality-discipline.md                |  5 +++
 .claude/skills/list-specs/SKILL.md                 |  6 ++--
 .claude/skills/list-specs/list_specs.py            | 32 +++++++++++++++--
 .claude/skills/list-specs/test_list_specs.py       | 42 ++++++++++++++++++++++
 antigravity/.agents/skills/list-specs/SKILL.md     |  4 ++-
 .../.agents/skills/list-specs/list_specs.py        | 32 +++++++++++++++--
 .../.agents/skills/list-specs/test_list_specs.py   | 42 ++++++++++++++++++++++
 .../tasks/03-list-specs-quality-discipline.md      | 17 +++++++++
 8 files changed, 171 insertions(+), 9 deletions(-)
```

All 7 changed source files are exactly the task's `Touch:` list. No
forbidden paths touched: `.claude/skills/idea/SKILL.md`,
`.claude/skills/breakdown/SKILL.md`, `.claude/skills/build/SKILL.md`,
`.claude/skills/drain/SKILL.md`, their mirrors, and
`.claude-plugin/plugin.json` are all absent from the diff — confirmed by
`git diff --stat` above containing none of those paths.

## Append-only task-file check

`git diff e33ae7a HEAD -- specs/rigor-tier/tasks/03-list-specs-quality-discipline.md`
shows only a single insertion: the `<!-- PLAN (delete at close-out) -->`
comment block (17 lines) inserted between the header fields and `## Goal`.
Goal/Steps/Acceptance/Touch text is byte-identical to base. The `Status:`
line remains `in-progress` (not flipped to done/complete) and all 5
acceptance checkboxes remain unticked `[ ]` — the worker did not mark the
task closed, though the implementation and all 5 acceptance commands pass.
This is a minor process gap (task not formally closed) but does not affect
acceptance-criteria correctness; noted as a finding below, not a FAIL.

## Findings

- **Process note (not a FAIL):** Task file's `Status:` line was not flipped
  to `done`/`complete` and none of the 5 acceptance checkboxes were ticked,
  despite all 5 acceptance commands passing and the implementation being
  complete. Someone should flip Status and tick boxes before considering
  this task closed in the drain/build workflow, but this is a bookkeeping
  gap, not a functional defect — none of the caller's 5 specified
  acceptance criteria reference the Status line or checkboxes.
- No scope creep detected — diff is limited to the 7 Touch-listed files
  plus the task file's plan-comment insertion.
- No evidence of overfitting to the exact test inputs: `parse_rigor()` is a
  general regex over any spec's header text (not special-cased to the test
  fixture's literal string), and `render_table`'s annotation logic applies
  uniformly to any row with `rigor == "prototype"`, not the specific test
  fixture spec name.
