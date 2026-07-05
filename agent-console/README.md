# Agent Console

A local, zero-LLM dashboard for this machine's Claude Code setup. One pure-Python
stdlib HTTP server (plus local `git`) — no network calls to Claude or anywhere
else, so it costs nothing to run. Auto-starts at login via launchd.

**http://127.0.0.1:8899**

| View | Path | Shows |
|------|------|-------|
| **Skills** | `/` | Every installed agent skill & subagent — personal, project, and plugin (skills, commands, and agents), grouped by source, with a live filter. |
| **Workboard** | `/workboard` | Open work across every repo in `~/REPOS.md`: specs, `docs/TASKS.md`, handoffs, git state, and Claude Code sessions — with a needs-attention inbox up top. |

Each request re-scans on demand (workboard git state is cached ~20s), and the
page **auto-refreshes in place every 25s** — it re-fetches and swaps the data
while preserving your scroll position, expanded specs, and open drill-down
panel (it pauses while a tab is hidden or you're typing in the filter).

On the workboard: **click a summary tile** (open specs / open tasks / active
sessions) to drill into the underlying items, and **expand a spec** (`▸`) to see
its task **dependency graph** — a DAG laid out left→right by depth, parsed from
each task file's `Depends on:` line and colored by status.

## Controls (the read-write surface)

- **Priorities** — each spec row has a `P0–P3 / —` selector. Changing it rewrites
  the spec's `Priority:` line and **auto-commits** it (one file, one commit).
  Specs are sorted by priority. Only specs inside a `~/REPOS.md`-tracked repo are
  editable.
- **Agents** — the *Agents* section lists running background agents (`claude
  agents --json`). **Kick off** a new one (prompt + repo → `claude --bg -p …`;
  this costs tokens), **stop** a running one (SIGTERM — resumable), or **resume**
  a recent one (`claude --bg --resume`). Every costly/destructive action needs a
  confirm click.

These mutating actions are **POST-only and CSRF-guarded**: each page carries a
per-process token required on every write, plus Host/Origin checks — so another
local process or a malicious page can't drive them. Writes are validated (spec
path must be under a tracked repo; agent `cwd` must be a tracked repo; `stop`
only accepts a PID the CLI currently reports as an agent).

## Install

```bash
./install.sh      # symlinks the CLI + loads the launchd service
```

Then open http://127.0.0.1:8899. To remove: `./uninstall.sh`.

Run it in the foreground for a one-off (no launchd):

```bash
./agent-console.py                 # or: agent-console  (after install)
SKILLS_DASHBOARD_PORT=9001 ./agent-console.py
```

## How it decides "needs attention"

- **Handoff waiting** — a `HANDOFF.md` exists in the repo.
- **Ready to verify** — a spec's tasks are all done.
- **Stale spec** — a spec has open tasks untouched for >7 days.
- **Unpushed** — commits ahead of upstream.
- **Dirty, no live session** — uncommitted changes with no session running in that repo.

## Notes

- **Plugins and live sessions come from supported Claude CLIs**:
  `claude plugin list --json` (only `enabled` plugins are shown) and
  `claude agents --json`. If `claude` isn't on `PATH`, it falls back to reading
  the internal `installed_plugins.json` / `~/.claude/sessions/*.json` (which
  lack enabled state / lag, and are undocumented — see `specs/`).
- Personal skills in `~/.claude/skills/` are symlinks into their home repos, so
  the scanner follows symlinks (via `scandir`) and never walks into
  `worktrees/` or `node_modules/`.
- Built-in harness skills (dataviz, code-review, …) have no on-disk `SKILL.md`,
  so they can't be enumerated without the harness — scope is personal + project
  + plugin.
- GitHub public/private badges use one cached `gh repo list --json` call (the
  only network touch); everything else is local.

Personal tooling. See `AGENTS.md` for orientation.
