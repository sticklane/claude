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

Multi-file coverage: when one criterion certifies a port/mirror of several
requirements, anchor EACH ported item's phrase — a single-phrase grep lets
a partial port pass.
