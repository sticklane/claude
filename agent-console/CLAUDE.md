# Agent Console — Conventions

@AGENTS.md

## Rules

- **Zero LLM cost — no model inference, ever.** That is the hard invariant, not
  "no subprocess/network". Local introspection is fine: `git`, `gh` (GitHub
  repo metadata, best-effort + long-cached, off the hot path), and
  `claude … --json` (plugin/agent introspection — no model call). Never call the
  Claude model or an inference API. Stdlib only; no third-party pip deps.
- **Prefer supported `claude … --json` CLIs over reading `~/.claude` internals.**
  `claude plugin list --json` (carries `enabled`) and `claude agents --json` are
  documented/stable; `installed_plugins.json`, `sessions-index.json`, and the
  `~/.claude/sessions/*.json` PID records are undocumented and Anthropic's docs
  say they change between versions. The file scrapers are fallback-only.
- **Everything is discovered at runtime — nothing user-specific in the repo.**
  No hardcoded usernames, home/`/Users/<name>` paths, repo names, or personal
  skill names anywhere in tracked files — a committed one is a bug (grep before
  commit). Config comes from env (`AGENT_CONSOLE_*`, `SKILLS_DASHBOARD_*`) or
  discovery (REPOS.md, `.claude/` scan); the launchd plist is rendered from a
  template at install time, never committed with real paths. Personal skills are
  shown only because they're scanned live — never name a specific one in code or
  docs.
- **No decorative chrome.** No emoji, no meta self-labels ("no LLM cost",
  "powered by…") in the UI. Functional facts live in the data, not banners.
- **Fail soft, and fail loud on drift.** A bad file/repo/slow `git` must never
  blank the page (`do_GET` degrades to a 500, scans skip unreadable items). But
  when an internal source exists yet parses to nothing, surface a "source check"
  banner — a silent-empty render that reads as "no work" is the worst outcome.
- Run `./scripts/check.sh` green before committing (it runs the parser unit
  tests too, not just a smoke test).
