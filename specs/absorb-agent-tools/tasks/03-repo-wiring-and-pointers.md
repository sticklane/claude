# Task 03: repo wiring — AGENTS.md, skill pointers, mirror, plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R6)
Touch: AGENTS.md, .claude/skills/workboard/SKILL.md, antigravity/.agents/skills/workboard/SKILL.md, .claude-plugin/plugin.json

## Goal

The repo knows about its two new components: root `AGENTS.md` Map lists
`agentprof/` and `agent-console/` with one-line roles and its Commands
section carries both `scripts/check.sh` lines (verified by actually
running them); every literal `~/agent-console/agent-console.py` is
replaced with `~/claude/agent-console/agent-console.py` — two occurrences
in `.claude/skills/workboard/SKILL.md`, two body-line occurrences in the
antigravity mirror's workboard SKILL.md (its frontmatter description
carries no path literal — leave it); and `.claude-plugin/plugin.json`
version is bumped because skill text changed.

## Touch

Only the four files in the Touch header. Do NOT edit anything under
`agentprof/` or `agent-console/` (tasks 01/02 own those), and no other
skill files. Per CLAUDE.md conventions the mirror edit and the bump land
in the same commit as the SKILL.md edit.

## Steps

1. Run `bash agentprof/scripts/check.sh` and
   `bash agent-console/scripts/check.sh` — the AGENTS.md Commands lines
   must be verified by running, never written cold.
2. Edit AGENTS.md: Map entries + Commands lines.
3. Replace the path literal in both SKILL.md files (all four body
   occurrences); confirm the antigravity frontmatter needs nothing.
4. Bump `version` in `.claude-plugin/plugin.json`.
5. Run the repo gates; commit once.

## Acceptance

- [x] `grep -c "agentprof/" AGENTS.md` → ≥1 and `grep -c "agent-console/" AGENTS.md` → ≥1
- [x] `grep -rn "~/agent-console/agent-console.py" .claude/skills/ antigravity/ | wc -l` → 0
- [x] `grep -c "~/claude/agent-console/agent-console.py" .claude/skills/workboard/SKILL.md` → 2
- [x] `grep -c "~/claude/agent-console/agent-console.py" antigravity/.agents/skills/workboard/SKILL.md` → 2
- [x] `git diff main -- .claude-plugin/plugin.json | grep -c "version"` → ≥2 (old + new line)
- [x] `for t in tests/test_*.sh; do bash "$t"; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh` → all green

## Progress

- [2026-07-05 /drain] Worker verdict BLOCKED. Done: all four Touch-scoped
  edits complete and individually verified (acceptance 1–5 PASS) on branch
  `task/03-repo-wiring-and-pointers` (commit 69ea7e5, based on main
  592a8cc) — branch PRESERVED, not merged. Remaining: acceptance 6 (full
  gate suite) fails solely on `tests/test_workboard_render.sh`, a
  PRE-EXISTING regression on main (reproduced at b92f98f and at 592a8cc
  with no task edits applied; drain independently reproduced it at
  main~1 before this task dispatched). Root cause:
  `.claude/skills/workboard/workboard.py` renders the actions-script
  command (`bash <tmpdir>/a.sh`) with no adjacent copy button / not
  cwd-independent — outside this task's Touch. See draft stub
  tasks/07-fix-workboard-render-regression.md. Resolution paths: fix the
  regression (draft 07) then re-run gates and merge the preserved
  branch, or human re-scopes acceptance 6.

## Discovered

- [2026-07-05 /drain] tests/test_workboard_render.sh fails on unmodified main (copy button / cwd-independence regression in workboard.py from wcc-01) → RESOLVED attended 2026-07-05 (user-authorized): fix(workboard) commit on main; stub 07 removed
