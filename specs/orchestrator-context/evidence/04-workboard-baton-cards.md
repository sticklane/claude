# Verification: Task 04 — Workboard surfaces DRAIN-BATON.md files

Verdict: **PASS** (verified inline; worker had no Task tool to spawn a separate verifier)

## Criterion 1 — fixture DRAIN-BATON.md appears with generation + relaunch command + needs-attention content
- Scanner unit tests: `python3 -m unittest discover -s .claude/skills/workboard`
  → `Ran 16 tests ... OK`. `TestScanBatons` asserts `scan_batons` extracts
  `generation==3`, `command` containing `claude -p` / `/drain specs/demo`, and
  `needs_attention` containing "auth provider".
- End-to-end rendered HTML: real `workboard.py . --out out.html` over a temp git
  repo with `specs/demo/DRAIN-BATON.md` produced a card reading
  `drain baton · generation 3 parked in specs/demo/DRAIN-BATON.md`, the escaped
  command `claude -p "/drain specs/demo (generation 4, baton: ...)"`, and
  `needs attention: - 05-e deferred: which auth provider should the login flow use?`.
- ✓ PASS

## Criterion 2 — baton card text differs from handoff resume-then-delete prompt
- `TestRenderBatons.test_baton_card_text_differs_from_handoff_resume_then_delete`
  asserts the rendered baton HTML does NOT contain
  "resume it in a fresh session, then delete" and DOES contain "relaunch".
- Source: renderer line for the baton reads "relaunch to continue the queue
  (drain self-manages; the final generation deletes it)"; the handoff inbox
  string "resume it in a fresh session, then delete the file" is unchanged and
  distinct. Grep of the baton `<p class="baton">` element in the e2e HTML found
  0 occurrences of the handoff phrase.
- ✓ PASS

## Criterion 3 — existing HANDOFF.md cards still render (regression)
- `TestBatonInFullRender.test_baton_and_handoff_both_render_on_the_board`
  renders a repo with both a baton and a HANDOFF.md and asserts both
  `DRAIN-BATON.md` and `HANDOFF.md` appear.
- E2e HTML retained `⚑ handoff: <code>HANDOFF.md</code> — Parked feature work`.
  All 11 pre-existing workboard tests still pass.
- ✓ PASS

## Scope / mirror checks
- Touched only `.claude/skills/workboard/` (workboard.py, test_workboard.py,
  reference.md) and the `antigravity/.agents/skills/workboard/` mirror (same
  three files) + this task file + evidence. No drain/autopilot/parallel/
  breakdown skills, no runtimes/, no plugin.json.
- Antigravity mirror kept byte-identical to `.claude/` source (all three files
  were identical at base); mirror test suite also `Ran 16 tests ... OK`.

## Gates
- No `scripts/check.sh` in this repo. The workboard unittest suite is the gate:
  green in both trees. Not an ultra-path skill, so `evals/lint-ultra-gate.sh`
  does not apply.

Verdict: **PASS** — all 3 criteria verified, mirror in sync, no scope creep.
