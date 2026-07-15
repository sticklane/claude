# Task 01: /fleet prints inline, delete reference.md and its viz.py CSS emitter

Status: done
Depends on: none
Priority: P0
Budget: 6 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: .claude/skills/fleet/SKILL.md, .claude/skills/fleet/reference.md, .claude/skills/_shared/viz.py

## Goal

`/fleet` no longer renders an HTML snapshot: `fleet/SKILL.md`'s steps 3-4
("Render", "Present") are replaced with printing one markdown table
(columns `Label | Kind | Status | Elapsed | Snippet`) plus the existing
one-line summary directly in the response. `fleet/reference.md` (the HTML
template) is deleted. `.claude/skills/_shared/viz.py`'s
`_emit_fleet_css` function and `--emit-fleet-css` CLI flag, and any
docstring/comment mentioning fleet CSS generation, are removed — nothing
else in the repo invokes that flag.

## Touch

Exactly the three files listed above. Do not touch `workboard.py` or
`workboard/SKILL.md` (Task 02), any other repo file referencing `/fleet`
(Task 05's sweep), or the antigravity mirror (Task 04).

## Steps

1. Confirm `--emit-fleet-css` has no other caller:
   `git grep -n 'emit-fleet-css\|_emit_fleet_css' -- .claude/ antigravity/ tests/ evals/`
   — every hit should be inside the two files this task and Task 04 edit.
2. Edit `.claude/skills/fleet/SKILL.md`: replace the Render/Present steps
   with printing the inline markdown table plus the one-line summary
   ("3 running · 1 queued · 2 completed · 0 failed — snapshot HH:MM:SS;
   re-run /fleet to refresh"). Rewrite the frontmatter `description` line
   (currently ends "...as a self-contained HTML snapshot with status
   tiles, a timeline, and per-agent detail") to describe the new inline
   markdown-table output — this is the skill's auto-invocation trigger
   surface, not just body prose.
3. Delete `.claude/skills/fleet/reference.md`.
4. In `.claude/skills/_shared/viz.py`, remove `_emit_fleet_css` and the
   `--emit-fleet-css` CLI flag, plus any docstring/comment referencing
   fleet CSS generation.

## Acceptance

- [x] `[ ! -f .claude/skills/fleet/reference.md ]` — file deleted (git rm), verifier confirmed absent.
- [x] `grep -c "self-contained HTML snapshot" .claude/skills/fleet/SKILL.md`
      → 0 — confirmed 0 (frontmatter description rewritten to inline-table output).
- [x] `.claude/skills/fleet/SKILL.md` describes printing a markdown table,
      not rendering/writing HTML — spot-check by reading the Render/
      Present steps after the edit — step 3 now "## 3. Print", emits a
      `Label | Kind | Status | Elapsed | Snippet` table inline; no HTML/file.
- [x] `grep -n "_emit_fleet_css\|--emit-fleet-css" .claude/skills/_shared/viz.py`
      returns no matches — confirmed no matches; `--self-sha256` still runs.
