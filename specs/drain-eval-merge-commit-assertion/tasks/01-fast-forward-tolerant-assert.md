# Task 01: Fast-forward-tolerant landing identification in assert.sh

Status: done
Depends on: none
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: evals/drain/01-rolling-window/assert.sh, specs/drain-rolling-window/evidence/06-drain-eval-scenario.md

## Goal

`evals/drain/01-rolling-window/assert.sh` identifies each task's landing by
its `Status:` done-flip (matched against the full landed commit range, from
fork-point/prior landing through the done-flip commit), not by the presence
of a merge commit. The merge-count/barrier check, the Touch-enforcement
check, and the final done-but-unlanded loop all work correctly whether a
given landing was a real merge or a silent git fast-forward.

## Touch

Do not touch `.claude/skills/drain/SKILL.md` or `reference.md` — production
merge behavior is confirmed correct and out of scope (see spec's Problem
section: production doesn't force `--no-ff` either, and shouldn't need to).
Do not touch `evals/run.sh` or any other eval scenario.

## Steps

1. Read the current `evals/drain/01-rolling-window/assert.sh` in full —
   note its three merge-commit-dependent checks (merge-count/barrier,
   Touch-enforcement, done-but-unlanded loop).
2. Build hand-crafted git fixtures directly (scratch dir, not via a real
   `/drain` session) for each acceptance scenario below, run `assert.sh`
   against each, and confirm the CURRENT (unfixed) script's behavior first
   — establish which fixtures currently fail incorrectly (red), so the fix
   has a real before/after.
3. Rewrite `assert.sh`'s landing identification: for each task file, find
   its done-flip commit (the commit where `Status:` becomes `done`), and
   derive the landed range as fork-point-or-prior-landing → done-flip
   commit. Use this range (not merge-commit presence) to feed all three
   checks:
   - merge-count/barrier check: count distinct done-flip landings; a
     barrier is one commit flipping ≥2 task files' Status at once.
   - Touch-enforcement check: diff the FULL landed range (not just the
     done-flip commit) against the task's declared Touch list.
   - done-but-unlanded loop: a task is "landed" if its done-flip commit
     exists in `main`'s history, fast-forwarded or not.
4. Re-run all fixtures from step 2 against the rewritten script; confirm
   each now produces the correct pass/fail per the acceptance criteria.
5. Update `specs/drain-rolling-window/evidence/06-drain-eval-scenario.md`
   to describe the new mechanism and cite the fixture runs from step 4,
   replacing the stale "2 merge commits" claim.

## Acceptance

- [x] Fixture A (task 01 fast-forwards, task 02 real merge) → `assert.sh` passes; all three checks correctly recognize task 01's landing — verifier reproduced: exit 0, `2 rolling-window landings` (evidence/01-fast-forward-tolerant-assert.md)
- [x] Fixture B (both tasks real merges) → `assert.sh` passes (no regression) — verifier reproduced: exit 0 (evidence/01-...md)
- [x] Fixture C (task 01 fast-forwards; its done-flip commit itself also touches a file outside its Touch list) → `assert.sh` fails, naming the Touch violation — verifier reproduced: exit 1, `task 01 landing changed src/gamma.sh, outside its Touch [src/alpha.sh]`
- [x] Fixture C' (task 01 fast-forwards across TWO commits: an earlier commit with an out-of-Touch edit, then a separate later done-flip-only commit) → `assert.sh` fails, naming the Touch violation from the earlier commit — proves the Touch check diffs the full landed range, not just the done-flip commit — verifier reproduced: exit 1, same gamma.sh message from the earlier commit
- [x] Fixture D (one fast-forward commit flips two task files' Status at once — a barrier, not a rolling-window landing) → `assert.sh` fails the barrier check — verifier reproduced: exit 1, `landing <sha> flips 2 task files at once (all-in-one barrier …)`
- [x] Fixture E (both tasks fast-forward, zero merge commits anywhere in history) → `assert.sh` passes — proves no hidden merge-count floor remains — verifier reproduced: exit 0; confirmed no residual `--merges` floor in assert.sh
- [x] `bash evals/drain/01-rolling-window/assert.sh` run against all 6 fixtures above produces the documented pass/fail in a single session's log — full matrix (red pre-fix, green post-fix) recorded in specs/drain-rolling-window/evidence/06-drain-eval-scenario.md; builder at scratchpad/build_fixtures.sh; all 6 also confirmed under macOS bash 3.2
- [x] `specs/drain-rolling-window/evidence/06-drain-eval-scenario.md` updated per step 5 — appended fast-forward-tolerant mechanism section + fixture matrix, superseding the stale "2 merge commits" claim
- [ ] Optional: one full `bash evals/run.sh drain` end-to-end run passes — SKIPPED (optional per spec/dispatch; ~25-min headless model spend; hand-built fixtures are the primary acceptance gate per R3)

## Next stage

No further tasks in this spec.
