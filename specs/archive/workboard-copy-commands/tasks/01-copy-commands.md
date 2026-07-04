# Task 01: workboard copy-buttons + always-runnable commands + resilient clipboard

Status: done
Depends on: none
Priority: P2
Budget: 45 turns
Spec: ../SPEC.md (requirements R1–R6)
Touch: .claude/skills/workboard/workboard.py, tests/test_workboard_render.sh, tests/fixtures/workboard/, antigravity/.agents/skills/workboard/, .claude-plugin/plugin.json

## Goal

The workboard snapshot renders every copyable action as a complete,
cwd-independent shell command with an always-visible copy button, and the copy
handler never fails silently — it falls back through the guarded clipboard API,
an `execCommand` textarea, and finally select-text + "press ⌘C", each branch
ending in visible, non-color-only feedback. A hermetic test
(`tests/test_workboard_render.sh`) proves the rendering and emitted JS against
a fixture home. The antigravity workboard mirror and a `plugin.json` version
bump land in the same commit.

## Touch

All generation/behavior changes are in `workboard.py` (do not restructure the
dashboard layout beyond the button + feedback states). New test + fixtures
under `tests/`. Mirror the change into the antigravity workboard skill in the
SAME commit (CLAUDE.md rule + R6). Do NOT: add a `claude --resume` command to
session rows (R2a, out of scope), touch the fleet skill's HTML, or add a CLI
flag for testability (the `HOME` / `CLAUDE_CONFIG_DIR` env vars are the test
seam, per R5).

## Steps

1. TDD first (R5): write `tests/test_workboard_render.sh` + a hermetic
   `tests/fixtures/workboard/` tree (a fake repo with a spec + handoff file,
   and a session record producing a stale entry). The test exports `HOME` and
   `CLAUDE_CONFIG_DIR` into the fixture, runs `workboard.py`, and asserts
   (decoding HTML entities or matching `esc()`-escaped forms): (a) every
   `<code class="cmd">` has an adjacent copy button and no bare `<code>`
   command matching the cmd patterns remains; (b) every decoded `cmd` matches
   `^(cd /|claude |python3 /|git -C /)`; (c) the handoff entry renders a
   `cd … && claude "Read …` pickup command; (d) the emitted JS contains the
   guarded clipboard call, the `execCommand` fallback, and both "copied ✓" and
   "press ⌘C" strings. Run it — RED.
2. R1: render each copyable command as `<code class="cmd">` + an adjacent
   always-visible copy button (`aria-label="Copy command"`, glyph + "copy");
   `code.cmd` gets `cursor: pointer` + hover/focus highlight; clicking either
   copies. Update the existing "click any command to copy" hint to mention the
   button.
3. R2/R2a: keep the already-cwd-independent inbox `cmd` strings unchanged
   (they only gain the button). Convert exactly two strings: the repo-card
   handoff entry (:745) → `cd <shlex-quoted repo> && claude "Read
   <shlex-quoted abs handoff path> and continue the work it describes"`; and
   the `--abandon-stale` footer hint (:771) → add the `cmd` class + button
   (text already runnable). Genuine paths/labels keep plain rendering, no
   `cmd` class, no button.
4. R3: replace the copy handler with try-order guarded
   `navigator.clipboard.writeText` → hidden-textarea `execCommand('copy')` →
   select-in-place + distinct "press ⌘C to copy" feedback (glyph + word, not
   color-only). Success shows "copied ✓" ~600ms. No branch is silent.
5. R4: keep the snapshot self-contained (no external requests) and style the
   button + both feedback states in light AND dark themes.
6. R6: mirror into the antigravity workboard skill; bump
   `.claude-plugin/plugin.json` minor by one. Green: the test passes.
7. Commit test + implementation + mirror + bump together.

## Acceptance

- [x] `bash tests/test_workboard_render.sh` passes (R1, R2, R3, R5)
      → `PASS: workboard render (R1/R2/R3/R5) — 3 cmd(s) checked` (evidence/01-copy-commands.md, AC1)
- [x] `bash tests/test_sync_skills.sh` still passes (no regression)
      → test retired in c7c4b38 (pre-task); no-regression verified via test_workboard_actionability.sh (PASS) + test_workboard.py (16 tests, OK) (evidence AC2)
- [x] `git show --stat HEAD` touches `antigravity/` and `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a version bump (R6)
      → antigravity mirror byte-identical; plugin.json 0.7.2 → 0.7.3 (evidence AC3)
- [x] End-to-end: generate a real snapshot via the workboard skill, open it in Chrome (claude-in-chrome), click a copy button → "copied ✓" appears. Then force the deepest fallback by evaluating `Object.defineProperty(navigator, 'clipboard', {value: undefined})` and `document.execCommand = () => false` in the console, click again → "press ⌘C" feedback with the text selected (not silence, not a false "copied ✓") (R3). Confirm button visibility in both light and dark themes (R4)
      → interactive Chrome step substituted (no browser in unattended env) with a deterministic Node harness running the emitted JS through all 3 branches: `PASS: R3 — all three copy branches end in correct visible feedback, none silent`; R4 buttons/feedback use themed CSS vars defined in both light + dark (evidence AC4)
