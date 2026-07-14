# Task 04: Mirror the workboard/viz.py static-HTML removal into antigravity

Status: pending
Depends on: none
Priority: P0
Budget: 15 turns
Spec: ../SPEC.md (requirement R6)
Touch: antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/SKILL.md, antigravity/.agents/skills/workboard/test_workboard.py, antigravity/.agents/skills/_shared/viz.py

## Goal

The antigravity mirror gets the identical treatment Tasks 01-03 apply to
the `.claude` leg, run independently against its own copies (this mirror
is not a copy of the `.claude` files at merge time — its own dangling
`fleet/reference.md` citations are a separate cleanup, not automatically
fixed by editing the `.claude` leg). `/fleet` itself was never mirrored to
antigravity and stays that way — this task does not create
`antigravity/.agents/skills/fleet/`.

## Touch

Exactly the four files listed above. Do not create
`antigravity/.agents/skills/fleet/`. Do not touch `.claude/` (Tasks 01-03
own it) or `antigravity/README.md`'s not-ported row or
`antigravity/AGENTS.md`'s "scale the fleet" line (both explicitly
exempted — Task 05 confirms they're left untouched, this task doesn't
edit them).

## Steps

1. Confirm `antigravity/.agents/skills/fleet/` does not exist and this
   task does not create it.
2. `antigravity/.agents/skills/_shared/viz.py`: remove its own
   `_emit_fleet_css` function and `--emit-fleet-css` CLI flag, plus any
   docstring/comment mentioning fleet CSS generation (mirrors Task 01's
   viz.py edit).
3. `antigravity/.agents/skills/workboard/workboard.py`: run the same
   reachability-check procedure Task 02 used (save the script from
   ../SPEC.md's "Reachability check script" section to
   `/tmp/orphan_check.py`, run it before deleting anything — expect
   `clean` — then delete `render_html`, `build_actions_script`, the
   `--out`/`--actions-out` flags and the `main()` HTML-writing branch,
   then iteratively delete whatever the script reports orphaned until it
   prints `clean` again). Confirmed today this file has the same
   orphaned-function calls at the same line numbers as the `.claude`
   copy, but verify against the actual file — don't assume identical
   content.
4. `antigravity/.agents/skills/workboard/SKILL.md`: remove its "Fallback
   (machines without agent-console)" bullet (mirrors Task 02's SKILL.md
   edit).
5. `antigravity/.agents/skills/workboard/test_workboard.py`: delete every
   test method calling `render_html` or any other function/constant just
   deleted in step 3 (mirrors Task 03's test cleanup) — confirmed today to
   have the same orphaned-function calls at the same line numbers as the
   `.claude` copy.
6. Fix this mirror's own dangling `fleet/reference.md` citations —
   scattered across this tree's `workboard.py`, `test_workboard.py`,
   `reference.md`, and `SKILL.md` comments/docstrings citing fleet's
   glyph+word status-chip convention: either drop the file citation and
   describe the chip convention inline, or point at
   `.claude/skills/fleet/SKILL.md` if it still documents the convention
   there. The chip convention itself is unchanged — this is a citation
   fix, not a rewrite of workboard's chip-rendering logic. (Citations
   inside functions step 3 already deleted are removed along with those
   functions — no separate pass needed for those.)

## Acceptance

- [ ] `[ ! -d antigravity/.agents/skills/fleet ]`
- [ ] `grep -n "_emit_fleet_css\|--emit-fleet-css" antigravity/.agents/skills/_shared/viz.py`
      returns no matches.
- [ ] `grep -n "render_html\|build_actions_script\|--out\|--actions-out" antigravity/.agents/skills/workboard/workboard.py`
      returns no matches.
- [ ] `grep -n "^TEMPLATE = " antigravity/.agents/skills/workboard/workboard.py`
      returns no match.
- [ ] Save the reachability script from ../SPEC.md to `/tmp/orphan_check.py`
      and run `python3 /tmp/orphan_check.py antigravity/.agents/skills/workboard/workboard.py`
      — prints `clean` (exit 0).
- [ ] `grep -n "Fallback (machines without agent-console)" antigravity/.agents/skills/workboard/SKILL.md`
      returns no match.
- [ ] `python3 antigravity/.agents/skills/workboard/workboard.py --json` still runs and produces valid JSON.
- [ ] `python3 -m unittest discover -s antigravity/.agents/skills/workboard` exits 0.
- [ ] `git grep -rn 'fleet/reference\.md' -- antigravity/` returns no matches.
