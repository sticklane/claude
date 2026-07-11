# Verification: 01-deep-research-pins

Verdict: PASS

## Per-criterion

1. `node --check .claude/workflows/deep-research.js`
   ✓ exit 0. Output: `exit:0` (no syntax errors printed).

2. `grep -n 'model' .claude/workflows/deep-research.js`
   ✓ All literal `model:` key hits (checked via `grep -n 'model:'`) are exactly
   two: line 188 (inside Search `agent()` opts:
   `label: "search:"+angle.label, phase: "Search", schema: SEARCH_SCHEMA, model: "haiku", effort: "low"`)
   and line 222 (inside Fetch `agent()` opts, same object as `phase: "Fetch"`,
   `schema: EXTRACT_SCHEMA`). Other `model`-substring hits (lines 5, 18-20,
   104, 262, 325, 346) are meta.phases detail strings and prose comments
   ("session model"), not agent() opts.
   MANUAL check: read the Scope agent() call (line 110-121, opts =
   `{ label: "scope", schema: SCOPE_SCHEMA }`), Verify agent() call (line
   269-273, opts = `{ label, phase: "Verify", schema: VERDICT_SCHEMA }`),
   Synthesize agent() call (line 347-359, opts = `{ label: "synthesize",
   schema: REPORT_SCHEMA }`) — confirmed none carries a `model` or `effort` opt.

3. `grep -c 'model: "haiku"' .claude/workflows/deep-research.js`
   ✓ Output: `2` (≥2 satisfied).

## Goal cross-checks

- meta.phases Search detail: "...one per angle — haiku + effort:low" ✓ (was
  "— effort:low").
- meta.phases Fetch detail: "...extract falsifiable claims — haiku +
  effort:low" ✓ (was "— effort:low").
- Stage comment above pipeline (line 183): "Search + Fetch/Extract run on
  haiku at effort:'low' — mechanical fan-out" ✓ (was "run at effort:'low'").
- Header comment block (lines 15-21) updated: "Search + Fetch/Extract are
  mechanical fan-out → haiku + effort:'low'" and a new Verify-is-judgment
  decision line: "Verify stays on the session model — its refuters are
  judgment work, not a mechanical stage, so it takes no model pin and no
  effort downgrade (SPEC R1's resolved open question: adversarial
  refutation is judgment, so no haiku pin)." ✓ present.

## Scope / diff check

`git diff fd4a4d2 --stat` → only `.claude/workflows/deep-research.js`
(9 insertions, 5 deletions) changed. Matches Touch: exactly. No other files
modified.

## Append-only task-file check

`git diff fd4a4d2 -- specs/workflow-model-pins/tasks/01-deep-research-pins.md`
→ empty (no changes at all vs base). Not a violation (nothing added exceeds
allowed set), but note: acceptance checkboxes remain unticked (`- [ ]`) and
Status line still reads "in-progress" rather than done, despite the
implementation being complete and passing all three criteria. This is a
completeness/bookkeeping gap, not a scope-creep or append-only violation.

`git diff fd4a4d2 -- '*/tasks/*.md' --stat` → empty (no other task files
touched).

## Gates

Repo has no `scripts/check.sh` for this workflow-only change; `node --check`
is the stated gate and passes.

## Verdict

PASS — all three acceptance criteria verified by direct command execution,
Goal cross-checks (phase details, stage comment, header decision line) all
present, diff scoped to the single Touch file, and no append-only violation
in the task file (file simply left unmodified/un-ticked).
