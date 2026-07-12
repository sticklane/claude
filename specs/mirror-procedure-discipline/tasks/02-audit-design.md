# Task 02: Audit design's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/design/SKILL.md, antigravity/.agents/workflows/design.md, tests/mirror-procedure-manifest.txt

## Goal

`design`'s Antigravity mirror (`antigravity/.agents/skills/design/SKILL.md`
and, if it carries real content rather than a pointer,
`antigravity/.agents/workflows/design.md`) is read side-by-side against its
source (`.claude/skills/design/SKILL.md`, plus `reference.md` if the source
skill has one) and reconciled per `.claude/rules/mirror-procedure-discipline.md`'s
load-bearing-vs-incidental classification (read that rule first — task 01
must be done before this one starts). Any found incidental divergence
(missing steps, swapped order, invented or dropped behavior not forced by a
runtime difference) is fixed with a small, targeted edit. A manifest entry
is added for anything fixed that's phrase-expressible; anything fixed that
isn't, or a finding of zero divergence, gets a `# checked: design — <finding
or clean>` comment line appended to `tests/mirror-procedure-manifest.txt`.

## Touch

Only the three files listed in the header. Do not touch any other skill's
mirror files, `.claude/skills/design/` (the source — reconcile the mirror
TO it, never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/design/SKILL.md` in full (and its `reference.md` if
   one exists) as the source of truth.
3. Read `antigravity/.agents/skills/design/SKILL.md` in full, and
   `antigravity/.agents/workflows/design.md` if it carries real content
   (check first — many `workflows/*.md` files are 5-line pointers to the
   `skills/` counterpart; if this one is a pointer, its content doesn't
   need auditing, only the `skills/` file does).
4. Compare procedure, not prose: for each step/decision point in the
   source, confirm the mirror expresses the same behavior (same steps,
   same order, same stated conditions) unless the divergence is load-bearing
   (a real Antigravity mechanism difference — no Stop hook, no
   `disable-model-invocation` equivalent, different launch/dispatch
   primitive, etc.).
5. Fix any incidental divergence found — small, targeted edits matching
   the surrounding file's existing style and terseness. Do not rewrite
   working, correct content for style reasons.
6. For each fix: if it's expressible as a `<source>|<mirror>|<phrase>`
   manifest line (a specific phrase/concept now present in both files that
   wasn't before), append it to `tests/mirror-procedure-manifest.txt`. If
   not expressible that way (e.g. a reorder, or removed-wrong-content), or
   if zero divergence was found, append one line:
   `# checked: design — <one-line summary: what was fixed, or "no
   divergence found">`.
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] `grep -c "checked: design" tests/mirror-procedure-manifest.txt` → ≥1, OR at least one new pipe-delimited manifest line whose source/mirror paths reference `design` — evidence either way
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
