# Verification: specs/criterion-depth-ladder/tasks/01-doctrine-depth-ladder.md

Verdict: PASS

## Scope check

Command: `git diff b243995 --stat -- .`
Output: only `docs/memory/anchored-acceptance-criteria.md | 58 +++++++++++++++++++++++++++++`
(1 file changed, 58 insertions(+), 0 deletions). Matches the task's
`Touch:` header exactly — no other file changed.

Command: `git diff b243995 -- specs/criterion-depth-ladder/tasks/01-doctrine-depth-ladder.md`
Output: empty — the task file is byte-identical to the base commit. The
append-only rule (Status line / checkbox ticks / evidence citations / plan
comment) is trivially satisfied because nothing was touched, but note: the
task's own checkboxes are still unticked and `Status: in-progress` (not
flipped to done) — the worker did not close out the task file even though
the deliverable content is complete and passing. This is a closure gap, not
a criteria violation.

Command: `git status --short` → clean; committed as `01e463f docs: add
criterion depth ladder to anchoring doctrine` on top of `b243995 drain:
criterion-depth-ladder task 01 in-progress`.

## Criterion 1

Command: `grep -ci 'depth ladder' docs/memory/anchored-acceptance-criteria.md`
Result: `1` (≥ 1 required). PASS.

## Criterion 2

Command: `grep -ci 'trivially satisfiable' docs/memory/anchored-acceptance-criteria.md`
Result: `2` (≥ 1 required). PASS.

## Adequacy check (Goal / R1, beyond the two greps)

Read full file post-change and isolated the diff (`git diff b243995 --
docs/memory/anchored-acceptance-criteria.md`, 58 lines added, 0 removed).

(a) Fourth failure pattern present as a genuine bullet ("Trivially
satisfiable (the anchoring doctrine's own blind spot)") with substantive
prose distinguishing "kills criteria that pass with NO work" vs "TRIVIAL
work," and cites all three spec-survey examples named in the task's Step 2
and the spec's Problem section:

- `specs/critique-findings-loop-closure/tasks/01` (MECHANICAL/JUDGMENT grep)
- `specs/rigor-tier/tasks/01` (literal `Rigor:` grep)
- `specs/mirror-procedure-discipline` (21-task grep-manifest)
  All three verbatim, not paraphrased away. Not gamed — the phrase "trivially
  satisfiable" appears twice as a real heading/term inside this substantive
  paragraph, not as a bare inserted string.

(b) `## Criterion depth ladder` section present with:

- L0 text-presence, L1 artifact-structure, L2 behavior, L3 end-to-end — all
  four levels defined with example commands/artifacts per level.
- **Deepest-feasible rule** bullet, worded to match spec R1 ("each
  requirement carries the deepest feasible criterion... explicit
  depth-ceiling annotation stating why deeper is infeasible and naming the
  behavioral complement").
- **Annotation grammar** bullet giving the exact `Depth ceiling: <why> —
behavioral complement is <...>.` template.
- **Binding scope** bullet citing `specs/criterion-depth-ladder R5,
maintainer override 2026-07-19`, stating the self-detecting marker rule
  (`Depth ceiling:` line or "verified <date>" anchor note), the
  binds-post-landing-plus-swept-specs scope, the L0-only-is-INCOMPLETE rule,
  and unconditional exemption for done/archived work with pre-ladder notes
  reported informationally — this tracks R5's decided text closely (not a
  paraphrase that drops the grandfathering clause).

No skill-procedure text was added — the new content is pure doctrine
prose (failure-pattern catalog + ladder definitions), consistent with "this
is the doctrine home the skills cite... no skill-procedure text belongs
here." No `.claude/skills/*` or agent files were touched (confirmed by the
stat diff above).

## Gates

No project-wide build/lint/test gate applies to a markdown-only memory-doc
change; no test suite exists for this file. `git diff b243995 --stat` is
the only relevant mechanical gate and is green (single permitted file only).

## Findings

- Minor process flag (not a criteria failure): the task file itself was
  never updated — `Status:` still reads `in-progress` and both acceptance
  checkboxes remain unticked, despite the underlying deliverable content
  fully satisfying both grep criteria and the Goal's substance. Closing
  this out (flip Status, tick boxes, cite the commit as evidence) is
  outstanding per the task's own append-only convention.
- No scope creep: diff touches exactly one file, the one named in `Touch:`.
