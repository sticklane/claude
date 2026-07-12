# Verification: specs/drain-forward-progress/tasks/01-intake-contract.md

Verdict: PASS

## Automated acceptance commands (run from worktree root)

1. `grep -qi 'Intake-refused' .claude/skills/drain/SKILL.md && grep -qi 'Intake-refused' .claude/skills/drain/reference.md`
   → both greps succeeded (exit 0). PASS.
   Hits: SKILL.md lines 481, 484, 486, 565; reference.md lines 1011, 1046, 1067, 1075, 1077, 1080, 1082, 1088, 1091, 1097, 1111, 1121, 1143.

2. `grep -qi 'may not return ACTIONABLE-without-criteria' .claude/skills/drain/reference.md`
   → matched (exit 0), reference.md:1025 — "the assessor **may not return
   ACTIONABLE-without-criteria**". PASS.

3. `grep -c '2026-07-11' .claude/skills/drain/reference.md`
   → output `7` (≥ 1 required). PASS.

4. `bash evals/lint-ultra-gate.sh`
   → output: `lint-ultra-gate: OK — all ultra mentions gated in 4 files`, exit 0. PASS.

## Manual criterion verification

**R1 (Intake-refused line contract).** reference.md:1091-1117 defines
`Intake-refused: <screen|assess|gate> — <one-line reason> (<ISO date>)`,
states placement "on the line immediately after `Status:`" (line 1093-1094),
states it is "drain-written queue state" that "a dispatched worker never
writes or edits" (1105-1107), and states the lifecycle: "A later PASS or
gate-confirmed OBSOLETE Act write CLEARS any prior `Intake-refused:` line in
the same commit... the identical strip-in-the-promotion-commit clause that
already governs `## Original report`... extended to this line" (1110-1114).
SKILL.md's exit checklist section 6 (lines 559-567) quotes the
`Intake-refused:` line per refused stub: "each refused stub (screen-refused,
assess-refused, or gate-failed) with its `Intake-refused: <screen|assess|gate>
— <reason> (<date>)` line quoted verbatim". PASS — all sub-elements present.

**R3 (assessor must-author contract).** reference.md:1017-1046 names exactly
three outcomes — ACTIONABLE, DECISION-SHAPED, OBSOLETE. ACTIONABLE requires
authored Goal + criteria + `Touch:` + `Budget:` and states "the assessor may
not return ACTIONABLE-without-criteria" (1025). DECISION-SHAPED "names the
decision" which becomes the R1 reason line when no defensible default exists
(1032-1035). OBSOLETE "cites the closing evidence", which becomes the R1
`gate` line if unconfirmed (1037-1040). PASS.

**R4 (worked examples + lifecycle).** reference.md:1125-1144, under heading
"R4 — worked authoring examples (2026-07-11)", cites all three stubs:
`cache-reprime-visibility/tasks/05-*` (1131), `agentprof-attribution-gaps/
tasks/07-*` (1134), `agentprof-attribution-gaps/tasks/08-*` (1137) as worked
ACTIONABLE-authoring examples. Clear-on-promotion lifecycle is (re)stated at
1110-1117 and referenced again at 1142-1144. PASS.

## Scope check

`git diff 36d93bf --stat`:
```
 .claude/skills/drain/SKILL.md                                   | 38 +++--
 .claude/skills/drain/reference.md                               | 133 ++++++++++++++----
 specs/drain-forward-progress/tasks/01-intake-contract.md         | 18 +++
 3 files changed, 152 insertions(+), 37 deletions(-)
```
Only the two Touch-listed skill files plus the task file itself changed — no
antigravity/codex mirror files, no plugin.json bump, no unrelated files. No
out-of-Touch product change found.

"ultra" sanity check: `lint-ultra-gate.sh` passed with "OK — all ultra
mentions gated in 4 files", i.e. no new case-insensitive "ultra" mention was
introduced outside the gated window. No manual override was needed since the
gate itself is the authoritative check per the task's own acceptance
criterion 4.

## Append-only task-file check

`git diff 36d93bf -- specs/drain-forward-progress/tasks/01-intake-contract.md`
shows only a `<!-- PLAN (worker, task 01): ... -->` HTML comment block
inserted between the header fields and `## Goal`. No Goal/Steps/Touch/Budget/
acceptance criteria text was altered; Status remains `in-progress`
(unchanged) and no checkboxes were ticked. This is within the allowed
append-only set (plan comment block) per the task file's own header comment.
No violation.

## Notes (non-blocking)

- Acceptance checkboxes in the task file remain unticked (`- [ ]`) and
  Status remains `in-progress` despite all 4 commands and manual criteria
  passing — the task appears not yet formally closed out, but this is a
  process/status observation, not an acceptance-criterion failure; the
  criteria themselves are satisfied by the current file contents.
