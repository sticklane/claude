Status: done
Depends on: none
Priority: P3
Budget: 5 turns
Discovered-from: 05-mirrors-plugin-bump-trim.md
Spec: ../SPEC.md
Touch: codex/.agents/skills/drain/SKILL.md

# Cosmetic inline code span wraps mid-span in codex drain mirror

`codex/.agents/skills/drain/SKILL.md` has an inline code span that wraps
mid-span (e.g. a `git worktree remove` command split across a line break)
in the R1-R4 mirror content task 05 added — renders awkwardly but doesn't
affect the machine-parsed procedure.

## Answers

The prior assessor-authored acceptance criteria were unsatisfiable/
backwards (per `Intake-refused`) and missed a second wrapped span. Fixed
directly instead of re-authoring criteria for a future worker: there were
TWO wrapped instances of the same `git worktree remove <path>` / `git
branch -D <branch>` idiom (line ~251 and line ~288), both reflowed so each
inline code span now sits entirely on one line — confirmed via both a
Python regex scan and `rg -U` (ripgrep multiline mode) that no backtick
now opens on one line and continues into "worktree"/"branch" on the next.

## Acceptance

- [x] ``grep -c '`git worktree remove <path>` then' codex/.agents/skills/drain/SKILL.md``
      → 2 (both instances now intact, single-line spans; was mid-span-wrapped
      before this fix) — verifier PASS (2026-07-16 sweep)
- [x] ``rg -U '`git\n(worktree|branch)' codex/.agents/skills/drain/SKILL.md``
      → no match, exit 1 (confirms no code span still opens on one line and
      continues into "worktree"/"branch" on the next — the exact wrap bug
      this task fixes) — verifier PASS (2026-07-16 sweep)
- [x] `bash evals/lint-skill-size-gate.sh` exits 0 (no regression) — verifier PASS (2026-07-16 sweep)
- [x] `bash tests/test_doc_links.sh` exits 0 (no regression) — verifier PASS (2026-07-16 sweep)
