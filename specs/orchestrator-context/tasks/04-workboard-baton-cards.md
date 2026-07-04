# Task 04: Workboard surfaces DRAIN-BATON.md files

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: 01
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirement R6)
Touch: .claude/skills/workboard/, antigravity/.agents/skills/workboard/

## Goal

The workboard scanner globs `specs/*/DRAIN-BATON.md` alongside HANDOFF.md
and renders a baton card showing generation number, the relaunch command,
and any needs-attention/deferred section — with baton-appropriate card
text, not the handoff card's "resume in a fresh session then delete"
prompt. This is the third sanctioned scanner change (after workboard-live
R2a and unblock-next-steps R5).

## Touch

Whatever scanner/renderer files live under `.claude/skills/workboard/`
(SKILL.md, reference.md, and any scan script it ships). Must NOT touch:
drain/autopilot/parallel/breakdown skills, runtimes/, plugin.json.

## Steps

1. Locate the workboard scanner's HANDOFF.md glob (scout first).
2. Write the failing check: a fixture `DRAIN-BATON.md` (generation 3, a
   relaunch command line, a needs-attention section) in a temp scanned
   repo does not appear on the rendered board.
3. Add the baton glob + extraction (generation, command, needs-attention)
   and the baton card text.
4. Re-run the fixture check; assert the card renders all three fields.

## Acceptance

- [ ] A fixture `DRAIN-BATON.md` in a scanned repo appears on the workboard with generation + relaunch command + needs-attention content (scanner unit test or rendered-HTML grep)
- [ ] The baton card text differs from the handoff card's resume-then-delete prompt (grep the renderer/template)
- [ ] Existing HANDOFF.md cards still render (fixture regression check)
