# Task 01: CLAUDE.md compaction, conventions, memory pointer; breakdown header note

Status: pending
Depends on: ../../model-agnostic/tasks/02-core-tier-language.md, ../../review-fixes/tasks/04-worker-prompt-resolution.md
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R2-conventions, R3-pointer, R6; R9 note)

## Goal

CLAUDE.md gains four additions: a `## Compact instructions` section (≤10
lines) steering what compaction preserves (task-file paths + Status
values, wave/dispatch state, branch names, acceptance-evidence pointers,
unresolved review findings) and drops first (raw tool output, file
listings); authoring-convention bullets for post-compact skill survival
(execution-critical contracts in a SKILL.md's first 30 lines — bodies
truncate on compact, descriptions reload; reference files >100 lines
open with a table of contents; references stay one level deep); the
always-on memory pointer line ("narrow per-topic lessons are indexed in
`docs/memory.md`; check it when a task matches a topic"); and the
machine-state bullet (fields skills read programmatically — Status,
Depends on, Priority (optional, absent = P2), Budget, and
post-review-fix-wave Touch — are single-line
`Key: value` headers above the file's first `##`; body sections are for
humans and workers, never orchestrator parsing). /breakdown's task
template gains a one-line comment stating that same header convention,
mirrored into the antigravity breakdown skill. CLAUDE.md stays ≤200
lines. Do NOT bump plugin.json — the combined bump (R9) is owned by
global task 99 in specs/review-fixes.

## Touch

- `CLAUDE.md` — Cross-spec: also edited by chaining-antipatterns,
  model-agnostic — see specs/QUEUE.md
- `.claude/skills/breakdown/SKILL.md` (template comment only) —
  Cross-spec: also edited by chaining-antipatterns, review-fixes — see
  specs/QUEUE.md
- `antigravity/.agents/skills/breakdown/SKILL.md` (mirror of the
  template comment, per the repo's same-commit mirror convention)

## Steps

1. Add `## Compact instructions` (≤10 lines) to CLAUDE.md with the
   preserve/drop lists from R1.
2. Extend the authoring conventions with the three R2 bullets
   (first-30-lines contract, table-of-contents rule for >100-line
   reference files, one-level-deep references).
3. Add the R3 pointer line for `docs/memory.md` (one line, always-on).
4. Add the R6 machine-state-in-headers bullet. Note the Touch
   relocation itself is out of scope (code-review fix wave owns it).
5. Add the one-line header-convention comment to the task template in
   `.claude/skills/breakdown/SKILL.md`; mirror it into
   `antigravity/.agents/skills/breakdown/SKILL.md`.
6. Confirm `wc -l CLAUDE.md` ≤ 200 (currently 41 — keep additions tight).

## Acceptance

- [ ] `grep -q "^## Compact instructions" CLAUDE.md && test "$(wc -l < CLAUDE.md)" -le 200` (R1)
- [ ] `grep -qi "first 30 lines" CLAUDE.md && grep -qi "table of contents" CLAUDE.md` (R2 conventions)
- [ ] `grep -q "docs/memory.md" CLAUDE.md` (R3, CLAUDE.md half — distill half lives in task 02)
- [ ] `grep -qi "single-line" CLAUDE.md && grep -qi "header" .claude/skills/breakdown/SKILL.md` (R6)
