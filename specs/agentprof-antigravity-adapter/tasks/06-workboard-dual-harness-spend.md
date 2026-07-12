# Task 06: `workboard.py` dual-harness spend (`compute_antigravity_spend` + `merge_spend`)

Status: in-progress
Depends on: 05
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (Solution item 5; R4)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, .claude-plugin/plugin.json

## Goal

`workboard.py` (both the original at `.claude/skills/workboard/
workboard.py` and its byte-identical mirror at `antigravity/.agents/skills/
workboard/workboard.py`) gains `compute_antigravity_spend(antigravity_dir,
cascade_ids)` — structurally parallel to the existing `compute_spend`
(same subprocess/timeout/fail-soft shape, shelling out to `agentprof
antigravity -o summary --antigravity-dir <dir> --days 3650`), filtering
rows by `row["session"] in cascade_ids` — and a `merge_spend(claude_spend,
antigravity_spend)` helper whose return shape is a drop-in replacement for
what `compute_spend` returns today, so `render_spend_section`
(`workboard.py:1381-1410`) needs no changes. Both mirrors change in the
same commit, per this repo's CLAUDE.md mirror-parity convention.

## Touch

Both `workboard.py` copies and both `test_workboard.py` copies, making the
identical edit in each (they are byte-identical today — keep them that
way). Do not modify `render_spend_section` itself, `scan_antigravity()`,
or `compute_spend`'s existing Claude-only behavior — this task adds a
sibling function and a merge helper, it does not change either existing
one's contract. Do not touch any Go code (Task 05, already done) — this
task only shells out to the binary it produces.

## Steps

1. Write the failing tests first in `test_workboard.py` (add the same
   tests to both mirror copies), following the existing `make_agentprof_stub`
   mock pattern used for `TestSpend` (`workboard.py:1275-1396`'s test
   class):
   - `compute_antigravity_spend`: a fabricated `agentprof antigravity -o
     summary` stdout (mocked subprocess via the stub, not a real binary)
     whose `session` value IS a member of the passed `cascade_ids`
     contributes a nonzero amount to the returned spend — proving the
     id-set plumbing works (this is the id-space bug R4 exists to fix:
     filtering by the Claude-only `session_ids` would silently zero this
     out).
   - `merge_spend`: given a Claude spend dict and an Antigravity spend
     dict, `by_model` is the concatenation of both lists RE-SORTED by
     `(-cost_microusd, model)` (not left as two separately-sorted blocks);
     `by_session` is the union of both dicts (no key collision possible —
     cascade ids and Claude session ids are different UUID spaces);
     top-level `available` is `claude_available OR antigravity_available`;
     when exactly one harness fails, the corresponding
     `claude_available`/`claude_reason` or
     `antigravity_available`/`antigravity_reason` keys are set without
     touching the working harness's `by_model`/`by_session` rows.
   - Independent-degrade case: a broken Antigravity call (subprocess
     failure) does not blank out `by_model`/`by_session` rows the Claude
     call already populated, and vice versa.
2. Confirm the new tests fail (no implementation yet).
3. Implement `compute_antigravity_spend` and `merge_spend` in
   `.claude/skills/workboard/workboard.py`, then apply the identical edit
   to `antigravity/.agents/skills/workboard/workboard.py`.
4. Wire the new dashboard's `"spend"` key to `merge_spend(compute_spend(...),
   compute_antigravity_spend(...))` at the existing call site
   (`workboard.py:1479`, one line below `scan_antigravity()`'s call at
   `workboard.py:1462` — reuse its already-computed `antigravity` list for
   `cascade_ids = {c["id"] for c in antigravity}`), in both mirror copies.
5. Get tests green in both copies.
6. Bump `version` in `.claude-plugin/plugin.json` (currently `0.8.39`) —
   this task changes `.claude/skills/workboard/workboard.py` behavior, and
   CLAUDE.md's authoring conventions require a version bump whenever a
   skill's behavior changes.

## Acceptance

- [ ] `diff .claude/skills/workboard/workboard.py antigravity/.agents/skills/workboard/workboard.py` → no output (mirrors stay byte-identical)
- [ ] `diff .claude/skills/workboard/test_workboard.py antigravity/.agents/skills/workboard/test_workboard.py` → no output
- [ ] `python3 -m pytest .claude/skills/workboard/test_workboard.py -q` → passes, including the new `compute_antigravity_spend`/`merge_spend` cases
- [ ] `python3 -m pytest antigravity/.agents/skills/workboard/test_workboard.py -q` → passes, same cases
- [ ] `git show HEAD:.claude-plugin/plugin.json | grep version` → shows a version greater than the value at this task's base commit (`git show <base-commit>:.claude-plugin/plugin.json | grep version`)
