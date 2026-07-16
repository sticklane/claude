# Task 04: antigravity mirror + version bump (closing)

Status: in-progress
Depends on: 01, 02, 03
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/workflows/evals.md, .claude-plugin/plugin.json, specs/trajectory-evals/evidence/

<!-- plan (worker, task 04)
1. DONE confirm tasks 01-03 Status: done
2. Investigate Antigravity headless transcript: runtimes/antigravity.md
   Headless (L148-151) — no --json/-o flag, prose/markdown to stdout, only
   a brain/<uuid> artifact, NOT a locatable turn-by-turn JSONL transcript.
   => carve-out path. Write evidence file + non-EVAL_TRANSCRIPT pointer in
   antigravity/.agents/workflows/evals.md (keep grep A false so exactly one
   acceptance branch is true).
3. Re-check LIVE plugin.json version immediately before bump; +1 patch.
4. bash evals/lint-ultra-gate.sh exits 0.
Commit incrementally; verifier before close.
-->

## Goal

`antigravity/.agents/workflows/evals.md` receives the equivalent
`EVAL_TRANSCRIPT` documentation from task 03, or — if Agent Manager runs
expose no transcript file — a reviewed carve-out recorded as evidence,
never a silent skip. `.claude-plugin/plugin.json`'s version is bumped.
This is the closing task: verify tasks 01-03 landed cleanly before
bumping the version.

## Touch

Do not re-touch `.claude/skills/evals/SKILL.md`, `reference.md`, or
`codex/.agents/skills/evals/SKILL.md` — those are task 03's, already
landed. Do not touch `evals/run.sh` (task 01) or `evals/breakdown/`
(task 02).

## Steps

1. Confirm tasks 01-03 are `Status: done` before proceeding.
2. Investigate whether Antigravity's Agent Manager runs produce a
   locatable transcript file the way `claude -p --output-format
stream-json` does. If yes: add the equivalent `EVAL_TRANSCRIPT`
   documentation to `antigravity/.agents/workflows/evals.md`, mirroring
   task 03's `.claude` leg. If no (or genuinely undeterminable from this
   repo alone): write
   `specs/trajectory-evals/evidence/antigravity-transcript-carveout.md`
   recording what was checked and why the carve-out is correct, and
   leave `antigravity/.agents/workflows/evals.md` unedited except a
   pointer to that evidence file — never a silent skip with no trace.
3. Re-check the live `.claude-plugin/plugin.json` version immediately
   before bumping (it drifts fast in this repo from concurrent merges —
   don't trust an earlier round's snapshot). Bump the patch version by
   one.
4. Run `bash evals/lint-ultra-gate.sh` — this spec doesn't touch an
   ultra-path skill directly, but confirm it still exits 0 as a
   sanity check.

## Acceptance

- [ ] `grep -q "EVAL_TRANSCRIPT" antigravity/.agents/workflows/evals.md`
      OR `test -f specs/trajectory-evals/evidence/antigravity-transcript-carveout.md`
      (exactly one of these two must be true — a carve-out with no
      evidence file, or an evidence file with no carve-out rationale
      inside it, both fail this check in spirit even if the grep alone
      can't distinguish; read the evidence file's content if using the
      carve-out path)
- [ ] `git show HEAD~1:.claude-plugin/plugin.json | grep -o '"version": "[^"]*"'`
      differs from the current file's `"version"` value, and the current
      value is a one-patch-level increment above it (never a decrease).
      `HEAD~1` is the commit immediately before your own version-bump
      commit.
- [ ] `bash evals/lint-ultra-gate.sh` exits 0
