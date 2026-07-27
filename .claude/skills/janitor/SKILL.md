---
name: janitor
description: Reclaims dead in-flight work, stale runtime worktrees, and orphaned drain branches so long-running swarm sessions stay resumable and queue hygiene stays healthy.
argument-hint: "[--dry-run] [--scope all|drain|claims] [--json]"
---

Run focused queue hygiene when worktrees are accumulating or sessions die mid-run. Janitor is a cleanup-only workflow: it never edits production source, only tracker markers and infrastructure state.

## 1) Pre-flight: collect live and scoped state

1. Confirm tracker health.
   - `bd doctor --check=conventions`
   - `bd preflight`

2. Build a live-session inventory from the active runtime only.
   - This workflow uses the runtime-native inventory reader. In Claude Code use the local harness session list; in Codex use the runtime-native `list_agents` surface; in Antigravity use its native conversation/session inventory.
   - If live inventory is unavailable, run in **fail-safe skip mode**: mark anything ambiguous as blocked and do not prune.

3. Build a repository-scoped worktree inventory: `git worktree list --porcelain`.

4. Capture current in-progress issues: `bd list --status in_progress --json`.
5. Capture open parked work from tracked handoffs: `bd list --label handoff --status=open --json`.

Open `handoff` issues are valid tracker state, not ad-hoc files. Treat them as stale only after explicit evidence from both age and live-track checks.

## 2) Sweep stale claims and in-flight markers

For each open or in-progress issue whose live-session mapping is missing:

1. Drop ownership to make it resumable:
   - `bd update <id> --status open`

2. Remove tracker bookkeeping:
   - Remove `<id>` from `.beads/session-claims`.
   - Remove any matching `<id> <epoch>` line from `.beads/session-inflight`.

3. Reclaim any orphaned `drain/` worker branch/worktree tuple that this issue owns if and only if:
   - worktree path exists,
   - no live runtime session maps to that path,
   - `git -C <worktree> status --short` is clean.

Do not delete work produced by an open issue.

### Handoff-specific handling

If handoff tracking appears in a zombie pattern (`/resume-handoff` never started, no tracked live runtime sessions, old `updated_at`), do not drop data directly from files:

1. Keep the issue open, add a short triage comment:
   - `[janitor] stale-handoff: candidate for recovery - no live sessions and no recent touch`
2. Emit a `skipped_ambiguous` ledger entry so it can be reviewed and revived later.
3. Only close a handoff entry during a planned `--scope handoff` run where the operator explicitly accepts possible queue noise.

## 3) Sweep stale worktrees and branches

Run a conservative pass over known orchestration artifacts only.

Candidates are:
- `drain/<issue-id>*` branches and worktrees,
- branches that start with `task/` and resolve to closed/unknown tasks,
- worktree paths under `/tmp`/`/private/tmp` that are not mapped to a live session and have no open tracking issue in `bd`.

For each candidate:
1. Skip immediately if any state is ambiguous:
   - cannot determine liveness,
   - worktree is dirty,
   - branch is unmerged (or merge status is undetermined against base branch),
   - worktree path has no valid branch reference from `git worktree list --porcelain`.
2. In non-dry-run mode:
   - verify the branch is merged/fast-forwarded into the detected base branch before branch deletion.
   - `git worktree remove --force <worktree_path>`
   - `git worktree prune`
   - If the branch is only held by that worktree and the branch is not open in `bd`, run `git branch -D <branch_name>` after successful worktree removal.
3. If a branch is unmerged but clean, skip removal with `recoverable: true` and route it for manual merge handoff.
4. Record the action in the janitor ledger.

### Branch deletion order

If branch cleanup follows worktree cleanup, always remove the checkout first.

- Remove worktree before deleting a checked-out branch.
- Never run branch deletion before the corresponding worktree removal.

If a safe branch deletion is needed, remove it only after worktree removal succeeds.

## 4) Revivable cleanup ledger

Every sweep writes one line per action to `.beads/janitor-revival-log.jsonl`.
Append fields are:

- `ts` (RFC3339)
- `type` (`reclaimed_claim`, `removed_worktree`, `skipped_ambiguous`, `dry_run`)
- `id` / `branch` / `path`
- `reason`
- `recoverable` (`true` if a non-destructive reversal exists)
- For handoff zombies, include `type: reclaimed_claim` plus `reason` and keep `recoverable: true` only if the issue stayed open in bd after triage comment.

Also print a short terminal summary:

- reclaimed claims,
- removed worktrees,
- skipped items,
- failures with IDs and commands.

If `--dry-run` is set, do not mutate anything and write only `dry_run` ledger entries.

## 5) Human-facing closure and safe default

If this pass unblocks work, post the exact unblock evidence on the issue that blocked on the recovery and run `/resume` or the normal queue entry.

If a task is not clear to revive, file a follow-up issue with `--type=task` and link it with `--deps "discovered-from:<current id>"`.

## Notes

- This workflow is intentionally conservative. A wrong prune is worse than leaving a zombie for the next pass.
- Do not run this workflow on a branch that is already in an explicit cleanup lockout.
- If your live session inventory is down, stop at the ambiguity checks and record skipped items.
