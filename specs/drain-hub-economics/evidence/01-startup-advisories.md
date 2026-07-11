# Verification: 01-startup-advisories

Verdict: PASS

## Criterion 1 — marker grep
Command: `grep -qi 'hub-economics advisory' .claude/skills/drain/SKILL.md && echo MATCH`
Output: `MATCH`
Result: PASS

## Criterion 2 — MANUAL block coverage
Command: `Read .claude/skills/drain/SKILL.md` (lines 66-77)
Block text (excerpt):
```
**Hub-economics advisory (gen 1, never blocking).** Two advisory lines at
gen-1 startup — never on baton generations, and neither ever blocks
dispatch: (a) *frontier-hub* — when the model the harness disclosed in this
session's system context maps to the **frontier tier** (`runtimes/` profiles
carry the mapping; Claude default: `fable`), print one line citing the
wake-economics doctrine (step 2) and recommending a relaunch on a deep-tier
(`opus`) or lower hub via a fresh `/drain` session with the same argument —
queue state is committed, so nothing is lost; skip silently where the runtime
discloses no model. (b) *heavy-hub* — when the drain launch arrives beyond the
session's first few turns (the observable heuristic), print one line
recommending that same fresh-session relaunch. Advisory only: neither line
blocks dispatch, and neither prints on baton generations.
```
Checks:
- Both advisories present: frontier-hub (a) and heavy-hub (b) — yes.
- Gen-1 only: "Two advisory lines at gen-1 startup — never on baton
  generations" and repeated "neither prints on baton generations" — yes.
- Non-blocking: "never blocking" in heading + "neither ever blocks dispatch"
  stated twice — yes.
- Names disclosed-model signal: "the model the harness disclosed in this
  session's system context maps to the frontier tier" — yes.
- Names beyond-first-few-turns heuristic: "the drain launch arrives beyond
  the session's first few turns (the observable heuristic)" — yes.
- Recommends deep-tier fresh-session relaunch: "recommending a relaunch on a
  deep-tier (opus) or lower hub via a fresh /drain session with the same
  argument" — yes, and (b) recommends "that same fresh-session relaunch".
- Cites (does not restate) the wake-economics doctrine: "citing the
  wake-economics doctrine (step 2)" — cites, doesn't restate. Complies with
  Touch constraint (doctrine text itself not edited; drain-wake-cost owns it).
Result: PASS

## Constraint — <500-line criterion removed
`## Answers` (2026-07-11, Steven via interview) explicitly relaxes/removes the
line-count criterion. File is 580 lines (`wc -l`), not evaluated as a
criterion. Not counted against PASS.

## Constraint — Touch scope (single file only)
Command: `git diff b634f465d34c475be888fc405c142a4839cd9c80 --stat`
Output:
```
 .claude/skills/drain/SKILL.md | 13 +++++++++++++
 1 file changed, 13 insertions(+)
```
Only `.claude/skills/drain/SKILL.md` changed; no edits to antigravity/,
plugin.json, or codex/. No edits to the wake-economics doctrine text itself
(the block cites step 2 rather than restating it). Result: PASS, no scope
creep.

## Gate — lint-ultra-gate.sh
Command: `bash evals/lint-ultra-gate.sh`
Output: `lint-ultra-gate: OK — all ultra mentions gated in 4 files` (exit 0)
Result: PASS

## Append-only task-file diff check
Command: `git diff b634f465d34c475be888fc405c142a4839cd9c80 -- 'specs/*/tasks/*.md'`
Output: (empty — no diff)
Result: Task file unchanged from base. Worker has not yet flipped Status or
ticked acceptance boxes (Status line still reads "in-progress", checkboxes
unticked in the file as read). This is expected per the task instructions
and is not a violation — nothing appended outside the allowed set because
nothing was appended at all yet.

## Overall verdict: PASS

All checkable acceptance criteria pass; the manual criterion is satisfied by
direct inspection of the added block; Touch scope respected; ultra-gate
passes; task-file diff is clean (no premature or out-of-scope edits).
