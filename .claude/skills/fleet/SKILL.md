---
name: fleet
description: Renders a dashboard of this session's open agents - running, queued, completed, and failed background workers - as a self-contained HTML snapshot with status tiles, a timeline, and per-agent detail. Use when the user asks "what agents are running", "show my agents", "agent status", "fleet status", "visualize the agents", or wants to watch a /parallel or /autopilot dispatch.
---

Show the user what their agents are doing right now. This is a read-only
monitoring snapshot — it never blocks on, messages, or restarts an agent, and
it must stay cheap: metadata only, never transcripts.

## 1. Gather (metadata only)

- List background tasks/agents via the harness task tools (`TaskList`; load
  it with ToolSearch if deferred). Capture per task: label/description, type,
  status, start time, end time if finished, and the output-file path.
- `git worktree list --porcelain` — worktrees named for `task/NN-*` branches
  are `/parallel` workers; match them to tasks where possible, otherwise list
  them as their own rows.
- For each agent, take at most the last 2 lines of its output file
  (`tail -n 2`) as a snippet. Do NOT read transcripts or output files
  wholesale into context — that is exactly the pollution this toolkit exists
  to avoid.
- If both sources are empty, skip rendering: report "no open agents this
  session" and stop.

## 2. Normalize

One record per agent: `label`, `kind` (scout/critic/verifier/build-worker/…),
`status` (one of `running | queued | completed | failed`), `started`,
`elapsed`, `snippet`, `output` path. Map unknown/pending states to `queued`;
anything that exited non-zero or reported BLOCKED is `failed`.

## 3. Render

Fill the HTML template in [reference.md](reference.md) — status tiles, agent
table, and timeline; the template is self-contained (no external requests,
light/dark via `prefers-color-scheme`, pre-validated status palette). Write
it to the session scratchpad (or `/tmp` if none) as `fleet.html`. Never write
it into the project repo — it is a disposable snapshot, not a pipeline
artifact.

## 4. Present

Send the file for inline rendering when the surface supports it (e.g.
`SendUserFile` with `display: render`); otherwise print the file path plus a
compact terminal table (label / status / elapsed). Either way, end with one
summary line, e.g.:

> 3 running · 1 queued · 2 completed · 0 failed — snapshot 14:32:05; re-run
> /fleet to refresh.

The dashboard is a point-in-time snapshot; refreshing means re-running
/fleet. Next pipeline step: none — when the fleet drains, return to
/parallel step 3 (collect and integrate) or the dispatching skill's
collection step.
