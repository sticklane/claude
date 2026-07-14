# Handoff — 2026-07-14, resumed session over wake budget (second refresh this thread)

## Task

User invoked `/agentic:drain` (no argument = whole `specs/` queue) in a
fresh session. Before launching drain, resumed a prior HANDOFF.md that
named 3 specs as READY but not yet broken down. This session did that
breakdown work (plus one more critique round narrow-autopilot's own
handoff explicitly asked for) — **drain itself has not been launched
yet**. That's the next step.

## State — what's done this session

**1. narrow-autopilot — re-critiqued (3 more fix rounds), broken into 6
tasks, decomposition critic-verified READY.** Commits `13d441f`,
`c12787b`, `e02559b` (critique fixes: manifest-coverage gap, inert
canary phrase, unenforced canary-source requirement), `8b93411` (cleared
stale critique-findings.md), `58c08e3` (6-task breakdown, 2 critic
rounds on the decomposition itself — first caught a real cross-task
ordering hazard, fixed and re-verified READY). Tasks: 01 (P0, retire
autopilot + fold into `.claude/skills/build/{SKILL.md,reference.md}`),
02-05 (P1, parallel Group — `.claude`-leg consumers / core-tree doctrine
sweep / antigravity leg / codex leg), 06 (P1, closing verification +
plugin.json bump + sequencing check). All `Status: pending`.

**2. build-doc-currency-check — broken into 2 tasks, both deliberately
`Status: blocked`, critic-verified READY WITH NITS (2 cheap nits
applied).** Commit `c2ceec0`. Both tasks carry
`Unblock: run: for f in specs/narrow-autopilot/tasks/*.md; do grep -q
'^Status: done' "$f" || echo "not done: $f"; done` — this spec's
collision with narrow-autopilot is broader than its own SPEC.md text
states (narrow-autopilot also touches the antigravity and codex `build`
mirrors, not just `.claude/skills/build/SKILL.md`), so both tasks are
blocked, not pending, until every narrow-autopilot task reads
`Status: done`. **Nothing auto-flips this** — drain does not re-run
`Unblock: run:` on a pre-existing blocked task; a human or a future
session must re-check and flip `Status: blocked` → `pending` once
narrow-autopilot fully lands.

**3. retire-static-dashboards — broken into 5 tasks, critic-verified
(1 blocking gap found and fixed, 1 nit applied).** Commit `083463a`.
First critic pass found NOT READY: a between-defs section comment in
`.claude/skills/workboard/workboard.py` citing `fleet/reference.md`
sits outside any function body, so Task 02's reachability-check
deletion wouldn't remove it and no task's `Touch:` covered a fix — fixed
by adding an explicit step+AC to Task 02. Also bumped Task 04's budget
11→15 turns (it does 3 tasks' worth of antigravity-mirror work in one
pass). **Did not re-dispatch a third critic round after this fix** (time/
budget pressure) — the fix is small and mechanical (one grep AC matching
the critic's exact suggested check), but if picking this back up soon,
consider one more critic pass on Task 02 before dispatching it, purely
as insurance given this spec's history (its dead-code orphan set was
under-enumerated twice before this session even started, per its own
critique-findings.md). Tasks: 01/02/04 (P0, parallel Group — fleet+viz.py
/ workboard.py dead-code removal / antigravity mirror), 03 (P1, depends
on 01+02, test deletions), 05 (P1, sink, repo-wide sweep + version bump).
All `Status: pending`.

## Next step

**Launch `/agentic:drain` with no argument** (whole `specs/` queue) — this
is the original request that started this session. Expected behavior once
launched:

- `narrow-autopilot` Task 01 dispatches first (P0), then 02-05 as a
  parallel window, then 06.
- `retire-static-dashboards` Tasks 01/02/04 can dispatch concurrently with
  narrow-autopilot (fully disjoint files — fleet/workboard vs autopilot/
  build) — no conflict.
- `build-doc-currency-check`'s 2 tasks stay `blocked` and get reported in
  drain's exit checklist — this is correct, not a bug. After
  narrow-autopilot's tasks are ALL `Status: done`, re-run the
  `Unblock: run:` check by hand and flip both build-doc-currency-check
  tasks `blocked` → `pending` (then they become dispatchable in a later
  drain pass).
- Other specs (rigor-tier, codequality-agent-console-mutation-coverage,
  idea-research-freshness, trajectory-evals) are already fully done/closed
  — nothing to do there.

## Gotchas

- **This session made a real design call worth knowing about**: encoding
  a cross-spec landing-order constraint as `Status: blocked` +
  `Unblock: run:` (rather than `pending`) is a legitimate use of the task
  grammar (confirmed by critic against `.claude/skills/breakdown/SKILL.md`'s
  own vocabulary) and the only mechanical way to stop an unattended drain
  from landing two specs that edit the same files concurrently. If this
  pattern recurs, it's a reasonable default — no need to ask the user
  again.
- **The prose-formatter hook reflows Edit calls** (confirmed again this
  session) — always treat a just-edited file as reformatted before
  chaining a second `Edit` against the same region; don't assume line
  numbers hold.
- **`Unblock: run:` doesn't auto-fire** — don't assume build-doc-currency-check
  will magically become dispatchable once narrow-autopilot lands; someone
  has to explicitly re-check and flip the status.
- Each spec's decomposition got its own dedicated critic dispatch (not
  reused across specs) — narrow-autopilot needed 2 rounds (1 real bug),
  build-doc-currency-check needed 1 round (nits only), retire-static-dashboards
  needed 1 round (1 real bug, fixed, not re-verified — see above).

## Verification

No task `Status` flipped to `done` this session — all work was spec-level
critique/breakdown/decomposition-review, matching the prior session's own
precedent for skipping a verifier dispatch. Every fix (critique fixes,
decomposition fixes) was re-verified by a fresh critic pass after landing,
**except** retire-static-dashboards' orphaned-comment fix (see Gotchas —
time-boxed, recommend one more pass before dispatching Task 02).
