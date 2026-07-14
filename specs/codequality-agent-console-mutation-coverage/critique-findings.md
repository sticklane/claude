# Critique findings — codequality-agent-console-mutation-coverage

Verdict: **NOT READY** (drain gen 4 critique intake, 2026-07-12; Run-token e83f34f07094a4fa)

The spec feeds /breakdown then unattended /drain; the critic found the spec
factually mischaracterizes the code it targets, so a drained worker would be
told to test behavior that does not exist. Needs a human spec revision before
it is breakdown-ready.

## Ranked findings (from the critic agent)

1. **execute_push is mischaracterized (conf 88).** Problem section (SPEC.md:22-24)
   claims execute_push has a dirty-check / commit-message assembly (`:2872`) /
   ahead-behind branching. It has none — `agent-console.py:2374-2411` just runs
   `action["argv"]` (a `git ... push` built at `:1030`) via subprocess and
   returns `{code, body}`; branches are only timeout / rc==0 / rc!=0. `:2872` is
   _set_priority's_ commit-message line. Approach step 3 (SPEC.md:44-47)
   prescribes dirty/clean/ahead tests that cannot be written. Fix: rewrite to the
   real surface — rc 0 → `_invalidate_board` called; non-zero exit → `ok:false` +
   exit code in message; `TimeoutExpired` → `exit:None` + timeout message.

2. **render_markdown has zero acceptance criteria (conf 78).** Approach step 4
   (SPEC.md:48-49) adds render_markdown coverage but no criterion (SPEC.md:59-69)
   mentions it — silently droppable under drain pressure. Fix: add a grep anchor +
   a stated mutation (e.g. nested-list rendering stubbed to flat must fail tests).

3. **resume_agent "empty prompt" is not a failure case (conf 82).** Approach
   step 1 (SPEC.md:40) lists "empty prompt" as failure, but `resume_agent`
   (`:2962`) does `(prompt or "continue").strip()` → returns `(True,"resumed")`.
   Real failures are unknown sid (`"not a known session"`) and the
   `_claude_run_bg` OSError/RuntimeError path. Fix: replace "empty prompt" with a
   real failure branch.

4. **grep criterion passes on EITHER wrapper (conf 66).** SPEC.md:63
   `grep -rln "set_priority\|execute_push"` is an OR — one-wrapper coverage passes.
   Fix: two separate required-non-empty greps.

5. **check.sh uses `unittest discover`, not pytest (conf 62).** Bare
   `def test_...` pytest-style tests satisfy the greps but never run under
   `python3 -m unittest discover`. Fix: state tests must be `unittest.TestCase`
   subclasses.

6. **"mutation coverage" title but only resume_agent has a mutation-kill bar
   (conf 60).** Give each endpoint a concrete stub-mutation its tests must kill so
   "covered" is runnable per endpoint, not a reviewer judgment call.

## Next step

Human revises SPEC.md per the fixes above (primarily #1-#3, which block a
correct breakdown), then re-run /critique. Do not /breakdown until READY.

## Re-critique 2026-07-13 (drain critique intake, run a219d53e) — still NOT READY

Spec unchanged since the 2026-07-11 verdict; all findings re-verified against
current agent-console.py. Drain-fatal: execute_push Approach/acceptance
describe nonexistent branches (real surface is rc-0 / rc-nonzero / timeout,
agent-console.py:2451-2488); resume_agent "empty prompt" is a success not a
failure (:3040); check.sh runs unittest discover so bare pytest-style tests
pass vacuously; OR-grep satisfied by one wrapper; render_markdown step has no
criterion; line anchors ~90 lines stale. Gaps confirmed real (no tests name
the four functions) — spec mis-specified, not moot. Recovery: human revises
SPEC.md (findings 1-3 first), then re-run /critique.

## Re-critique 2026-07-13 (drain critique intake, run 57520c7421ab1aab) — still NOT READY

