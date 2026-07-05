# Task 04: End-to-end verification, antigravity mirror, version bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01, 02, 03
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (end-to-end acceptance; repo mirror + version conventions)
Touch: /Users/sjaconette/claude/antigravity/.agents/skills/workboard/workboard.py, /Users/sjaconette/claude/antigravity/.agents/skills/workboard/test_workboard.py, /Users/sjaconette/claude/.claude-plugin/plugin.json

## Goal

The spec's end-to-end criterion is proven on this machine, the antigravity workboard port carries the same behavior (byte-identical copies — the port was byte-identical before this spec and must stay so; the `_shared/` viz module already exists there), and `plugin.json`'s version is bumped one patch level per the repo's "bump on skill behavior change" convention. This is the closing task: it changes no toolkit skill code.

## Touch

Only the two antigravity mirror files and plugin.json. Do NOT edit `.claude/skills/workboard/*` (tasks 01–03 own it; if the mirror can't be byte-identical because of a port difference, that's a DEFERRED question, not an edit), `.claude/skills/_shared/`, or `antigravity/.agents/skills/_shared/` (already mirrored at 0.8.4 — verify, don't rewrite).

## Steps

1. Run the spec's end-to-end check: `python3 .claude/skills/workboard/workboard.py --out /tmp/wb-e2e.html`; assert the HTML (a) contains ≥1 dependency-graph `<svg` and (b) marks sessions active consistent with `claude agents --json` (diff active sids).
2. Copy `.claude/skills/workboard/workboard.py` and `test_workboard.py` over the antigravity port copies; confirm `antigravity/.agents/skills/_shared/viz.py` is still byte-identical to `.claude/skills/_shared/viz.py`.
3. Run the mirrored tests from the antigravity tree.
4. Bump `version` in `.claude-plugin/plugin.json` by one patch level (read the current value first; it was 0.8.4 when this task was written) and run `claude plugin validate .`.

## Acceptance

- [ ] `python3 /Users/sjaconette/claude/.claude/skills/workboard/workboard.py --out /tmp/wb-e2e.html` → exit 0; `grep -c '<svg' /tmp/wb-e2e.html` ≥ 1; active sids in the HTML match `claude agents --json` (show the diff)
- [ ] `diff /Users/sjaconette/claude/.claude/skills/workboard/workboard.py /Users/sjaconette/claude/antigravity/.agents/skills/workboard/workboard.py` → empty, and same for `test_workboard.py`
- [ ] `python3 -m pytest /Users/sjaconette/claude/antigravity/.agents/skills/workboard/test_workboard.py -q` → all pass
- [ ] `claude plugin validate /Users/sjaconette/claude` → passes, and `grep '"version"' /Users/sjaconette/claude/.claude-plugin/plugin.json` shows a patch bump over the value on main at branch time
