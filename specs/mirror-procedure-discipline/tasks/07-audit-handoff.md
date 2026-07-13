# Task 07: Audit handoff's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/handoff/SKILL.md, antigravity/.agents/workflows/handoff.md, tests/mirror-procedure-manifest.txt

## Goal

`handoff`'s Antigravity mirror is read side-by-side against its source
(`.claude/skills/handoff/SKILL.md`) and reconciled per
`.claude/rules/mirror-procedure-discipline.md`'s load-bearing-vs-incidental
classification (read that rule first — task 01 must be done before this one
starts). This session's own handoff-resume `SessionStart` hook work (see
`hooks/handoff-resume/`) is a separate mechanism from this skill and out of
scope here — this task audits only the `/handoff`-writing skill's
Antigravity procedure.

## Touch

Only the three files listed in the header. Do not touch any other skill's
mirror files, `.claude/skills/handoff/` (the source — reconcile the mirror
TO it, never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/handoff/SKILL.md` in full as the source of truth.
3. Read `antigravity/.agents/skills/handoff/SKILL.md` in full, and
   `antigravity/.agents/workflows/handoff.md` if it carries real content
   (check first — it may be a pointer).
4. Compare procedure, not prose: for each step/decision point in the
   source, confirm the mirror expresses the same behavior unless the
   divergence is load-bearing.
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: handoff — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 — evidence: ran, exit=0
- [x] `grep -c "checked: handoff" tests/mirror-procedure-manifest.txt` → ≥1, OR a new manifest line referencing `handoff` — evidence either way — evidence: grep -c → 1 (new `# checked: handoff` comment line appended)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines — evidence: ran full loop, zero FAIL lines (all suites pass)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 — evidence: ran, "lint-ultra-gate: OK — all ultra mentions gated in 4 files", exit=0
