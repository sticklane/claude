# Task 03: plugin-staleness detection and warning

Status: done
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirement R3)
Touch: bin/refresh-plugins, hooks/plugin-staleness/, .claude/settings.json, docs/memory.md

## Goal

A plugin-staleness check compares the installed Claude Code plugin's
version (this repo distributes itself as the `agentic` plugin via
`.claude-plugin/plugin.json`'s `version` field) against the source repo's
current value, and surfaces a warning — never a silent block, never an
auto-refresh with side effects the user didn't request — when the
installed version is behind source. This builds on the existing manual
`bin/refresh-plugins` remedy (run after pushing); this task is the missing
proactive-detection half.

Where the check lives and how it's triggered is this task's own
implementation decision, but is constrained to this task's own `Touch:`
list above (no new path outside it) — the spec leaves the checkpoint open
("session start, or before a session acts on doctrine that might have
changed") but this task file resolves the HOST to one of two options, so
there's no risk of landing in an unlisted path a drained worker can't
touch:

1. **Default:** a new `hooks/plugin-staleness/` directory, following the
   existing `hooks/handoff-resume/` shape (a `SessionStart` hook: script +
   README + test.sh — read that directory's files for the pattern before
   starting). Wire it via `.claude/settings.json`'s `hooks.SessionStart`
   array (add the array if absent).
2. **Fallback**, only if the SessionStart-hook shape proves unworkable for
   a concrete reason recorded in the commit message: extend
   `bin/refresh-plugins` itself with a `--check`-style proactive mode.

Either way, record which option was taken and why in the commit message.

## Touch

Do not touch `bin/install-gates`, `templates/check.sh.tmpl`, or
`templates/stop-gate.sh` (Tasks 01/04/05 own those). Do not touch any
`.claude/skills/*/SKILL.md` file (Task 02 owns the two that change under
this spec, and no other skill file is in scope for R3) — the two Touch
paths in Steps above are this task's only allowed hosts.

## Steps

1. Read `bin/refresh-plugins` in full (45 lines) — it already knows how to
   query the installed plugin version via `claude plugin list` and compare
   against cache directories. Read `hooks/handoff-resume/README.md` and
   `hooks/handoff-resume/resume-check.sh` for the SessionStart hook pattern
   this repo already uses, and `hooks/handoff-resume/test.sh` for how such
   a hook is tested.
2. Decide and record the checkpoint and host file (see Goal above).
3. Write a failing test first: given a repo where `.claude-plugin/
plugin.json`'s version differs from the version `claude plugin list`
   (or an equivalent installed-state read) reports, the new check emits a
   warning (non-empty stdout/stderr, exit 0 — never a non-zero blocking
   exit) naming both versions. Given matching versions, the check is
   silent.
4. Implement the check so it satisfies the test. The literal phrase
   `plugin-staleness` must appear in the file it lands in.
5. Run the new test(s) green; run this repo's own check command before
   committing.

## Acceptance

- [x] `grep -rc "plugin-staleness" bin/refresh-plugins hooks/ 2>/dev/null | awk -F: '{sum+=$2} END {print sum}'` → greater than 0 (the phrase must appear in whichever of this task's two allowed hosts was actually chosen) — verifier: sum = 6 (phrase appears in hooks/plugin-staleness/staleness-check.sh, README.md, test.sh)
- [ ] MANUAL (manual-pending): on a repo with a deliberately stale plugin cache (mismatched `.claude-plugin/plugin.json` version vs. what's installed), confirm the check surfaces a warning rather than silently proceeding or hard-blocking — an unattended worker cannot exercise an interactive plugin-cache mismatch against the real installed state (docs/memory/unattended-worker-tool-limits.md manual-pending escape). Automated synthetic-fixture equivalent PASSES (verifier: behind case warns naming both versions, matching case silent, both exit 0).
- [x] Whatever automated test this task adds (e.g. a `hooks/plugin-staleness/test.sh` or an addition to an existing test file) exits 0 — verifier: `bash hooks/plugin-staleness/test.sh` → pass: 12 fail: 0, exit 0

## Decisions

- Host/checkpoint choice: took the **default** (Option 1) — a `hooks/plugin-staleness/` SessionStart hook following `hooks/handoff-resume/`'s shape (script + README + test.sh), wired via `.claude/settings.json`'s `hooks.SessionStart` array. The SessionStart-hook shape was a clean fit with no concrete reason it's unworkable, so the Option-2 fallback (extending `bin/refresh-plugins --check`) was not needed. Reversal: delete `hooks/plugin-staleness/`, revert the settings.json SessionStart array, and implement the check as a `--check` mode in `bin/refresh-plugins` instead.
- `docs/memory.md` was in the Touch list but left untouched: no narrow per-topic memory entry was warranted for a self-documenting hook (it has its own README). Reversal: add an index line if a future lesson emerges.
