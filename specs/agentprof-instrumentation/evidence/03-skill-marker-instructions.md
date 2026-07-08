# Verification: 03-skill-marker-instructions

Verdict: PASS

## Criteria

1. `grep -c 'agentprof:role=' .claude/skills/drain/SKILL.md` → 5. ✓
2. `grep -c 'agentprof:stage=' .claude/skills/drain/SKILL.md` → 5, and
   `grep -c 'agentprof:stage=' .claude/skills/build/SKILL.md` → 5. ✓ (5, 5)
3. `grep -c 'agentprof:role=' antigravity/.agents/workflows/drain.md` → 5,
   `grep -c 'agentprof:stage=' antigravity/.agents/workflows/drain.md` → 5,
   `grep -c 'agentprof:stage=' antigravity/.agents/workflows/build.md` → 5. ✓ (5, 5, 5)
4. `git diff main -- .claude-plugin/plugin.json | grep '"version"'` → shows
   `-  "version": "0.8.20",` / `+  "version": "0.8.21",`. ✓ (also confirmed
   via `git diff HEAD~1` per the literal acceptance text — same result,
   HEAD~1 == base commit 05d9061).
5. `bash evals/lint-ultra-gate.sh` → `lint-ultra-gate: OK — all ultra
   mentions gated in 4 files`, exit 0. ✓

## Semantic checks

- drain role markers: literals `worker-attempt1` (SKILL.md:233, step 2
  dispatch, prose explicitly states it covers "both the single-worker
  launch and the concurrent group-throughput launch"), `worker-relaunch`
  (SKILL.md:288, step 3 relaunch site), `worker-tournament-t1/-t2/-t3`
  (SKILL.md:300-302, step 3 tournament entrant sites). All 5 confirmed at
  sensible call sites — matches task's PLAN block exactly.
- drain stage markers: `inventory` (## 1, line 45), `dispatch` (## 2, line
  101), `collect-verdict` (## 3, line 246), `baton-pass` (## 3a, line 379),
  `batch-interview` (## 4, line 464). No 3b/auto-breakdown marker present.
  Matches spec.
- build stage markers: `load` (## 0, line 14), `plan` (## 1, line 43),
  `implement` (## 2, line 57), `verify` (## 3, line 70), `close-out` (## 4,
  line 96). Matches spec.
- antigravity mirrors: drain.md carries all 5 role literals (verbatim,
  paraphrased surrounding prose) at steps 2/2/3(x3), and all 5 stage
  literals verbatim at steps 1/2/3/baton-pass-subsection/5. build.md
  carries all 5 stage literals verbatim at steps 1-5. Prose is paraphrased
  as expected/allowed; marker literals are exact.

## Scope / append-only check

`git diff main -- specs/agentprof-instrumentation/tasks/03-skill-marker-instructions.md`
shows only a 16-line `<!-- PLAN (delete at close-out): ... -->` comment
block inserted after the `Touch:` header line. Status line unchanged
(`Status: in-progress`, same as base — task started already in-progress
and worker did not flip it or check acceptance boxes). Goal/Steps/
Touch/Budget/Acceptance text bytes are unchanged (only the PLAN block was
added). This is within the allowed append-only set.

`git diff main --stat` shows exactly the 5 Touch-listed files plus the
task file itself changed — no scope creep:
- .claude-plugin/plugin.json
- .claude/skills/build/SKILL.md
- .claude/skills/drain/SKILL.md
- antigravity/.agents/workflows/build.md
- antigravity/.agents/workflows/drain.md
- specs/agentprof-instrumentation/tasks/03-skill-marker-instructions.md

## Gate

`bash evals/lint-ultra-gate.sh` (also required by the repo's ultra-path
convention for drain/build) passed, exit 0, as noted in criterion 5.

## Notes

- Acceptance checkboxes in the task file were left unticked and no
  evidence-citation lines were added by the worker; this verification was
  performed independently against the literal acceptance commands and
  passed regardless.
