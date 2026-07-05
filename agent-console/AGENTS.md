# Agent Console — Orientation

A local, zero-LLM dashboard of this machine's Claude Code skills and cross-repo
open work. Pure Python stdlib; local introspection only (`git`, `gh`,
`claude … --json`) — no model inference. Runs as a launchd service on
`http://127.0.0.1:8899`.

## Map

- `agent-console.py` — everything: skill/agent scanning, workboard collection
  (repos, specs, tasks, handoffs, git, sessions), HTML rendering, HTTP server.
  Sections are commented: frontmatter/skills → workboard → rendering → server.
- `launchd/agent-console.plist.tmpl` — service template; `install.sh` renders
  it into `~/Library/LaunchAgents/com.agent-console.plist` with the current
  user's paths (nothing user-specific is committed).
- `install.sh` / `uninstall.sh` — wire up / tear down the CLI symlink + service.
- `scripts/check.sh` — canonical check (py_compile + render smoke test + the
  `tests/` unit tests via `unittest discover`).
- `tests/test_parsers.py` — pure-function tests (no server/network).
- `specs/` — open work (best-practices review); `docs/TASKS.md` indexes them.

## Commands

```bash
./scripts/check.sh    # py_compile + render both views + unit tests
./install.sh          # symlink CLI, (re)load launchd service, health-check
./agent-console.py    # run in foreground (env: SKILLS_DASHBOARD_PORT/HOST)
curl -s http://127.0.0.1:8899/healthz    # -> ok
# reload the running service after editing code (the script it runs is symlinked):
launchctl kickstart -k gui/$(id -u)/com.agent-console
```

## State

- GET routes: `/` (Skills), `/workboard`, `/healthz`. POST routes (CSRF + Host/
  Origin guarded, in `Handler.do_POST` / the "Mutations & control" section):
  `/api/priority`, `/api/agent/{start,stop,resume}`.
- Reads use `git` (per-repo, 4s timeout), `gh` (one cached `repo list`),
  `claude … --json` (plugins/sessions; falls back to `~/.claude` scraping).
  Writes: rewrite+commit a spec's `Priority:` line; spawn/kill `claude` agents.
  Pure text transforms (`apply_priority`) and CLI parsers are unit-tested.
- All data is discovered at runtime — **nothing is hardcoded to a user, repo,
  or skill**. Workboard repos come from `REPOS.md` (`AGENT_CONSOLE_REPOS`, default
  `~/REPOS.md`); project-scoped skills come from `project_roots()` (every tracked
  repo with a `.claude/` dir, or `AGENT_CONSOLE_PROJECT_ROOTS`). Port/host via
  `SKILLS_DASHBOARD_PORT`/`HOST`.
