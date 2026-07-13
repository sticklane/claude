# Verification: 03-ship-gate

Verdict: PASS (5/5 checkable criteria pass; 1 criterion manual/deferred as specified)

## Per-criterion

1. Antigravity mirror content-coverage
   Command: `grep -qiE '2k tokens' antigravity/.agents/workflows/drain.md && grep -qiE 'TTL|cache' antigravity/.agents/workflows/drain.md`
   Result: PASS — both greps exit 0. Spot-checked matches: line 178 "≤ 2k tokens", line 251 "capped at ≤ 2k tokens", lines 284-296 TTL/cache wake-economics paragraph, line 483 `max(2, 6 − W)` dual trigger, line 338 merge-step "MUST NOT (wake economics)", lines 174/197/296/380 Pro-class/frontier session-model note. All 5 mandated contracts present in paraphrased form (not byte-identical to `.claude/skills/drain/*`).

2. Gate script
   Command: `bash evals/lint-ultra-gate.sh`
   Result: PASS — output: `lint-ultra-gate: OK — all ultra mentions gated in 4 files`.

3. Plugin manifest validation
   Command: `claude plugin validate .`
   Result: PASS — output: `Validating marketplace manifest: .../.claude-plugin/marketplace.json` / `✔ Validation passed`.

4. Plugin version bump commit
   Command: `git log --oneline -- .claude-plugin/plugin.json` (worktree)
   Result: PASS — top commit `0b38a03 chore: bump plugin version 0.8.33 -> 0.8.34 (drain-wake-cost dw/03)`. Diff confirms `"version": "0.8.33"` -> `"0.8.34"` in `.claude-plugin/plugin.json`. Message names the spec slug (`drain-wake-cost`) and body cites "wake-economics contracts, dual baton trigger, verdict cap".

5. Evals drain scenario updated for dual trigger
   File: `evals/drain/01-rolling-window/setup.sh` (comment block, lines 10-14):
   > "Dual baton trigger: with Parallel-window: 2 the size-adaptive baton budget is max(2, 6-W) = max(2, 4) = 4 recorded verdicts, so this 2-task (2-verdict) run must complete within a SINGLE generation — no baton pass, no relaunch. assert.sh's check 5 enforces exactly that (no DRAIN-BATON.md ever written, clean lease/baton end state), exercising the dual trigger's threshold."

   File: `evals/drain/01-rolling-window/assert.sh` — new "Check 5 (dual baton trigger)" block (lines 113-124):
   ```
   if git log --diff-filter=A --format=%H -- specs/demo/DRAIN-BATON.md | grep -q .; then
     fail "a DRAIN-BATON.md was written (baton fired) though max(2,6-2)=4 > 2 verdicts — dual trigger mis-applied"
   fi
   [ -e specs/demo/DRAIN-BATON.md ] && fail "DRAIN-BATON.md left in tree after queue drained"
   [ -e specs/demo/DRAIN-OWNER.md ] && fail "DRAIN-OWNER.md lease not released after queue drained"
   ```
   `bash -n` on both scripts (full worktree paths): exit clean, no output — PASS.
   Result: PASS.

6. MANUAL — live /drain run over a 2-task demo spec, hub verdicts ≤2k tokens, no task-body reads after dispatch.
   Result: MANUAL — deferred to a human pass, per the task's own note (/drain is `disable-model-invocation`; unattended workers cannot run it). Not treated as failing or blocking.

## Append-only task-file discipline

`git diff 67ad9c5 -- specs/drain-wake-cost/tasks/03-ship-gate.md` (includes working-tree uncommitted edit) shows exactly one hunk: a `<!-- PLAN (dw/03-ship-gate) ... -->` HTML comment block inserted after the header fields, before `## Goal`. No edits to Goal/Steps/Touch/Budget/Acceptance text. Status line unchanged (`Status: in-progress`) — consistent with instructions (worker flips it after verifier reports). Checkboxes remain unticked `[ ]` in all 6 Acceptance items (worker has not yet ticked them, no over-claiming).

## Touch-list conformance

`git diff 67ad9c5..HEAD --name-only` → exactly 4 files: `.claude-plugin/plugin.json`, `antigravity/.agents/workflows/drain.md`, `evals/drain/01-rolling-window/assert.sh`, `evals/drain/01-rolling-window/setup.sh`. Task file edit is uncommitted (working tree only, plan-block only, see above). No commits touch `.claude/skills/drain/*` or `.claude/rules/*` — confirmed via `git diff 67ad9c5..HEAD --name-only -- .claude/skills/drain .claude/rules` (empty output). Matches the task's Touch line (`antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json, evals/`) with no scope creep.

## Diff size sanity (no scope creep)

```
.claude-plugin/plugin.json              |  2 +-
evals/drain/01-rolling-window/assert.sh | 15 ++++++++++++++-
evals/drain/01-rolling-window/setup.sh  |  6 ++++++
```
(antigravity/.agents/workflows/drain.md diff not shown in full — it's a substantial prose port, consistent with Step 2's mandate to port 5 contracts into an existing 500+ line file; spot-checked content above, no unrelated edits detected via targeted greps.)

## Notes / environment caveat

Some Bash tool invocations in this session were transiently denied by the harness's "don't ask mode" permission layer for reasons unrelated to command content (retrying the identical command succeeded); all criteria were eventually exercised directly (not read-only "looks right" judgments) and evidence above reflects actual command output.

## Overall verdict: PASS
