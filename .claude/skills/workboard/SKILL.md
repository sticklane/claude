---
name: workboard
description: Renders a cross-repo dashboard of ALL open work on this machine - specs, task files, handoffs, Kiro/Antigravity state, and every Claude Code session (live, recent, stale) - as a self-contained HTML snapshot with a needs-attention inbox. Use when the user asks "what's open across my repos", "show all my work", "work dashboard", "workboard", "what did I leave unfinished", or "show my sessions across projects". For agents in THIS session only, use /fleet instead.
---

Show the user every piece of open work on this machine and what needs a
human decision. Read-only: the scanner never mutates the state it reports.
Design rationale and sources: [docs/agent-dashboards.md](../../../docs/agent-dashboards.md).

## 1. Scan

Run the bundled scanner (stdlib-only Python 3, no installs):

```
python3 <this skill dir>/workboard.py [ROOTS ...] --out <scratchpad>/workboard.html
```

- No ROOTS → it scans `~/code ~/src ~/projects ~/dev ~/repos ~/work`, the
  cwd, **plus every repo any Claude Code session has touched** (from session
  records' `cwd`). Pass explicit roots when the user names directories.
- `--json` emits the same data as JSON if you need to reason over it instead
  of rendering; `--stale-days N` tunes the staleness threshold (default 7).
- Data sources and the state model are documented in
  [reference.md](reference.md) — load it only if the scan misbehaves or the
  user asks what a state means.

Write the HTML to the session scratchpad (or `/tmp`), never into a repo —
it is a disposable snapshot, not a pipeline artifact.

## 2. Present

Send the file for inline rendering when the surface supports it
(`SendUserFile` with `display: render`); otherwise print the path plus the
scanner's one-line summary. Then relay the **needs-attention inbox** as a
short list — that is the actionable part; don't re-narrate the repo cards.

## 3. Triage (only if the user asks)

For each inbox item the suggested action column already names the move:

- `blocked` handoff → resume it in a fresh session from the HANDOFF.md, then
  delete the file. Blocked task file → answer its open question, flip its
  `Status:` line, re-dispatch via /build or /drain.
- `needs-review` all-tasks-done spec → run the verifier, then archive the
  spec dir. Dirty/unpushed repo → commit, stash, or push.
- `stale` open spec → resume, defer (`Status: deferred`), or delete — open
  work decays; deciding is the point.

The dashboard is a point-in-time snapshot; refreshing means re-running the
scanner. Next pipeline step: none — items route back into /build, /drain,
/handoff, or /verify as triaged above.
