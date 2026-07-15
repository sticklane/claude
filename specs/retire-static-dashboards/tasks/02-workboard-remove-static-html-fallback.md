# Task 02: Remove workboard's static-HTML fallback (code + doc)

Status: in-progress
Depends on: none
Priority: P0
Budget: 11 turns
Spec: ../SPEC.md (requirements R4, R5)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/SKILL.md

## Goal

`workboard.py`'s entire non-`--json` output path is deleted: `render_html`,
`build_actions_script`, the `--out`/`--actions-out` CLI flags, and the
`main()` branch that writes both the HTML file and its `.actions.sh`
companion. Every function and module-level constant whose only reference
path leads into that deleted branch is deleted too (illustrative,
not-exhaustive starting list of ~27 functions plus `TEMPLATE`,
`STATE_BADGE`, `INBOX_CATEGORIES`, `FILTER_CATEGORIES`,
`_AGENT_CHIP_GLYPH`, `_NO_UNBLOCK_CHIP`, `_MODEL_DATE_RE` — verify with
the reachability check, don't hand-count). `--json` is unaffected.
`workboard/SKILL.md` no longer documents a static-HTML fallback: when the
live server can't start, `/workboard` reports the failure and what to
check, it does not degrade to a file.

## Touch

Exactly the two files listed above. Do not touch `agent-console.py` (out
of scope — untouched by this spec), tests (Task 03), or the antigravity
mirror (Task 04).

## Steps

1. Save the spec's "Reachability check script" (../SPEC.md, the
   `## Reachability check script` section) to `/tmp/orphan_check.py`.
2. Run it once BEFORE any deletion: `python3 /tmp/orphan_check.py
.claude/skills/workboard/workboard.py` — expect `clean` (everything is
   still reachable through `render_html` pre-edit; this is expected, not
   a sign there's nothing to delete).
3. Delete `render_html`, `build_actions_script`, the `--out`/
   `--actions-out` CLI flags, and the `main()` branch writing the HTML
   file and its `.actions.sh` companion.
4. Re-run `python3 /tmp/orphan_check.py .claude/skills/workboard/workboard.py`
   — it will report `ORPHANED: [...]` naming every function/constant now
   unreachable. Delete each named item, then re-run. Repeat until it
   prints `clean`. Do not stop at a hardcoded name list (this spec's own
   history under-enumerated this exact orphan set twice before) — trust
   the script's output each round.
5. Edit `.claude/skills/workboard/SKILL.md`: remove the "Fallback
   (machines without agent-console)" bullet. State instead that when the
   live server genuinely cannot start, `/workboard` reports the startup
   error and what to check (Python availability, port conflict,
   `SKILLS_DASHBOARD_PORT`/`_HOST`).
6. Delete the module-level section comment above `_AGENT_CHIP_GLYPH`
   ("Spawn-tree rendering (SPEC.md R6/R7). Reuses /fleet's status-chip
   convention exactly (fleet/reference.md:29-30,181): ..."), lines
   2245-2247. This is a between-defs comment, not inside any function
   body, so the reachability check's node deletion in steps 3-4 does not
   remove it automatically — but `_AGENT_CHIP_GLYPH` and the whole
   spawn-tree/chip section it heads (`_agent_chip`, `_spawn_nodes_html`,
   `_spawn_tree_html`, `_agent_time_html`) are themselves in R4's
   orphaned set and are deleted by steps 3-4. The comment describes code
   that no longer exists once that deletion lands, so it goes with the
   section it heads — this is a stray-comment cleanup, not a citation
   reword; do not keep and reword it.
7. Confirm `--json` still works: `python3 .claude/skills/workboard/workboard.py --json`.

## Acceptance

- [ ] `grep -n "render_html\|build_actions_script\|--out\|--actions-out" .claude/skills/workboard/workboard.py`
      returns no matches.
- [ ] `grep -n "^TEMPLATE = " .claude/skills/workboard/workboard.py` returns
      no match.
- [ ] Save the reachability script from ../SPEC.md to `/tmp/orphan_check.py`
      and run `python3 /tmp/orphan_check.py .claude/skills/workboard/workboard.py`
      — prints `clean` (exit 0).
- [ ] `grep -n "Fallback (machines without agent-console)" .claude/skills/workboard/SKILL.md`
      returns no match.
- [ ] `git grep -c 'fleet/reference\.md' .claude/skills/workboard/workboard.py`
      → 0 (the orphaned section-comment citation, not caught by the
      reachability check since it's a comment, not a node).
- [ ] `python3 .claude/skills/workboard/workboard.py --json` still runs and
      produces valid JSON.
