# Handoff — 2026-07-14, resumed session over wake budget

## Task

Resumed from the prior HANDOFF.md (now consumed/overwritten by this
file): critique + fix + breakdown the batch of 7 `~/claude` specs
(`build-doc-currency-check`, `codequality-agent-console-mutation-coverage`,
`idea-research-freshness`, `narrow-autopilot`, `retire-static-dashboards`,
`rigor-tier`, `trajectory-evals`). Goal: all 7 critiqued, broken into
tasks, and sound — ready for `/build` or `/drain`.

## State — per spec

**1. rigor-tier — DONE** (pre-existing, unchanged this session). Tasks
`01-04` exist, sanity-checked SOUND.

**2. codequality-agent-console-mutation-coverage — DONE, closed**
(pre-existing). `Status: done`.

**3. idea-research-freshness — DONE.** READY WITH NITS (fresh critique
this session fixed one mechanical nit: the spec's own replacement text
miscounted `docs/guides/large-codebase-context.md`'s intro-paragraph
shape — "4-line" → generic "multi-line", matching task 01's already-safer
phrasing). Tasks `01-04` already existed pre-session and still match.
Nothing left to do.

**4. trajectory-evals — DONE.** Confirmed READY by fresh critique. Broke
into tasks `01-04` this session, sanity-checked by a critic (found 2 real
issues, both fixed): task 01's steps claimed a single `claude -p
--output-format stream-json` invocation could keep plaintext
`session.log` AND write a separate `transcript.jsonl` — infeasible, one
invocation emits one format. Fixed: `EVAL_TRANSCRIPT` now points at
`session.log` itself (which becomes JSONL once `stream-json` is added),
no separate file. Also added manual-pending tags to task 01's paid-
headless-run ACs (a drained worker can't launch `claude -p`). Nothing
left to do.

**5. build-doc-currency-check — SPEC READY, `/breakdown` NOT YET RUN.**
Fresh critique found and fixed a real blocking bug: `grep -c "not by
\$code-review itself"` is unsatisfiable — `\$` collapses to a literal `$`
inside double quotes, and mid-pattern `$` in BRE mode isn't guaranteed to
match a literal dollar sign (reproduced directly: returns 0 even when the
phrase is present). Every prior critique round's "confirmed absent, grep
→ 0" was reading this same false-absent. Fixed with `grep -cF` +
single quotes. Also fixed a low-confidence portability nit (`\|` BRE
alternation → `grep -cE`). Confirmed READY by a second fresh critique
pass. **Next step: run `/breakdown specs/build-doc-currency-check`.**
**Self-correction note**: I marked this task "completed" in my own task
tracker after the critique confirmed READY, without having actually run
`/breakdown` — caught and reopened before writing this handoff. This is
the _exact same mistake_ the prior session's handoff flagged about
itself for `trajectory-evals`. Worth a `/distill` pass in a future
session: something about spec-READY getting conflated with
breakdown-done recurring across sessions.

**6. narrow-autopilot — SPEC READY WITH NITS, `/breakdown` NOT YET RUN.**
Highest-blast-radius spec in the batch (deletes `/autopilot`, sweeps
`.claude/`, `antigravity/`, `codex/`, and more). Two real rounds of fixes
this session:

- R6's prose promised a "whole repo" sweep but its verifying grep scoped
  to only `.claude/ docs/ CLAUDE.md .claude-plugin/ codex/ antigravity/`,
  silently missing `evals/`, `runtimes/`, `README.md`, `AGENTS.md`,
  `bin/`, `tests/`, `agent-console/` — each confirmed to hold a living
  `/autopilot` reference, including a whole orphaned evalset
  (`evals/autopilot/01-security-refusal/`) and stale gate machinery
  (`bin/check-token-discipline`'s `IN_SCOPE` list pointing at paths R1
  deletes). Fixed: broadened the pathspec, named every new hit's
  disposition, cross-checked by re-running the full sweep.
- `gate/SKILL.md` has TWO `/autopilot` mentions, R4 only named one
  (the closing `Next stage:` line, missed the prose sentence above it).
  Fixed.
  Confirmed READY WITH NITS by two successive fresh critique passes (the
  second found nothing new beyond the gate/SKILL.md gap, which is now
  fixed but not yet re-verified by a third pass — the pattern in this spec
  has been "one more layer" almost every round, so **strongly consider one
  more fresh critique before `/breakdown`**, not just proceeding straight
  to breakdown on the strength of the second pass). **Next step: re-run
  `/critique specs/narrow-autopilot` once more to be safe, then
  `/breakdown specs/narrow-autopilot` — give the decomposition a critic
  sanity-check given the blast radius (same rigor as rigor-tier and
  idea-research-freshness got).**

**7. retire-static-dashboards — SPEC READY, `Breakdown-ready: true` set,
`/breakdown` NOT YET RUN.** This spec needed 3 more fix-and-recheck
rounds this session (on top of the 4 it had already been through before
this session started) before settling:

