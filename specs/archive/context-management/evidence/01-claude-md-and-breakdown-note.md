# Verification evidence: task 01 — CLAUDE.md compaction, conventions, memory pointer; breakdown header note

Verdict: PASS
Verified: 2026-07-03, branch `task/01-claude-md-and-breakdown-note`, worktree
`/Users/sjaconette/claude/.claude/worktrees/agent-a3bba23238b5df54e`
Verifier: independent (did not write this code); all commands run from worktree root.

## Acceptance criteria (task file ## Acceptance)

### 1. R1 — Compact instructions section + line budget — ✓
Command:
```
grep -q "^## Compact instructions" CLAUDE.md && test "$(wc -l < CLAUDE.md)" -le 200
```
Exit 0. `wc -l CLAUDE.md` = 68 (≤200).

### 2. R2 conventions — ✓
Command:
```
grep -qi "first 30 lines" CLAUDE.md && grep -qi "table of contents" CLAUDE.md
```
Exit 0. Both bullets present in `## Authoring conventions`, plus the
one-level-deep references bullet ("References stay one level deep:
SKILL.md → reference file, never reference → reference.").

### 3. R3 pointer (CLAUDE.md half) — ✓
Command:
```
grep -q "docs/memory.md" CLAUDE.md
```
Exit 0. Pointer line in the intro paragraph: "Narrow per-topic lessons are
indexed in `docs/memory.md`; check it when a task matches a topic." (Distill
half correctly deferred to task 02, per criterion note.)

### 4. R6 machine-state bullet + breakdown header comment — ✓
Command:
```
grep -qi "single-line" CLAUDE.md && grep -qi "header" .claude/skills/breakdown/SKILL.md
```
Exit 0. CLAUDE.md bullet covers Status, Depends on, Priority (optional;
absent = P2), Budget, post-review-fix-wave Touch, single-line `Key: value`
headers above the first `##`, body sections never orchestrator-parsed.

## Goal constraints

- Compact instructions section ≤10 lines: ✓ — 7 body lines (8 including the
  `##` header), measured with
  `awk '/^## Compact instructions/{flag=1;next}/^## /{flag=0}flag' CLAUDE.md | wc -l` → 7.
  Content matches R1: preserves task-file paths + Status values,
  wave/dispatch state, branch names, acceptance-evidence pointers,
  unresolved review findings; drops first raw tool output and file listings.
- CLAUDE.md ≤200 lines: ✓ — 68 lines.
- Breakdown template comment mirrored identically: ✓ — `git diff main`
  shows the identical one-line HTML comment added in both
  `.claude/skills/breakdown/SKILL.md` and
  `antigravity/.agents/skills/breakdown/SKILL.md`, at the same point in the
  task template (above `Status: pending`):
  `<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line \`Key: value\` headers above the first ## heading; body sections are never parsed by orchestrators. -->`
- Diff scope: ✓ — `git diff main --stat`:
  ```
   .claude/skills/breakdown/SKILL.md             |  1 +
   CLAUDE.md                                     | 21 ++++++++++++++++++++-
   antigravity/.agents/skills/breakdown/SKILL.md |  1 +
   3 files changed, 22 insertions(+), 1 deletion(-)
  ```
  Exactly the three Touch-listed files; no untracked files in `git status`.
- plugin.json unchanged vs main (R9 out of scope): ✓ —
  `git diff main -- .claude-plugin/plugin.json` and
  `git diff main --stat -- .claude-plugin/` both empty.

## Gates

No build/lint/test gates apply to this markdown-only change. The repo's
skill-eval gate (`evals/run.sh`) is defined for skill-behavior changes; the
breakdown edit here is a template comment only, and running evals was not
part of this task's acceptance section — noted, not run.

## Overfitting / scope-creep findings

None. Additions are general prose matching spec R1/R2/R3/R6 substance, not
grep-bait: the compact section, convention bullets, pointer, and
machine-state bullet each carry the full required content rather than just
the grepped phrases. No test files exist for this change to game. The mirror
edit is required by the repo's same-commit mirror convention and is in the
Touch list.

## Verdict

PASS
