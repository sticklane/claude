---
name: fleet
description: Prints a markdown table of this session's open agents - running, queued, completed, and failed background workers - inline in the response, one row per agent (label, kind, status, elapsed, snippet) plus a one-line status summary. Use when the user asks "what agents are running", "show my agents", "agent status", "fleet status", "visualize the agents", or wants to watch a /drain or /build dispatch.
---

Show the user what their agents are doing right now. This is a read-only
monitoring snapshot — it never blocks on, messages, or restarts an agent, and
it must stay cheap: metadata only, never transcripts.

## 1. Gather (metadata only)

- List background tasks/agents via the harness task tools (`TaskList`; load
  it with ToolSearch if deferred). Capture per task: label/description, type,
  status, start time, end time if finished, and the output-file path.
- Enumerate this session's isolated worktrees — e.g., under git: `git worktree
list --porcelain`. Worktrees named for `task/NN-*` branches are dispatched
  task workers (a drain queue or group, /build); match them to
  tasks where possible, otherwise list them as their own rows.
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

## 3. Print

Print one markdown table directly in the response — no file, static or
otherwise, is produced. One row per agent, columns
`Label | Kind | Status | Elapsed | Snippet`:

```
| Label | Kind | Status | Elapsed | Snippet |
| --- | --- | --- | --- | --- |
| task/03-foo | build-worker | running | 4m12s | … last output line … |
```

Then end with one summary line counting each status, e.g.:

> 3 running · 1 queued · 2 completed · 0 failed — snapshot 14:32:05; re-run
> /fleet to refresh.

The table is a point-in-time snapshot; refreshing means re-running
/fleet. Next pipeline step: none — when the fleet drains, return to
the dispatching skill's collection step (drain step 3 for queue and
group dispatches).
