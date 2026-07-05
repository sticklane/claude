# Task 03: repo wiring — AGENTS.md, skill pointers, mirror, plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
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

- [ ] `grep -c "agentprof/" AGENTS.md` → ≥1 and `grep -c "agent-console/" AGENTS.md` → ≥1
- [ ] `grep -rn "~/agent-console/agent-console.py" .claude/skills/ antigravity/ | wc -l` → 0
- [ ] `grep -c "~/claude/agent-console/agent-console.py" .claude/skills/workboard/SKILL.md` → 2
- [ ] `grep -c "~/claude/agent-console/agent-console.py" antigravity/.agents/skills/workboard/SKILL.md` → 2
- [ ] `git diff main -- .claude-plugin/plugin.json | grep -c "version"` → ≥2 (old + new line)
- [ ] `for t in tests/test_*.sh; do bash "$t"; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh` → all green
