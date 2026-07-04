# Workboard: commands that actually copy

## Problem

The workboard dashboard renders commands as bare `<code>` with a
body-level click-to-copy handler
(`.claude/skills/workboard/workboard.py:902-906`, hint at :917). Three
things fail for Steven (interview 2026-07-03): (1) clicking often copies
nothing — the snapshot is viewed in contexts where `navigator.clipboard`
is denied and the `execCommand` fallback fails silently; (2) nothing
signals that a `<code>` is clickable; (3) some copyable text is not a
runnable command. Note the inbox suggested-action `cmd` strings are
*already* cwd-independent (`cd <quoted-repo> && claude …` at :513/:536,
`git -C <repo> push` at :561, `python3 <abs-script> --abandon` at :572) —
they need only the copy-button treatment, not rewriting. Two copyable
strings are the real content problems: the repo-card handoff entry (:745),
which renders a bare repo-*relative* path (`h["path"]` set from
`f.relative_to(repo)` at :267) with no command wrapper; and the
antigravity-footer `python3 <SCRIPT> --abandon-stale` (:771), which is a
complete command but rendered as bare `<code>` outside the `cmd`
class, so it would miss the copy-button treatment unless explicitly
covered.

## Solution

Fix generation and behavior in `workboard.py` only: normalize every
copyable action to a complete, cwd-independent shell command at render
time; give each one an explicit copy button; replace the silent clipboard
chain with one that always ends in visible feedback (worst case:
select-the-text + "press ⌘C"). The template stays self-contained and
theme-aware per the skill's existing constraints (reference lines 45-48:
glyph + word, never color alone).

## Requirements

- R1: Every copyable command is rendered as a `<code class="cmd">` plus
  an adjacent always-visible copy button (`aria-label="Copy command"`,
  glyph + the word "copy"); `code.cmd` gets `cursor: pointer` and a
  hover/focus highlight. Clicking either the button or the code copies.
  The existing "click any command to copy" hint text (currently at :917)
  stays and is updated to mention the button.
- R2: Every rendered `code.cmd` is executable verbatim in a fresh
  terminal with `~` as cwd. The inbox commands already satisfy this —
  keep their text unchanged (they gain only the R1 button). Two
  conversions:
  - The repo-card handoff entry at :745 becomes a runnable pickup
    command. The absolute handoff path is `Path(r["path"]) / h["path"]`
    where `r["path"]` is the repo's absolute path (:749) and `h["path"]`
    is the repo-relative handoff path (:267). Render, `shlex.quote`ing
    both parts:
    `cd <quoted-repo> && claude "Read <quoted-abs-handoff-path> and
    continue the work it describes"` as `code.cmd` with a copy button.
  - The `python3 <SCRIPT> --abandon-stale` hint at :771 gains the `cmd`
    class and a copy button (its text is already runnable — do not
    change it).
  Any string that is genuinely a path/label and not a command keeps
  plain rendering with NO `cmd` class and NO copy button.
- R2a: No new command categories are added — session rows get no
  `claude --resume` command (out of scope); only the two strings above
  are converted.
- R3: The copy handler tries, in order: `navigator.clipboard.writeText`
  (guarded by `navigator.clipboard &&`); a hidden-textarea
  `document.execCommand('copy')` fallback; and if both fail (rejected
  promise, thrown error, or `false` return) it selects the command text
  in-place and shows a distinct "press ⌘C to copy" feedback. Success
  shows "copied ✓" for ~600ms as today. Failure feedback is visually
  distinct and not color-only (glyph + word). No path is silent — every
  branch ends in visible feedback.
- R4: The snapshot remains fully self-contained (no external requests)
  and theme-aware in both light and dark; the button and feedback states
  are styled in both themes.
- R5: A test script `tests/test_workboard_render.sh` runs
  `workboard.py` against a hermetic fixture tree under
  `tests/fixtures/workboard/` by exporting `HOME` and `CLAUDE_CONFIG_DIR`
  to point into the fixture (workboard.py reads sessions from
  `CLAUDE_CONFIG_DIR` at :582 and antigravity/todo state from
  `Path.home()`; the repo roots it scans are CLI args) so the test never
  touches Steven's real home. The fixture provides a fake repo with a
  spec and a handoff file plus a session record that produces a stale
  entry. The test captures the HTML and asserts (decoding HTML entities
  first, or matching the `esc()`-escaped forms — the handoff command is
  rendered through `esc()` at :745, so `&&`→`&amp;&amp;` and `"`→`&quot;`
  in raw HTML): (a) every `<code class="cmd">` has an adjacent copy
  button and there are NO bare `<code>` commands left that match the cmd
  patterns in (b); (b) every `cmd` text (decoded) matches
  `^(cd /|claude |python3 /|git -C /)` — i.e. cwd-independent; (c) the
  handoff entry renders a `cd ... && claude "Read ...` pickup command
  (decoded); (d) the emitted JS contains the guarded clipboard call, the
  `execCommand` fallback, and both the "copied ✓" and "press ⌘C"
  feedback strings. Tests written first and failing before the
  implementation (TDD). No new CLI flag is added for testability — the
  env vars are the seam.
- R6: Antigravity mirror of the workboard skill updated in the same
  commit per repo conventions, and `.claude-plugin/plugin.json` version
  bumped once.

## Out of scope

- The fleet skill's HTML (no JS today; stays that way).
- Any layout/visual redesign of the dashboard beyond the button and
  feedback states.
- Making copy work where the host page denies both clipboard APIs *and*
  text selection — the R3 select-and-⌘C path is the floor.
- Changing what the inbox decides to suggest (only how suggestions are
  rendered as commands).

## Acceptance criteria

- [ ] `bash tests/test_workboard_render.sh` passes (R1, R2, R3, R5)
- [ ] `bash tests/test_sync_skills.sh` still passes (no regression)
- [ ] `git show --stat HEAD` touches `antigravity/` and
      `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a version
      bump (R6)
- [ ] End-to-end: generate a real snapshot via the workboard skill, open
      it in Chrome (claude-in-chrome), click a copy button — "copied ✓"
      appears. Then force the deepest fallback by evaluating both
      `Object.defineProperty(navigator, 'clipboard', {value: undefined})`
      and `document.execCommand = () => false` in the console, click
      again, and observe the "press ⌘C" feedback (with the text selected)
      rather than silence or a false "copied ✓" (R3). Verify button
      visibility in both light and dark themes (R4)

## Open questions

(none)

## Parallelization

Single task (`tasks/01-copy-commands.md`) — no parallel groups. R5 mandates
TDD (the test is failing by design until the implementation lands), and R6
requires the antigravity mirror + version bump in the same commit, so test,
implementation, mirror, and bump are one indivisible session.
