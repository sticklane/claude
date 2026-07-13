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
   *set_priority's* commit-message line. Approach step 3 (SPEC.md:44-47)
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
