---
name: workboard
description: Opens the live cross-repo dashboard of ALL open work on this machine - specs, task files, handoffs, Antigravity conversation state, and every Claude Code session - by launching the agent-console server's Workboard tab, which re-scans on every refresh and leads with a needs-attention inbox. Use when the user asks "what's open across my repos", "show all my work", "work dashboard", "workboard", "what did I leave unfinished", or "show my sessions across projects". For agents in THIS window, the native Agent Manager is the surface; workboard covers what it can't see - other tools' state, specs, and git across every repo.
---

Show the user every piece of open work on this machine and what needs a
human decision, on the **live agent-console dashboard** — do not write a
static HTML snapshot. Read-only: nothing here mutates the state it reports —
the explicit exceptions are the scanner's `--abandon` / `--abandon-stale`,
which write a `.workboard-abandoned` skip-marker into an Antigravity
conversation dir (Antigravity's own artifacts are never touched), and
`--prune-stale-sessions`, which deletes dead-pid `~/.claude/sessions/*.json`
records (step 4).
Design rationale and sources: the toolkit repo's docs/agent-dashboards.md —
not shipped with installs.

## 1. Launch the live dashboard

The live server is `agent-console` (`~/claude/agent-console/agent-console.py`,
launchd label `com.agent-console`). Its `/workboard` tab re-scans on every
request, so the page is always current — there is no snapshot to regenerate.

```
curl -fsS http://127.0.0.1:8899/healthz >/dev/null 2>&1 \
  || launchctl kickstart -k gui/$(id -u)/com.agent-console
open http://127.0.0.1:8899/workboard
```

- Port and host come from `SKILLS_DASHBOARD_PORT` (default 8899) and
  `SKILLS_DASHBOARD_HOST` (default 127.0.0.1) — use the same env vars when
  they are set.
- If the launchd job doesn't exist, start the server directly in the
  background (`~/claude/agent-console/agent-console.py`), re-check `/healthz`,
  then open the URL.
- **Fallback (machines without agent-console):** run the bundled stdlib-only
  scanner and open the file instead — write it to a temp dir, never into a
  repo: `python3 <this skill dir>/workboard.py [ROOTS ...] --out /tmp/workboard.html`

## 2. Relay the inbox

The user still needs the actionable list in chat, not just a URL. Pull the
same data the dashboard renders:

```
python3 <this skill dir>/workboard.py [ROOTS ...] --json
```

and relay the **needs-attention inbox** as a short list — that is the
actionable part; don't re-narrate the repo cards.

- No ROOTS → it scans `~/code ~/src ~/projects ~/dev ~/repos ~/work`, the
  cwd, plus every repo any Claude Code session has touched. It also reads
  `~/.gemini/antigravity*/brain/` conversation artifacts, so Antigravity's
  own open checklists appear alongside everything else.
- `--stale-days N` tunes the staleness threshold (default 7). Data sources
  and the state model are in [reference.md](reference.md) — load only if
  the scan misbehaves.

## 3. Triage (only if the user asks)

For each inbox item the suggested-action column already names the move:

- `blocked` handoff → resume it in a fresh Agent Manager conversation from
  the HANDOFF.md, then delete the file. Blocked task file → answer its open
  question, flip its `Status:` line, re-dispatch.
- `needs-review` all-tasks-done spec → verify, then archive the spec dir.
  Dirty/unpushed repo → commit, stash, or push.
- `stale` open spec → resume, defer (`Status: deferred`), or delete — open
  work decays; deciding is the point.
- `stale` Antigravity conversation → resume it in the Agent Manager, or run
  the scanner's `--abandon <conv-id>` (or `--abandon-stale` for all) — the
  inbox row shows the exact command; both rescan after marking.

## 4. Session hygiene (only if the user asks)

Dead-pid `~/.claude/sessions/*.json` records (left behind by `claude`
processes that exited) accumulate forever — the dashboard already filters
them out of its own liveness view, but the files themselves persist
untouched. `python3 <this skill dir>/workboard.py --prune-stale-sessions`
deletes only records whose pid is confirmed dead, then rescans; malformed
or unreadable records are left alone rather than guessed at. This is disk
hygiene, not an inbox action — it never changes what the dashboard shows.

The dashboard is live — it re-scans on every refresh, so there is nothing
to regenerate. Next step: none — items route back into the
build/drain/handoff workflows as triaged above.
