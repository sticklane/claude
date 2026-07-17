# plugin-staleness hook

A `SessionStart` hook that warns when the locally-installed `agentic` Claude
Code plugin is behind the source repo. This repo distributes itself as the
`agentic` plugin, and Claude Code caches the plugin's content at install time
(`~/.claude/plugins/cache/agentic-toolkit/agentic/<version>/`). That cache
goes stale once new content lands and `.claude-plugin/plugin.json`'s `version`
bumps — the manual remedy is `bin/refresh-plugins`. This hook is the missing
proactive-detection half: it compares the source manifest's version against
the installed version and surfaces a warning at session start.

## Why a warning, never a block or auto-refresh

Staleness is advisory, not fatal: an out-of-date plugin cache still works, it
just may lack the newest doctrine. So the hook exits 0 with a message on
stdout — it never returns a non-zero blocking exit, and it never runs
`bin/refresh-plugins` for you (that reinstall has side effects — a marketplace
re-sync and cache prune — the user didn't request this session). It only
points at the remedy; running it stays the user's call.

The automation half is `hooks/plugin-autorefresh` — a `Stop` hook that runs
`bin/refresh-plugins` once a bump has actually landed on the marketplace
source (maintainer-requested, 2026-07-16). That doesn't change this hook's
stance: at SessionStart it still only warns.

## What it does

- Silent (empty stdout, exit 0) whenever it cannot make a confident
  behind-comparison: no `.claude-plugin/plugin.json` at the project root (not
  a plugin checkout), no determinable installed version, or an installed
  version equal to or ahead of source. An up-to-date install sees zero
  behavior change.
- Reads the source version from `$CLAUDE_PROJECT_DIR/.claude-plugin/plugin.json`
  (falling back to cwd), and the installed version from `claude plugin list`
  (parsed the same way `bin/refresh-plugins` does).
- Warns only when the installed version is **strictly behind** source (by
  `sort -V` semver ordering), naming both versions and pointing at
  `bin/refresh-plugins`.
- Antigravity and Codex are live-file runtimes with no install/cache step
  (see `bin/refresh-plugins`), so this cache-version skew is Claude-Code-only.

## Wiring (one user-run step)

This hook ships with the toolkit. It is also wired into this repo's own
`.claude/settings.json` so the toolkit's own sessions get the check. To cover
every repo's sessions, wire it globally in `~/.claude/settings.json` (replace
`<TOOLKIT>` with the toolkit checkout root):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<TOOLKIT>/hooks/plugin-staleness/staleness-check.sh"
          }
        ]
      }
    ]
  }
}
```

Merge this `SessionStart` array into any existing `hooks` block rather than
replacing it — see `hooks/handoff-resume/README.md` for the same caveat if
you're running multiple SessionStart hooks.

## Testing

`bash hooks/plugin-staleness/test.sh` — synthetic fixtures only. It stubs the
installed version via `PLUGIN_STALENESS_INSTALLED_VERSION` and never invokes
the live `claude plugin list` nor touches the real installed plugin cache.
