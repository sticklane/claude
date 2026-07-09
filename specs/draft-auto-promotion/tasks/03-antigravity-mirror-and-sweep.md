# Task 03: Antigravity mirror, plugin bump, and full-spec sweep

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions / ## Decisions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01, 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R6, plus the R7 antigravity clause)
Touch: antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

The Antigravity drain workflow carries the equivalent stub-intake
contract (paraphrased port — docs/memory/workboard-mirror-verbatim.md;
adapt the screen script step to Antigravity's shape, e.g. run the same
script via its shell step, since the script itself ships in
`.claude/skills/drain/`), its manual-promotion sentence is revised per
R7, and `.claude-plugin/plugin.json` is bumped one patch level from this
task's own base commit. Then the whole spec's acceptance list is re-run
as a closing sweep.

## Steps

1. Read the landed diffs of tasks 01–02 and `../SPEC.md` R6/R7.
2. Port the contract into `antigravity/.agents/workflows/drain.md`;
   revise its "only a human (or …)" promotion sentence.
3. Bump plugin.json base-relative (siblings bump it repeatedly — never
   a hard-coded literal; cite base and current values).
4. Closing sweep: run every automatable checkbox in `../SPEC.md`'s
   Acceptance criteria, including the two-tree
   `rg -Uqi …` sweep, and cite each result in the evidence file.

## Acceptance

- [ ] `grep -qi "stub intake" antigravity/.agents/workflows/drain.md` → match (content-coverage, not byte-diff)
- [ ] `rg -Uqi "only a human (promotes|edits)|only a human \(or|Promotion is manual|promoted manually|only a human\s+(promotes|edits)" .claude/skills/ antigravity/.agents/` → exit 1, no matches (the spec's R7 sweep, both trees)
- [ ] plugin.json version differs from `git show <this task's base commit>:.claude-plugin/plugin.json` (cite both values)
- [ ] Every automatable checkbox in `../SPEC.md` Acceptance criteria → pass, cited individually in the evidence file
