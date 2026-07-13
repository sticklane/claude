# Task 05: Audit factcheck's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/factcheck/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

`factcheck`'s Antigravity mirror (`antigravity/.agents/skills/factcheck/SKILL.md`
— there is no `antigravity/.agents/workflows/factcheck.md`; confirm this is
still true before starting, since the file inventory may have changed) is
read side-by-side against its source (`.claude/skills/factcheck/SKILL.md`)
and reconciled per `.claude/rules/mirror-procedure-discipline.md`'s
load-bearing-vs-incidental classification (read that rule first — task 01
must be done before this one starts).

## Touch

Only the two files listed in the header (or the workflows/ file too, if it
turns out to exist with real content — check first). Do not touch any other
skill's mirror files, `.claude/skills/factcheck/` (the source — reconcile
the mirror TO it, never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/factcheck/SKILL.md` in full as the source of truth.
3. Confirm whether `antigravity/.agents/workflows/factcheck.md` exists; if
   so, read it too. Read `antigravity/.agents/skills/factcheck/SKILL.md` in
   full.
4. Compare procedure, not prose: for each step/decision point in the
   source, confirm the mirror expresses the same behavior unless the
   divergence is load-bearing.
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: factcheck — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] `grep -c "checked: factcheck" tests/mirror-procedure-manifest.txt` → ≥1, OR a new manifest line referencing `factcheck` — evidence either way
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
