Status: in-progress
<!-- plan (task 19):
  RED  — add manifest lines pinning re-derive/next-ranked (source-present,
         codex-absent) → test_mirror_procedure_coverage.sh fails on 2 GAPs.
  GREEN— restore codex tournament clause: 3 angle-suffixes (t1 minimal-diff,
         t2 strict-test-first, t3 re-derive; defines the angles the tie-break
         references), merge-failure fallback (abort → next-ranked survivor),
         no-survivor DEFERRED-beats-failed routing. Test green.
  VERIFY— all tests/test_*.sh green; ultra-gate green; independent verifier.
  Decision (Steven, attended): incidental compression, restore; targeted
  edit per .claude/rules/mirror-procedure-discipline.md, not a rewrite.
-->
Discovered-from: specs/mirror-procedure-discipline/tasks/14-audit-codex-drain.md
Spec: ../SPEC.md
Blocking: no
Priority: P2
Budget: 5 turns
Touch: codex/.agents/skills/drain/SKILL.md, tests/test_mirror_procedure_coverage.sh, specs/mirror-procedure-discipline/tasks/19-audit-codex-drain-tournament-compression.md

# Restore codex-drain's compressed tournament procedure

Decision (Steven, attended, 2026-07-13): **incidental compression, not
intentional Codex style** — restore. Audit verified all three pieces are
genuinely absent from `codex/.agents/skills/drain/SKILL.md` (tournament
clause, ~lines 208–216) and are procedure, not prose; the smoking gun is
codex's tie-break referencing "lowest angle index (t1 before t2)" while
the angles are never defined there.

## Goal

Carry the three dropped tournament decision points from
`.claude/skills/drain/reference.md` (and the antigravity workflow) into
codex-drain's tournament clause, per
`.claude/rules/mirror-procedure-discipline.md` (same steps, same order,
same stated conditions; targeted edit, not a rewrite):

1. The three generate angle-suffixes — minimal-diff / strict-test-first /
   re-derive — that make the three tournament workers non-identical.
2. The merge-failure fallback: on gate failure, abort the merge and move
   to the next-ranked survivor.
3. The no-survivor verdict routing: DEFERRED-beats-failed.

## Acceptance criteria

All four literals are confirmed absent from the codex file today
(grep -c → 0, verified 2026-07-13):

- [x] `grep -c "minimal-diff" codex/.agents/skills/drain/SKILL.md` ≥ 1 — result 1 (t1 angle label)
- [x] `grep -c "strict-test-first" codex/.agents/skills/drain/SKILL.md` ≥ 1 — result 1 (t2 angle label)
- [x] `grep -c "re-derive" codex/.agents/skills/drain/SKILL.md` ≥ 1 — result 1 (t3 angle label)
- [x] `grep -c "next-ranked" codex/.agents/skills/drain/SKILL.md` ≥ 1 — result 1 (merge-failure fallback)
- [x] The tie-break's "angle index" reference now resolves to angles defined in the same clause (no dangling reference — reviewer check) — t1/t2/t3 now defined inline before the "lowest angle index (t1 before t2 before t3)" tie-break
- [x] `tests/test_mirror_procedure_coverage.sh` gains manifest lines pinning the three restored phrases for the codex drain mirror, and `bash tests/test_mirror_procedure_coverage.sh` is green — 4 lines added (re-derive/next-ranked enforce; minimal-diff/strict-test-first advisory), exit 0
- [x] `for t in tests/test_*.sh; do bash "$t"; done` all green — ALL TESTS GREEN; ultra-gate OK