Third consecutive NOT READY on an unchanged spec (2026-07-11, 2026-07-12,
now this run). Findings unchanged in substance, line anchors now stale by
~90-190 lines against current agent-console.py (execute_push actual :2542,
resume_agent :3122, set_priority :3025, render_markdown :1206). Same core
defects: execute_push's dirty/ahead-behind branches don't exist (real
surface is rc-0/rc-nonzero/timeout); resume_agent's "empty prompt" case
succeeds, not fails; check.sh's unittest-discover runner would silently
skip bare pytest-style tests; the OR-grep acceptance criterion is
satisfiable by one wrapper alone; render_markdown has an Approach step but
no acceptance criterion. This spec needs the same human revision as the
prior two runs before another /critique pass is worth spending — a fourth
identical re-critique would be pure waste absent an actual SPEC.md edit.

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE. Edits before re-critique: (1) rewrite Approach step 3 + its AC to the real execute_push surface (agent-console.py:2542: TimeoutExpired / rc-0→_invalidate_board / rc-nonzero — no dirty-check or ahead-behind logic exists); (2) replace the "empty prompt" failure case with unknown-sid and the _claude_run_bg error path; (3) split the OR-grep, add a render_markdown AC, require unittest.TestCase style. Verified: zero tests reference resume_agent/set_priority/execute_push. High value — untested git-mutating endpoints on a live launchd service.

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/codequality-agent-console-mutation-coverage/SPEC.md` shows
no commit since the triage above — SPEC.md is byte-identical to the state
that produced this file's prior NOT READY rounds (this is now the 4th
consecutive NOT READY the file itself already called "pure waste absent an
actual SPEC.md edit" for a re-critique with nothing changed). Skipping a
redundant full critic dispatch on unchanged content per token-discipline's
"cheap before expensive" — the three approved triage edits above are the
recovery path, unchanged. This spec's critique intake is spent for this run.

## Re-critique (drain critique intake) — 5th round, still NOT READY

The three triage edits from the round above eventually landed in SPEC.md's
Approach section (execute_push/resume_agent branches corrected, ACs split),
but the Problem section was never updated to match — a new, self-inflicted
contradiction:

1. Problem section (SPEC.md:20-24 at the time) still described execute_push's
   fictional dirty-check/commit-message-assembly/ahead-behind logic even
   though Approach step 3 already had the correct rc-0/rc-nonzero/timeout
   branches — and cited `:2872`, which is unrelated dispatch-conflict code,
   not execute_push at all (conf 90).
2. All four Problem-section line numbers were stale against Approach's
   already-corrected ones (conf 70).

## Triage 2026-07-13 (attended; Steven approved, walk-through item 19)

Verdict: REVISE, applied directly. Fixes landed in SPEC.md:

1. Problem section rewritten to describe execute_push's real branches
   (TimeoutExpired / rc==0 → `_invalidate_board` / rc!=0 → `ok:false` +
   exit code) instead of the fictional dirty-check/ahead-behind claim;
   dropped the wrong `:2872` anchor.
2. All four function/route line numbers re-verified against the current
   `agent-console.py` and refreshed (resume_agent :3134, route :3465;
   set_priority :3037, route :3455; execute_push :2554, dispatched via the
   `"push"` action-kind table at :2633; render_markdown :1211-1256) — also
   caught and fixed a fresh 12-line drift in the Approach section's own
   resume_agent/execute_push anchors that had crept in since the last
   triage.
3. Added a hedge sentence to the Problem section: line numbers are
   snapshots, not a contract, since this spec has drifted between every
   single critique round so far — find functions by name at implementation
   time.

Ready for re-critique.

## Re-critique 2026-07-14 (drain critique intake, gen 3, run c92aedb1ae49f8d3) — READY WITH NITS

Verdict: **READY** (non-blocking nits only). The spec is now accurate
against the current `agent-console/agent-console.py`: all four named
functions (`resume_agent :3136`, `set_priority :3039`, `execute_push
:2556`, `render_markdown :1213`) verified to exist with the exact behavior
Problem/Approach describe; all five prior rounds' findings confirmed still
fixed (execute_push's real rc-0/rc-nonzero/timeout branches, resume_agent's
real failure modes, split non-OR greps, unittest.TestCase requirement,
render_markdown AC present with a runnable mutation-kill anchor). Line
anchors drifted ~2 lines from the last triage, immaterial under the
spec's own "snapshots, not a contract / find by name" hedge. No test
references any of the four functions — the gap is real.

Two sub-critical, non-blocking findings (optional, left for implementation
time rather than blocking breakdown):

1. **resume_agent's success-branch test has an unstated dependency on
   `_claude_json` (conf 62).** Approach step 1 says mock "the process
   boundary (subprocess/spawn) only," but the success path needs a known
   sid to pass the `sid not in sids` guard (`:3139`), and that set comes
   from `_claude_json("agents", "--all")` (`:3137`), not the spawn edge. A
   literal reading leaves the success branch undrivable deterministically.
   Optional fix: add "stub `_claude_json` to return a session list
   containing the test sid" to step 1.
2. **Only resume_agent and render_markdown carry a concrete mutation-kill
   bar; set_priority and execute_push fall back to wrapper-branch
   coverage (conf 55).** execute_push's AC is unusually concrete already
   (stale-then-fresh `_board_cache["ts"]`, `exit:<code>`, timeout message)
   so it's runnable-verifiable regardless; set_priority is the weakest.
   Optional fix: give set_priority a kill bar, e.g. "tests fail if the
   `_git commit` call is stubbed out."

`Breakdown-ready: true` written to SPEC.md's header. Recorded by drain gen 3
(Run-token c92aedb1ae49f8d3); eligible for auto-breakdown (3b) this run.
