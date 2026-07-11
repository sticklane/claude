# Task 04: end-to-end verification and antigravity mirror sync

Status: done
Depends on: 01, 02, 03
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (final acceptance bullet: end-to-end; solution item 5, antigravity mirror)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, .claude/skills/workboard/reference.md, antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, antigravity/.agents/skills/workboard/reference.md, antigravity/.agents/skills/workboard/SKILL.md

## Goal

The complete feature (Tasks 01-03) is verified end-to-end against a real
session with real spawned sub-agents, and the antigravity mirror at
`antigravity/.agents/skills/workboard/` is brought current with every
change the first three tasks made.

## Important correction to the spec's premise

SPEC.md's solution item 5 states the antigravity mirror "currently has no
antigravity mirror ... confirmed absent from `antigravity/skills/`". That
check looked at the wrong path. The mirror exists and is current as of this
writing at `antigravity/.agents/skills/workboard/` (`workboard.py`,
`test_workboard.py`, `reference.md`, `SKILL.md`). Per CLAUDE.md's mirroring
convention and per the spec's own fallback wording ("or, if that mirror
genuinely does not exist yet..."), this task follows the branch that
applies: **update the existing mirror**, not create a new one.

Per docs/memory/workboard-mirror-verbatim.md: workboard's two `.py` files
(`workboard.py`, `test_workboard.py`) are byte-identical across the two
trees — check them with `diff`. `reference.md` and `SKILL.md` are
paraphrased ports, not byte-identical — check them with a content-coverage
grep for the new concepts/identifiers, never a `diff`.

**Known pre-existing exception** (found during breakdown, unrelated to this
feature): `test_workboard.py`'s top-of-file run comment names its own tree's
directory (`.claude/skills/workboard` vs. `.agents/skills/workboard`), so
that one line legitimately differs between the two trees today and always
will. Mirror everything else byte-for-byte; exclude only that comment line
from the identical-mirror check (see the adjusted acceptance command below)
rather than trying to make it match or deleting it.

## Touch

The `.claude/skills/workboard/` paths listed here are read-only in this
task except for whatever the E2E pass reveals needs a genuine bug fix (keep
any such fix small and call it out explicitly in the commit). The primary
work is mirroring 01-03's already-landed changes into
`antigravity/.agents/skills/workboard/`.

## Steps

1. Find a real qualifying session on this machine: this very toolkit repo's
   own Claude Code sessions routinely spawn scout/critic/implementation
   sub-agents (this spec's own /breakdown session did, for instance), so a
   real non-empty `spawn_tree` should already exist without needing to
   manufacture a new live nested-agent spawn. Run
   `python3 .claude/skills/workboard/workboard.py --json` (default scan
   roots) and look for a session whose `spawn_tree` (Task 02's field) is
   non-empty.
2. If no qualifying real session is found in step 1's scan roots, construct
   one minimal fixture session dir on disk (not a new live agent spawn) with
   a real-shaped `subagents/agent-<id>.jsonl` + `.meta.json` pair, run
   workboard against that fixture repo, and use it as the E2E evidence
   instead.
3. Render the HTML dashboard (or call `render_html()` directly) for the
   qualifying session and confirm the collapsible tree node appears with
   the correct status once the underlying agent(s) completed. Capture the
   confirmation as a passing test or a saved snippet of the rendered
   fragment — whichever is more durable as regression evidence.
4. Copy forward every change 01-03 made to `.claude/skills/workboard/
   workboard.py` and `test_workboard.py` verbatim into
   `antigravity/.agents/skills/workboard/workboard.py` and
   `test_workboard.py` (byte-identical mirror, whole-file copy is simplest —
   e.g. `cp`). After copying `test_workboard.py`, restore its own tree's
   run-path comment line (the one pre-existing, tree-specific line noted
   above) if the copy overwrote it — every other line must match.
5. Update `antigravity/.agents/skills/workboard/reference.md` and
   `SKILL.md` with paraphrased coverage of the new spawn-tree
   concepts/fields (`extract_agent_tree`, `scan_session_spawns`,
   `spawn_tree`, the fleet-style status chip reuse) — wording may differ
   from the `.claude/` versions, per the paraphrased-port convention.
6. Run the antigravity mirror's own test suite to confirm it's still green
   after the copy.

## Acceptance

- [x] End-to-end: a real (or, per step 2, fixture-backed) session with at least one Agent tool_use renders as a spawn-tree node with correct status in `render_html()`'s output — cite the specific test name or manual check performed here once done. Evidence: live manual check — ran `workboard.py --json` over default scan roots (real toolkit sessions, no fixture needed) and passed the output through `render_html()`; the rendered HTML carried 42 `class="spawn-tree"` collapsible `<details>` nodes and status chips across all three states (`s-running`×569, `s-completed`×186, `s-failed`×1), confirming real spawned sub-agents render as tree nodes with correct status. Regression backstop: existing test `test_render_spawn_tree_indented_chipped_with_failed_branch` (passes in both trees).
- [x] `diff .claude/skills/workboard/workboard.py antigravity/.agents/skills/workboard/workboard.py` → no output.
- [x] `diff <(grep -v "unittest discover -s" .claude/skills/workboard/test_workboard.py) <(grep -v "unittest discover -s" antigravity/.agents/skills/workboard/test_workboard.py)` → no output (excludes only the one known tree-specific run-path comment line; every other line must match).
- [x] `grep -l "spawn_tree\|extract_agent_tree\|scan_session_spawns" antigravity/.agents/skills/workboard/reference.md` → file listed (content-coverage check, not diff — `reference.md` is field-level docs, expected to carry the code identifiers verbatim).
- [x] `grep -il "spawn.tree" antigravity/.agents/skills/workboard/SKILL.md` → file listed (case-insensitive prose-phrase check, not an identifier grep — `SKILL.md` is a paraphrased user-facing port and is not expected to carry code tokens like `spawn_tree` verbatim).
- [x] `python3 -m unittest discover -s antigravity/.agents/skills/workboard -p "test_workboard.py" -v 2>&1 | tail -5` → reports `OK`.
