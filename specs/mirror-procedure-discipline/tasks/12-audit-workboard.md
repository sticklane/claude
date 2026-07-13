# Task 12: Audit workboard's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/workboard/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

`workboard`'s Antigravity mirror
(`antigravity/.agents/skills/workboard/SKILL.md` — there is no
`antigravity/.agents/workflows/workboard.md`; confirm this is still true
before starting) is read side-by-side against its source
(`.claude/skills/workboard/SKILL.md`) and reconciled per
`.claude/rules/mirror-procedure-discipline.md`'s load-bearing-vs-incidental
classification (read that rule first — task 01 must be done before this one
starts).

Read `docs/memory/workboard-mirror-verbatim.md` before writing any diff:
only workboard's two bundled `.py` files are byte-identical across trees —
the `SKILL.md` prose itself is a paraphrased port like every other skill,
so this audit's scope (procedure content) applies normally to `SKILL.md`,
but do NOT expect or force byte-identical prose, and do not touch the `.py`
files (out of this spec's scope per its Out of scope section — they're
`codequality-antigravity-content-parity`'s territory).

## Touch

Only the two files listed in the header (or the workflows/ file too, if it
turns out to exist with real content). Do not touch `.py` files under
either tree, any other skill's mirror files, `.claude/skills/workboard/`
(the source — reconcile the mirror TO it, never edit the source), or the
rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification, and `docs/memory/workboard-mirror-verbatim.md`
   for the byte-identical-`.py`-only caveat.
2. Read `.claude/skills/workboard/SKILL.md` in full as the source of truth.
3. Read `antigravity/.agents/skills/workboard/SKILL.md` in full.
4. Compare procedure, not prose: for each step/decision point in the
   source, confirm the mirror expresses the same behavior unless the
   divergence is load-bearing.
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: workboard — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 — evidence: ran, coverage exit=0 (2 seeded workboard phrase lines both present in mirror)
- [x] `grep -c "checked: workboard" tests/mirror-procedure-manifest.txt` → ≥1, OR a new manifest line referencing `workboard` — evidence either way — evidence: grep returns 1 (plus 2 seeded `<source>|<mirror>|<phrase>` workboard lines)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines — evidence: ran full suite, no FAIL lines
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 — evidence: "lint-ultra-gate: OK — all ultra mentions gated in 4 files", exit=0
