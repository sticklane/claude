---
name: workboard
description: Opens the live cross-repo dashboard of ALL open work on this machine - specs, task files, handoffs, Kiro/Antigravity state, and native Claude Code, Codex, or Antigravity sessions - by launching the agent-console server's Workboard tab, which re-scans on every refresh and leads with a needs-attention inbox. Use when the user asks "what's open across my repos", "show all my work", "work dashboard", "workboard", "what did I leave unfinished", or "show my sessions across projects". For agents in THIS session only, use /fleet's inline table instead.
---

Show the user every piece of open work on this machine and what needs a
human decision, on the **live agent-console dashboard** — do not write a
static HTML snapshot. Read-only: nothing here mutates the state it reports —
the explicit exceptions are the scanner's `--abandon` / `--abandon-stale`,
which write a `.workboard-abandoned` skip-marker into an Antigravity
conversation dir (Antigravity's own artifacts are never touched), and
`--prune-stale-sessions`, which deletes dead-pid
`~/.claude/sessions/*.json` records (step 4).
Design rationale and sources: [docs/agent-dashboards.md](../../../docs/agent-dashboards.md).

## 1. Launch the live dashboard

The live server is `agent-console` (`~/claude/agent-console/agent-console.py`).
Its `/workboard` tab re-scans on every request, so the page is always current
— there is no snapshot to regenerate.

For Claude Code, use its launchd service:

```
curl -fsS http://127.0.0.1:8899/healthz >/dev/null 2>&1 \
  || launchctl kickstart -k gui/$(id -u)/com.agent-console
open http://127.0.0.1:8899/workboard
```

For Codex or Antigravity, do not reuse that Claude Code service. Start a
direct server on a free local port with
`AGENTIC_RUNTIME=<active-runtime>` in its environment, then open that
server's `/workboard` URL. The server inventories that runtime's native
session records and routes start, dispatch, and resume through its native
CLI. Codex and Antigravity do not expose a supported machine-wide live-session
inventory, so their sessions are labeled resumable rather than running and
their live-stop control is unavailable. The server never shells out to a
different runtime as a fallback.

- Port and host come from `SKILLS_DASHBOARD_PORT` (default 8899) and
  `SKILLS_DASHBOARD_HOST` (default 127.0.0.1) — use the same env vars when
  they are set.
- If the Claude launchd job doesn't exist, start the server directly in the
  background with `AGENTIC_RUNTIME=claude-code`, re-check `/healthz`, then
  open the URL.
- **If the live server genuinely cannot start** (the `/healthz` check fails
  AND the direct background-start attempt also fails): report the startup
  error and what to check — is `python3` available, is the port free
  (another process may hold `SKILLS_DASHBOARD_PORT`, default 8899), are
  `SKILLS_DASHBOARD_PORT` / `SKILLS_DASHBOARD_HOST` set as intended. Do not
  fall back to writing a static HTML file — the scanner has no file-output
  mode; its only outputs are `--json` (step 2) and a one-line summary.

## 2. Relay the inbox

The user still needs the actionable list in chat, not just a URL. Pull the
same data the dashboard renders:

```
AGENTIC_RUNTIME=<active-runtime> \
  python3 <this skill dir>/workboard.py [ROOTS ...] --json
```

and relay the **needs-attention inbox** as a short list — that is the
actionable part; don't re-narrate the repo cards.

Use `claude-code`, `codex`, or `antigravity` as `<active-runtime>`. The
scanner reads only that runtime's session inventory: Claude Code transcripts
plus its live-agent inventory, Codex rollout JSONL, or Antigravity's
conversation metadata cache. It never queries another runtime.

The inbox is **human-bounded work only**: agent-bounded work (drafts,
`Unblock: run:/agent:` rechecks, all-tasks-done specs awaiting the
verifier) proceeds via dispatch and never appears as an attention item —
the one exception is an open `handoff`-labeled bd issue, which surfaces
because resuming it needs a human to restart the session.

- No ROOTS → it scans `~/code ~/src ~/projects ~/dev ~/repos ~/work`, the
  cwd, **plus every repo an active-runtime session has touched** (when native
  metadata includes a workspace path). Pass explicit roots when the user names
  directories.
- `--stale-days N` tunes the staleness threshold (default 7).
- Data sources and the state model are documented in
  [reference.md](reference.md) — load it only if the scan misbehaves or the
  user asks what a state means.

## 3. Triage (only if the user asks)

For each inbox item the suggested action column already names the move:

- `blocked` handoff → run `/resume-handoff` in a fresh session; it reads the
  handoff-labeled bd issue and its tracked issue comments, resumes the
  recorded next step, then closes the handoff issue. Blocked task (no unblock
  step recorded) → answer its open question or record a typed `Unblock:` in
  its bd issue, then re-dispatch via /build or /drain.
- `needs-review` dirty/unpushed repo → commit, stash, or push.
- `stale` open spec → resume it or close/defer its task issues in bd — open
  work decays; deciding is the point.
- `stale` Antigravity conversation → resume it in Antigravity, or run the
  scanner's `--abandon <conv-id>` (or `--abandon-stale` for all) — the
  inbox row shows the exact command; both rescan after marking.

## 4. Session hygiene (only if the user asks)

For Claude Code only, dead-pid `~/.claude/sessions/*.json` records (left behind by `claude`
processes that exited) accumulate forever — the dashboard already filters
them out of its own liveness view, but the files themselves persist
untouched. `python3 <this skill dir>/workboard.py --prune-stale-sessions`
deletes only records whose pid is confirmed dead, then rescans; malformed
or unreadable records are left alone rather than guessed at. This is disk
hygiene, not an inbox action — it never changes what the dashboard shows.

The dashboard is live — it re-scans on every refresh, so there is nothing
to regenerate. Next stage: none — items route back into /build, /drain,
/handoff, or the verifier agent as triaged above.
