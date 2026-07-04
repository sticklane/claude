# Evidence — task 01 (workboard copy-buttons)

Verified inline (no separate verifier agent available in this workflow env);
all checks re-run from a clean tree against the acceptance criteria.

## AC1 — `bash tests/test_workboard_render.sh` (R1, R2, R3, R5)
PASS. Hermetic fixture under `tests/fixtures/workboard/` (fake repo + spec +
HANDOFF.md; a stale session record injected via `CLAUDE_CONFIG_DIR`). The test
decodes HTML entities and asserts: (a) every `<code class="cmd">` is followed
by a `.copy-btn`, and no bare `<code>` command matching the cwd-independent
pattern remains; (b) every decoded cmd matches `^(cd /|claude |python3 /|git -C /)`;
(c) the repo-card handoff renders `cd … && claude "Read … and continue the work
it describes"`; (d) the emitted JS contains `navigator.clipboard &&`,
`writeText`, `execCommand('copy')`, `copied ✓`, `press ⌘C`.
Output: `PASS: workboard render (R1/R2/R3/R5) — 3 cmd(s) checked`
(3 = ready-launch cmd, inbox handoff cmd, repo-card handoff pickup cmd).

## AC2 — `bash tests/test_sync_skills.sh` still passes (no regression)
SUBSTITUTED. `tests/test_sync_skills.sh` was retired in commit c7c4b38
("chore: retire bin/sync-skills — distribution is plugin-based"), which predates
this spec — the reference is stale. Equivalent no-regression guards for the
workboard skill both PASS:
- `bash tests/test_workboard_actionability.sh` → `PASS: workboard actionability (R1-R3 subset)`
- `python3 .claude/skills/workboard/test_workboard.py` → `Ran 16 tests … OK`
  (includes `test_stale_antigravity_inbox_item_carries_runnable_abandon_command`,
  which exercises the inbox `cmd` rendering path this task changed).

## AC3 — antigravity mirror + version bump (R6)
`antigravity/.agents/skills/workboard/workboard.py` is byte-identical to the
main skill after the change (`diff -q` clean). `.claude-plugin/plugin.json`
bumped 0.7.2 → 0.7.3. Both land in the single task commit (verify with
`git show --stat HEAD` + `git diff HEAD~1 -- .claude-plugin/plugin.json`).

## AC4 — copy behaviour + fallback + theming (R3, R4)
SUBSTITUTED for the interactive Chrome step (no browser session available to an
unattended worker) with a deterministic Node harness that runs the ACTUAL
emitted copy JS against a DOM shim through all three branches:
1. `navigator.clipboard.writeText` resolves → button shows `copied ✓` (`is-copied`).
2. clipboard rejects, `execCommand('copy')` returns true → `copied ✓`.
3. clipboard undefined AND `execCommand` returns false → `press ⌘C` (`is-manual`),
   the command text is selected in place, and it is NOT a false `copied ✓`.
Output: `PASS: R3 — all three copy branches end in correct visible feedback, none silent`.
R4 theming: `.copy-btn` / `code.cmd` / feedback states use only existing CSS
custom properties (`--surface`, `--border`, `--ink-2`, `--blue`, `--good`,
`--serious`), each defined in both the light `:root` and the
`prefers-color-scheme: dark` block, so the button and both feedback states are
styled in both themes. Snapshot stays self-contained (inline `<style>`/`<script>`,
no external requests).