- R4 missed **module-level constants** orphaned alongside the deleted
  functions (`TEMPLATE` — 251 lines, the bulk of the gap — plus 6 more).
  The reachability check script only walked `ast.FunctionDef`; rewrote
  it to walk general `Name`-Load references over both functions and
  module-level assignments, closing the "mechanical gate doesn't see X"
  failure mode structurally (this exact class of bug had already
  recurred twice before this session per the spec's own history).
- R8 (test coverage) missed **three repo-root gated shell tests**
  (`tests/test_workboard_render.sh`, `test_workboard_actionability.sh`,
  `test_fleet_css_drift.sh`) that directly invoke deleted code paths,
  with no runnable AC catching the breakage (no Stop hook runs
  `tests/test_*.sh`). Fixed: named all three + their two exclusive
  fixture trees for outright deletion, added 3 new ACs.
- R8's `test_workboard.py` bullet then repeated the same
  under-enumeration one layer down TWICE across two more critique
  rounds: first missing 6 more orphaned-function test calls
  (`render_batons`, `render_inbox`, `render_filter_tiles`,
  `render_spend_section`, `_spec_dag_html`, `_short_model_name`), then a
  7th (`_spec_dag_tasks`). Both fixed.
  Confirmed READY WITH NITS by the third fresh critique pass (the nits are
  by-design — R8's name list is explicitly "illustrative not exhaustive,"
  backstopped by the `unittest discover` AC as the real completeness
  check, not the list itself). **Next step: run
  `/breakdown specs/retire-static-dashboards`.**

## Files touched (commits, in order, all pushed to `origin/main`)

- `de05b49` — retire-static-dashboards: R4 module-level-constants fix.
- `4389491` — idea-research-freshness: nit fix.
- `36c0cf4`, `b52be70`, `82ce57e` — retire-static-dashboards: R8 fixes
  (3 rounds) + `Breakdown-ready: true`.
- `c0e4bf1`, `858b823` — build-doc-currency-check: grep bug fix, `-E`
  portability nit.
- `ef44c54`, `99d412e` — narrow-autopilot: R6 scope-widening, gate/SKILL.md
  second-mention fix.
- `2007971` — trajectory-evals: 4-task breakdown.

## Gotchas

- **Every spec in this batch keeps yielding "one more layer" on
  re-critique** — this session alone found real bugs in literally every
  spec it touched (5 of 5), often more than one round each. Don't treat
  a `Breakdown-ready: true` marker as trustworthy on its own — the prior
  session's handoff already warned about this, and it kept happening.
  Always dispatch a fresh critic before `/breakdown`, even on a spec
  that "should" already be READY.
- **Concurrent-session pattern from the prior handoff may still apply.**
  Check `claude agents --json` for another live `cwd:
/Users/sjaconette/claude` session before editing further. At the start
  of this session, `claude-a0` (the other session from the prior
  handoff) was idle, not busy — no collision this session, but re-check.
- **`grep -c "...\$..."` inside double quotes is a recurring false-absent
  trap** in this repo's specs (`\$` collapses to a literal `$` before
  grep sees it; mid-pattern `$` in BRE mode isn't guaranteed to match a
  literal dollar sign). Found once this session in
  `build-doc-currency-check`; worth grepping other specs' ACs for the
  same pattern if doing more critique work.
- **The prose-formatter hook reflows edits after every `Edit` call** —
  confirmed safe for prose (just rewraps line width) but always re-read
  after an edit before chaining a second `Edit` against the same region;
  an `old_string` written against pre-formatter text will fail to match.

## Verification

No task `Status` flipped to `done` this session (all work was spec-level
critique/fix/breakdown, matching the prior session's own reasoning for
skipping a verifier dispatch) — each critique verdict is itself the
verification, and every fix in this handoff was independently re-verified
by a fresh critic pass after landing. The one artifact-creation exception,
trajectory-evals' 4-task breakdown, got its own critic sanity-check
(found 2 real issues, both fixed, documented above).

## Next step

1. `/breakdown specs/build-doc-currency-check` (READY, straightforward).
2. `/critique specs/narrow-autopilot` once more (cheap insurance given
   this spec's track record), then `/breakdown specs/narrow-autopilot`
   with a critic sanity-check on the decomposition (highest blast
   radius in the batch).
3. `/breakdown specs/retire-static-dashboards` (READY, straightforward).
4. Once all three are broken down: report back to the user that all 7
   specs from the original batch are critiqued and broken into tasks,
   ready for `/build` or `/drain`.
5. Consider a `/distill` pass on the recurring "critique-confirmed-READY
   getting marked complete without the breakdown actually running"
   pattern — it happened in the prior session (trajectory-evals) and
   again in this one (build-doc-currency-check), self-caught both times
   but worth turning into a standing check.
