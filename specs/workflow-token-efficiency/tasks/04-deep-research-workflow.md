# Task 04: Repo-owned deep-research workflow + bin/sync-workflows

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: 01
Priority: P2
Budget: 45 turns
Spec: ../SPEC.md (requirement R5)
Touch: .claude/workflows/deep-research.js, bin/sync-workflows, tests/test_sync_workflows.sh

## Goal

A repo-owned `.claude/workflows/deep-research.js` mirrors the built-in's
phases (scope → search → fetch → verify → synthesize) with per-stage
tiering — search/fetch/claim-extraction at `effort: 'low'`, verify and
synthesize at session model, all fan-out stages schema-constrained — and
opens with `log('[repo-deep-research]')`. A narrow `bin/sync-workflows`
symlinks ONLY `.claude/workflows/*` into `~/.claude/workflows/` with the
`SYNC_WORKFLOWS_SRC`/`_DEST` env-override pattern (sync-skills is retired
— do NOT recreate or extend it); its tests never touch the real home
directory.

## Touch

New files only. Must NOT touch: any SKILL.md, .claude/rules/ beyond what
task 01 already wrote (if the resolution-probe fallback fires, the one
required R1-section sentence about the `research` name is the sole
sanctioned edit to token-discipline.md), plugin.json.

## Steps

1. **Resolution probe first:** write the script, symlink it via the
   env-override into a temp dest, then into `~/.claude/workflows/`, and
   invoke `Workflow({name: "deep-research"})`; confirm
   `[repo-deep-research]` appears in the progress log. If the harness
   built-in wins resolution, rename to `research.js` and document the
   fallback in the task-01 rule section (one sentence).
2. Write `tests/test_sync_workflows.sh` first (env-override src/dest,
   symlink-only assertion, idempotence) → RED, then implement
   `bin/sync-workflows` → GREEN. Note: the spec's acceptance line naming
   `tests/test_sync_skills.sh` is stale — sync-skills and its test were
   retired 2026-07-03 (commit 745b475); this test file replaces that half
   of the pair. Annotate the spec checkbox accordingly when ticking.
3. `node --check .claude/workflows/deep-research.js`.
4. Record the probe outcome in the task file.

## Acceptance

- [x] `bash tests/test_sync_workflows.sh` → exit 0 (env-override paths only) — 28/28 pass; replaces the stale `tests/test_sync_skills.sh` acceptance line (sync-skills retired 2026-07-03, commit 745b475).
- [x] `node --check .claude/workflows/deep-research.js` → exit 0; first statement is `log('[repo-deep-research]')`; search/fetch/extract stages carry `effort: 'low'`; fan-out stages pass schemas — node --check exit 0; marker is line 11 (first executable stmt after the `meta` export); `effort: "low"` on the Search + Fetch dispatches; all 5 agent() dispatches schema-constrained; also passes bin/check-token-discipline's 3 checks.
- [x] Resolution probe recorded: `[repo-deep-research]` observed in a live Workflow progress log, OR the `research` fallback taken and documented in the R1 rule section — RESOLVED by orchestrator (has Workflow tool): launched `deep-research` **by name** via the Workflow tool (runId wf_37f07d3c-2fa) after `bin/sync-workflows`; `[repo-deep-research]` marker appeared in the live journal (repo script won name-resolution over the harness built-in) and the full pipeline ran to completion with a valid structured report (probe question had no sources → 0 claims, as expected).
- [x] After `bin/sync-workflows`: `test -L ~/.claude/workflows/deep-research.js` (or `research.js`) → exit 0 — orchestrator ran `bin/sync-workflows` against real `$HOME` post-merge ("linked 1"); `test -L ~/.claude/workflows/deep-research.js` → exit 0, `readlink` → `/Users/sjaconette/claude/.claude/workflows/deep-research.js`.
