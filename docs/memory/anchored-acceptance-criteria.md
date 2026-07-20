# Anchored acceptance criteria

When: writing or critiquing a SPEC.md/task acceptance criterion that greps
for prose, or that pins a numeric bound on an existing file.

The 2026-07-11 cost-analysis spec wave lost three critic rounds and one
mid-drain deferral to criteria that were never checked against the files
they gate:

- **Vacuous grep** (three separate specs): `grep -qi 'frontier' SKILL.md`
  and `grep -qi 'worktree root' reference.md` both already matched
  pre-existing, unrelated text — the criterion green-checks a worker that
  writes nothing. Fix pattern: anchor on a NEW distinctive literal phrase
  the requirement mandates verbatim ("hub-economics advisory", "under your
  worktree root"), and run `grep -ci '<phrase>' <every target>` → 0 at
  authoring time; record "phrase absent today, verified <date>" in the
  criterion so the verifier knows it can't pass vacuously.
- **Unsatisfiable bound** (one mid-drain deferral): `wc -l SKILL.md < 500`
  written while the file already stood at 561 lines with a single-file
  Touch — no in-scope way to pass. Check the current value before pinning
  any bound; if the convention is already violated, the criterion belongs
  to a separate remediation task, not this one.
- **Version-bump criteria**: never a pinned literal (a sibling spec bumping
  the same line false-fails it) and never merely "differs from base" (a
  sibling bump false-passes it) — assert the closing task's OWN commit
  modifies the version line:
  `git show <closing-commit> -- <file> | grep -q '^+.*"version"'`.
- **Trivially satisfiable** (the anchoring doctrine's own blind spot): a
  criterion anchored per the three patterns above — a NEW distinctive
  phrase, absent today — still only proves the phrase was _typed_, not that
  the requirement's behavior was built. Anchoring kills criteria that pass
  with NO work; it does not kill criteria that pass with TRIVIAL work. A
  2026-07-19 survey of ~90 criteria across 13 specs found ~40% were
  literal-phrase greps a worker could green-check by writing the searched
  phrase: `specs/critique-findings-loop-closure/tasks/01` greps for the
  words "MECHANICAL"/"JUDGMENT", `specs/rigor-tier/tasks/01` greps for the
  literal `Rigor:`, and `specs/mirror-procedure-discipline` (21 tasks) gates
  almost entirely on a grep-manifest. This is the trivially satisfiable
  criterion, and anchoring alone cannot catch it. Fix pattern: name the
  criterion's depth on the ladder below and carry the deepest feasible
  level; where text-presence is the honest ceiling, annotate it rather than
  letting the grep masquerade as behavioral verification.

Multi-file coverage: when one criterion certifies a port/mirror of several
requirements, anchor EACH ported item's phrase — a single-phrase grep lets
a partial port pass.

## Criterion depth ladder

Name the depth of every acceptance criterion so its gaming surface is visible
at authoring, critique, and verification. Four levels, shallowest first:

- **L0 — text-presence**: a grep or count over prose (`grep -ci`, `wc -l`).
  Proves a phrase is present or a line-count holds; proves nothing about
  behavior.
- **L1 — artifact-structure**: existence, diff-shape, or committed-file
  layout — a file exists, a commit touches the version line, a directory has
  the expected members. Proves structure, not that anything runs.
- **L2 — behavior**: a command that exercises the requirement's behavior — a
  test run, a script execution, a produced-binary invocation — and observes
  the result.
- **L3 — end-to-end**: an eval scenario or user-flow walk that drives the
  whole feature the way a user would.

**Deepest-feasible rule.** Each requirement carries the deepest feasible
criterion. A requirement whose criteria are all L0/L1 carries an explicit
depth-ceiling annotation stating why deeper is infeasible and naming the
behavioral complement — an eval scenario, a manual-pending human read, or a
named verifier judgment instruction. Prose-only artifacts (most of this
toolkit) legitimately bottom out at L0/L1; the annotation legalizes that
ceiling instead of letting a grep pose as behavioral proof.

**Annotation grammar.** One line on (or directly under) the criterion:
`Depth ceiling: <why deeper is infeasible> — behavioral complement is <the
eval scenario / manual-pending human read / named verifier judgment
instruction>.`

**Binding scope** (self-detecting, needing no external list; per
`specs/criterion-depth-ladder` R5, maintainer override 2026-07-19). The
ladder binds any NOT-done spec whose acceptance sections carry the markers it
keys on — a `Depth ceiling:` line or a "verified <date>" anchor note — which
covers all specs authored after this lands plus the specs the already-landed
2026-07-19 sweep annotated. A behavioral requirement whose only green
evidence is L0 text-presence is INCOMPLETE, not PASS, unless a recorded
depth-ceiling annotation exempts it (that exemption is the annotation's whole
purpose). Done or archived work is exempt unconditionally: a pre-ladder
"verified <date>" note predates the ladder and must not re-bind it — such
specs get their ladder levels reported informationally, without flipping the
verdict.
