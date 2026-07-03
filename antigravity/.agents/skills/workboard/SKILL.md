---
name: workboard
description: Renders a cross-repo dashboard of ALL open work on this machine - specs, task files, handoffs, Antigravity conversation state, and every Claude Code session - as a self-contained HTML snapshot with a needs-attention inbox. Use when the user asks "what's open across my repos", "show all my work", "work dashboard", "workboard", "what did I leave unfinished", or "show my sessions across projects". For agents in THIS window, the native Agent Manager is the surface; workboard covers what it can't see - other tools' state, specs, and git across every repo.
---

Show the user every piece of open work on this machine and what needs a
human decision. Read-only: the scanner never mutates the state it reports.
Design rationale and sources: the toolkit repo's docs/agent-dashboards.md —
not shipped with installs.

## 1. Scan

Run the bundled scanner (stdlib-only Python 3, no installs):

```
python3 <this skill dir>/workboard.py [ROOTS ...] --out /tmp/workboard.html
```

- No ROOTS → it scans `~/code ~/src ~/projects ~/dev ~/repos ~/work`, the
  cwd, plus every repo any Claude Code session has touched. It also reads
  `~/.gemini/antigravity*/brain/` conversation artifacts, so Antigravity's
  own open checklists appear alongside everything else.
- `--json` emits the same data as JSON; `--stale-days N` tunes the
  staleness threshold (default 7). Data sources and the state model are in
  [reference.md](reference.md) — load only if the scan misbehaves.

Write the HTML to a temp dir, never into a repo — it is a disposable
snapshot, not a pipeline artifact.

## 2. Present

Open the file in the browser (or give the user the path) and relay the
**needs-attention inbox** as a short list — that is the actionable part;
don't re-narrate the repo cards.

## 3. Triage (only if the user asks)

For each inbox item the suggested-action column already names the move:

- `blocked` handoff → resume it in a fresh Agent Manager conversation from
  the HANDOFF.md, then delete the file. Blocked task file → answer its open
  question, flip its `Status:` line, re-dispatch.
- `needs-review` all-tasks-done spec → verify, then archive the spec dir.
  Dirty/unpushed repo → commit, stash, or push.
- `stale` open spec → resume, defer (`Status: deferred`), or delete — open
  work decays; deciding is the point.

The dashboard is a point-in-time snapshot; refreshing means re-running the
scanner. Next step: none — items route back into the build/drain/handoff
workflows as triaged above.
