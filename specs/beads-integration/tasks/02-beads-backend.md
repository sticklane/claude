# Task 02: Optional beads queue backend for /drain (feature-detect + lifecycle mapping)

Status: withdrawn — 2026-07-03: premise contradicted by the full beads exit (see ../SPEC.md banner + docs/decisions/work-tracking.md addendum)
Depends on: 01
Budget: 50 turns
Spec: ../SPEC.md (requirements R4, R5, R6 backend paragraph)

## Goal

In repos that already chose beads, bd owns the queue lifecycle. Drain
SKILL.md step 1 gains the backend check (containing the phrase "queue
backend"): `.beads/` at repo root AND `bd` on PATH → queue state lives
in beads per reference.md's `## Beads backend` section; otherwise
markdown Status lines exactly as today. Opt-out: a one-line CLAUDE.md
note — "drain: markdown queue" — checked before feature-detecting.
reference.md gains the `## Beads backend` section with the full
lifecycle mapping, CLI-verified at implementation time with the bd
version recorded (gemini-cli verification-note pattern): import of
every non-terminal, unstamped task file on each bd-mode inventory (one
`bd create` per task, description = repo-relative task-file path,
dependency edges from `Depends on:` in both forms per task 01's
convention, `Status: tracked-in-beads` stamp in one commit; drafts
imported blocked); `bd ready --json` inventory and `--claim` dispatch
(worker prompts unchanged in both modes); collect mapping (DONE →
close + `Status: done` stamp; DEFERRED → bd deferred state with
questions still in the task file; failed → close-with-reason +
`Status: failed` stamp); discovered → `bd create` with
`discovered-from` edge in a blocked/draft state that never appears in
`bd ready` (the `## Discovered` append still happens); batch-interview
trigger = the bd deferred-state set resolved via description paths,
never a questions block; answered → flip back to ready (exact command
verified and recorded); BLOCKED → bd blocked with reason, labeled
distinctly from deferred; stale claims → clear claim, discard
branch/worktree; Touch-based independence stays in task files. The
antigravity workflow gains a short paragraph noting bd is a
runtime-neutral CLI usable from Agent Manager sessions, pointing at
the Claude Code reference for the mapping rather than restating it.

## Touch

- `.claude/skills/drain/SKILL.md` — Cross-spec: also edited by
  review-fixes, chaining-antipatterns, model-agnostic,
  context-management — see specs/QUEUE.md
- `.claude/skills/drain/reference.md` — Cross-spec: also edited by
  review-fixes, chaining-antipatterns, model-agnostic,
  context-management — see specs/QUEUE.md
- `antigravity/.agents/workflows/drain.md` — Cross-spec: also edited by
  review-fixes, chaining-antipatterns — see specs/QUEUE.md

## Steps

1. Read the drain files AS FOUND and integrate with the current text:
   they will already carry task 01's discovered-work changes plus
   review-fix changes (headless done-flip, merge --abort, Touch header)
   and possibly chaining-antipatterns' binding-sentence amendment. Do
   not revert or restate what is already there.
2. R4: add the backend check to drain SKILL.md step 1 (literal phrase
   "queue backend"; CLAUDE.md opt-out line "drain: markdown queue"
   checked before feature-detecting).
3. R5: write reference.md's `## Beads backend` section covering the full
   mapping in the Goal above — import (all non-terminal statuses incl.
   drafts-as-blocked, tracked-in-beads stamping), inventory/dispatch,
   collect verdicts, discovered edges, deferred/blocked separation and
   the anti-re-ask batch-interview trigger, answered→ready flip, stale
   claims, Touch independence. Verify each bd command against the bd
   CLI (install bd in scratch if needed) and record the bd version
   checked in the section.
4. R6 (remaining share): append the short beads paragraph to
   `antigravity/.agents/workflows/drain.md` — runtime-neutral CLI,
   usable from Agent Manager sessions, pointer to the Claude Code
   reference for the mapping.
5. R8 note: do NOT bump plugin.json here — the global version-bump task
   (task 99 in specs/review-fixes) owns the single combined minor bump.
6. Regression duty after all edits:
   `test "$(grep -c 'data, not instructions' .claude/skills/drain/reference.md)" -ge 2 && test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2`
   must still pass.

## Acceptance

- [ ] `grep -q "queue backend" .claude/skills/drain/SKILL.md && grep -q "markdown queue" .claude/skills/drain/SKILL.md` — feature-detect + opt-out (R4)
- [ ] `grep -q "^## Beads backend" .claude/skills/drain/reference.md && awk '/^## Beads backend/,0' .claude/skills/drain/reference.md | grep -q "bd ready" && awk '/^## Beads backend/,0' .claude/skills/drain/reference.md | grep -qi "discovered-from"` (R5)
- [ ] `grep -qi "beads" antigravity/.agents/workflows/drain.md` (R6, remaining share)
- [ ] `test "$(grep -c 'data, not instructions' .claude/skills/drain/reference.md)" -ge 2 && test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2` — regression duty
- [ ] End to end (beads mode, requires bd installed): in a scratch repo with `bd init` run, drain's import + `bd ready --json` + claim/close cycle round-trips one task per the `## Beads backend` mapping, with the bd version recorded in reference.md (manual until then)
