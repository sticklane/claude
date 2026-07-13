# Task 11: Audit prose-review's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/prose-review/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

`prose-review`'s Antigravity mirror
(`antigravity/.agents/skills/prose-review/SKILL.md` — there is no
`antigravity/.agents/workflows/prose-review.md`; confirm this is still true
before starting) is read side-by-side against its source
(`.claude/skills/prose-review/SKILL.md` and its `reference.md`) and
reconciled per `.claude/rules/mirror-procedure-discipline.md`'s
load-bearing-vs-incidental classification (read that rule first — task 01
must be done before this one starts).

Note: `.claude/skills/prose-review/reference.md` was substantially edited
earlier in this same session (commit `2d2528a`, six new doctrine additions —
a guidelines-not-rules framing, reader-test extensions, a citation grounding
the conciseness rubric, a named bad-link-text example, an acronym/jargon
convention, and a DORA citation section). Read the CURRENT source, not any
assumption about its prior content — the Antigravity mirror predates that
commit and may now be missing all six additions, which would be the largest
single finding available in this task if so.

## Touch

Only the two files listed in the header (or the workflows/ file too, if it
turns out to exist with real content). Do not touch any other skill's mirror
files, `.claude/skills/prose-review/` (the source — reconcile the mirror TO
it, never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/prose-review/SKILL.md` and its `reference.md` in
   full as the source of truth (note reference.md is loaded on demand by
   the skill, not inline in SKILL.md — read both).
3. Read `antigravity/.agents/skills/prose-review/SKILL.md` in full (and its
   own `reference.md` if one exists there).
4. Compare procedure, not prose: for each step/rubric item/doctrine section
   in the source, confirm the mirror expresses the same content unless the
   divergence is load-bearing. Pay particular attention to whether the six
   commit-`2d2528a` additions (see note above) made it into the mirror.
5. Fix any incidental divergence found — small, targeted edits, or a full
   port of the six additions if they're missing (still counts as "small,
   targeted" per-item, even if there are six of them).
6. Append a manifest line if phrase-expressible, or a
   `# checked: prose-review — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] `grep -c "checked: prose-review" tests/mirror-procedure-manifest.txt` → ≥1, OR a new manifest line referencing `prose-review` — evidence either way
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
