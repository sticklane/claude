Status: done
Promotion-ready: true
Promoted-by-run: bc1c30ae8ac43971
Discovered-from: specs/mirror-procedure-discipline/tasks/14-audit-codex-drain.md
Spec: ../SPEC.md
Depends on: 01
Priority: P2
Budget: 7 turns
Touch: antigravity/.agents/workflows/drain.md, tests/mirror-procedure-manifest.txt

## Goal

Port commit `d35fc9e`'s baton loop-back gate to `antigravity/.agents/workflows/drain.md`.
That commit changed the Claude Code drain source's step 3 closing line and
step 3a's opening to force the baton-trigger check after every recorded
verdict, and task 13/14 this run already ported the equivalent fix into
`codex/.agents/skills/drain/SKILL.md`. `antigravity/.agents/workflows/drain.md`
still carries the pre-fix discretionary phrasing ("loop while anything is
dispatchable" / "At each safe boundary") and has not received the same fix.
Port the intent, not verbatim source prose — this repo's own
`.claude/rules/mirror-procedure-discipline.md` governs load-bearing vs.
incidental divergence, and Antigravity's own step numbering (its
auto-breakdown equivalent is "4a", not "3b") is a load-bearing difference to
preserve.

## Touch

Only the two files listed in the header. Do not touch
`.claude/skills/drain/` (SKILL.md or reference.md) — the source, reconcile
the mirror TO it, never edit it — any other skill's mirror files, or the
rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read commit `d35fc9e`'s diff (`git show d35fc9e -- .claude/skills/drain/SKILL.md`)
   to see exactly what changed in the Claude Code source's step 3/3a.
3. Read `antigravity/.agents/workflows/drain.md`'s current step-3/3a-equivalent
   section in full.
4. Restructure the mirror so the baton-trigger check ("evaluate the
   relaunch trigger") is forced after every recorded verdict, not left as a
   discretionary "at each safe boundary" choice — matching the mandatory
   phrasing already ported into `codex/.agents/skills/drain/SKILL.md` this
   run, adapted to Antigravity's own step-numbering convention.
5. Append a manifest line: `.claude/skills/drain/SKILL.md|antigravity/.agents/workflows/drain.md|after EVERY recorded verdict`
6. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `grep -q "after EVERY recorded verdict" antigravity/.agents/workflows/drain.md` → exit 0 (verified: match count=1)
- [x] `! grep -q "At each safe boundary" antigravity/.agents/workflows/drain.md` → exit 0 (old discretionary phrasing gone; count=0)
- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (verified: no output, exit 0)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines (verified per-file: all 15 test_*.sh pass, zero FAIL)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 (verified: "OK — all ultra mentions gated in 4 files")
