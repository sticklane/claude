# Verification: Task 02 — build close-out parity sentence for bare-SPEC runs

Verdict: PASS

## Criterion 1
Command: `grep -qi 'spec-completion review' .claude/skills/build/SKILL.md`
Result: exit 0 (hit).
Match location: line 162 — "SPEC.md (no `tasks/`), additionally run the spec-completion review".

## Criterion 2
Command: `bash evals/lint-ultra-gate.sh`
Output:
```
lint-ultra-gate: OK — all ultra mentions gated in 4 files
```
Exit: 0. PASS.

## Append-only task-file check
Command: `git diff 56a3f28 -- specs/spec-completion-review/tasks/02-build-parity.md`
Output: empty — no diff. The worker has not yet flipped Status/checkboxes; nothing beyond the
allowed set is present (because nothing is present at all). PASS (vacuously satisfies
append-only constraint).

## Scope-creep check
Command: `git diff 56a3f28 --stat` (whole worktree vs base)
Output:
```
 .claude/skills/build/SKILL.md | 7 ++++++-
 1 file changed, 6 insertions(+), 1 deletion(-)
```
Only the file listed in the task's `Touch:` header was modified. `git status --porcelain` shows
no untracked/uncommitted files. No scope creep found (e.g., no antigravity/codex mirror edits,
no plugin.json bump — none required since this SKILL.md is one of the four "real content" files
under the codex overlay per repo CLAUDE.md, but the task's Touch: header only lists the .claude
copy, and mirroring wasn't in this task's scope per its own Touch: list — flagged as an
observation, not a criterion failure, since the task file's Touch is binding and doesn't include
the codex mirror).

## Goal-intent check
Read region: .claude/skills/build/SKILL.md lines 140-166 (close-out review step).
Added sentence (lines 161-166):
> When this /build run's target was a bare SPEC.md (no `tasks/`), additionally run the
> spec-completion review (specs/spec-completion-review) over the run's whole diff through this
> same pre-commit review machinery — a bare-SPEC run has no per-task pass to catch spec-level
> gaps; task-file /build runs are unchanged, their per-task pass already covers them.

- (a) Names the spec-completion review, cites `specs/spec-completion-review`: YES.
- (b) Scopes to bare-SPEC (no tasks/) /build runs: YES — "target was a bare SPEC.md (no `tasks/`)".
- (c) References existing pre-commit review machinery: YES — "through this same pre-commit review
  machinery" (referring to the /code-review invocation described in the preceding paragraph,
  lines 140-160).
- (d) States task-file runs are unchanged: YES — "task-file /build runs are unchanged, their
  per-task pass already covers them."

All four goal-intent sub-requirements confirmed present in the actual file text.

## Gate check
`evals/lint-ultra-gate.sh` is the project's canonical ultra-path gate for this file (build is one
of the four ultra-path skills). Ran above: OK.

## Summary
| Criterion | Command | Result |
|---|---|---|
| 1 | `grep -qi 'spec-completion review' .claude/skills/build/SKILL.md` | PASS (exit 0) |
| 2 | `bash evals/lint-ultra-gate.sh` | PASS ("OK — all ultra mentions gated in 4 files") |
| Task-file append-only | `git diff 56a3f28 -- specs/spec-completion-review/tasks/02-build-parity.md` | PASS (empty diff, not yet edited) |
| Scope | `git diff 56a3f28 --stat` | PASS (only Touch-listed file changed) |
| Goal intent (a-d) | manual read of SKILL.md:140-166 | PASS (all four elements present) |

Overall: PASS.
