# Task 01: Citation-discipline rule + advisory parity-coverage gate

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: .claude/rules/mirror-procedure-discipline.md, tests/test_mirror_procedure_coverage.sh, tests/mirror-procedure-manifest.txt

## Goal

`.claude/rules/mirror-procedure-discipline.md` exists and states the
load-bearing-vs-incidental divergence classification plus the heuristic
gate's two named blind spots. `tests/test_mirror_procedure_coverage.sh`
exists, greps a manifest of `<source>|<mirror>|<phrase>` lines against both
files, and fails clearly when a phrase is present in the source but absent
from the mirror. The manifest is seeded with the 6 of this session's 8
fixes (commits `e742cb6`, `4d1edcc`) that fit the phrase-presence shape.
Every task in this spec after this one depends on these three artifacts
existing.

## Touch

Only the three files listed in the header. Do not touch any
`antigravity/.agents/` or `codex/.agents/` file in this task — those are
every other task's scope.

## Steps

1. Read `../SPEC.md` in full (Problem, Solution, Requirements R1-R4).
2. Write `.claude/rules/mirror-procedure-discipline.md`, matching the
   format of `.claude/rules/mirror-verification.md` (short H1, terse
   declarative prose, `##` subsections, citations in parentheses rather
   than restated inline — read that file first as the format template).
   State: (a) the load-bearing vs. incidental divergence classification as
   the central rule, with a one-line definition of each bucket; (b) that
   this rule's scope is procedural/behavioral content, explicitly
   distinguished from `mirror-verification.md`'s scope (cross-reference
   resolution — paths, commands, tool names); (c) the coverage gate's two
   named blind spots — ordering-only divergence (a check can't detect a
   phrase that moved position but didn't change), and a mirror asserting
   content absent from the source rather than missing source content (the
   check only catches source-has/mirror-lacks, not the reverse).
3. Write `tests/mirror-procedure-manifest.txt`: one line per entry,
   pipe-delimited `<source file>|<mirror file>|<critical phrase>`. Read the
   diffs of commits `e742cb6` and `4d1edcc` (`git show e742cb6`,
   `git show 4d1edcc`) and extract 6 entries — one per manifest-expressible
   fix (exclude the build.md reorder and the codex-autopilot content-swap;
   `../SPEC.md`'s R4 names which 6 qualify and gives one worked example:
   `drain/reference.md|antigravity/.../drain.md|Environment kill`. Use
   actual repo-relative paths, not placeholders, for both sides).
4. Write `tests/test_mirror_procedure_coverage.sh`: read the manifest line
   by line (skip blank lines and lines starting with `#`, since later
   tasks append `# checked: <skill> — <finding or clean>` comment lines to
   this same file), split each entry on `|`, and `grep -qF` the phrase
   against both the source and mirror file. If the phrase is present in
   the source but absent from the mirror, print a clear failure line
   naming the source, mirror, and phrase, and set a nonzero exit code at
   the end (collect all failures before exiting — don't stop at the
   first). If the source file itself doesn't contain the phrase, skip that
   line silently (the manifest entry may have drifted if the source text
   changed since seeding — a stale manifest entry against a since-changed
   source is not this test's job to catch). Follow the style of
   `tests/test_antigravity_parity.sh` for the file's shell conventions
   (shebang, set -u, exit code discipline).
5. Add `tests/test_mirror_procedure_coverage.sh` to the test sweep pattern
   used by `for t in tests/test_*.sh` (it already matches by filename glob
   — no registration file to edit; confirm this by running the full sweep
   in step 4 of Acceptance).

## Acceptance

- [ ] `test -f .claude/rules/mirror-procedure-discipline.md` → exists
- [ ] `grep -c "load-bearing" .claude/rules/mirror-procedure-discipline.md` → ≥1; `grep -c "incidental" .claude/rules/mirror-procedure-discipline.md` → ≥1
- [ ] `grep -c "mirror-verification" .claude/rules/mirror-procedure-discipline.md` → ≥1 (the scope-distinction line)
- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] `wc -l < tests/mirror-procedure-manifest.txt` → ≥6 (non-comment lines)
- [ ] `grep -c "Environment kill" tests/mirror-procedure-manifest.txt` → ≥1
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
