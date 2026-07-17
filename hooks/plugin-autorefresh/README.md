# plugin-autorefresh hook

A `Stop` hook that runs `bin/refresh-plugins` automatically once a
`.claude-plugin/plugin.json` version bump has landed on the marketplace
source. This repo distributes itself as the `agentic` plugin from the
GitHub-sourced `agentic-toolkit` marketplace, so the installed plugin cache
goes stale on every version bump. `hooks/plugin-staleness` is the detection
half (a warn at session start); this hook is the remediation half: at the
end of any turn in this repo, if the installed plugin is strictly behind the
version on origin's default branch, it refreshes the install.

## Why Stop, and why the remote-tracking ref

- **After push, never after commit.** The marketplace pulls from GitHub, so
  refreshing against a merely-committed bump reinstalls the old version —
  the reason `bin/submit` exists instead of a pre-push git hook. The hook
  reads the manifest at origin's default branch remote-tracking ref
  (`origin/HEAD`, falling back to `origin/main`), which the `git push` that
  shipped the bump updates locally. A committed-but-unpushed bump stays
  silent; the next turn after the push picks it up.
- **Stop is the moment bumps become visible.** Version bumps here happen in
  Claude Code sessions and are pushed by turn end (repo conventions), so the
  Stop hook fires exactly when a refresh first becomes useful. Bumps that
  land outside a session (e.g. a PR merged on GitHub) are still covered by
  the plugin-staleness warning and the login-time update stack.

## Behavior

- Silent (empty stdout, exit 0) whenever it cannot act confidently: no
  remote version determinable, no determinable installed version, or an
  install equal to or ahead of the remote.
- Single-flight: a lock (`$TMPDIR/plugin-autorefresh-<uid>.lock`) keeps
  concurrent sessions' Stop hooks from racing the reinstall + cache prune;
  a stale lock (>10 min) from a crashed run is taken over.
- **Always exits 0.** A refresh failure prints a pointer to run
  `bin/refresh-plugins` manually and never blocks the session from stopping.
- Auto-running the refresh is deliberate and maintainer-requested
  (2026-07-16). It does not change plugin-staleness's warn-only stance at
  SessionStart — that hook still never acts on the user's behalf.
- Antigravity and Codex are live-file runtimes with no install/cache step
  (see `bin/refresh-plugins`), so this hook is Claude-Code-only and has no
  mirror.

## Env overrides (tests + explicit control)

- `PLUGIN_AUTOREFRESH_REMOTE_VERSION` — skip the git read.
- `PLUGIN_AUTOREFRESH_INSTALLED_VERSION` / `PLUGIN_AUTOREFRESH_SKIP_CLI=1` —
  skip the `claude plugin list` read.
- `PLUGIN_AUTOREFRESH_CMD` — the refresh command (default
  `$CLAUDE_PROJECT_DIR/bin/refresh-plugins`).
- `PLUGIN_AUTOREFRESH_LOCK` — the lock path.

Tests: `bash hooks/plugin-autorefresh/test.sh` (stubbed end to end — never
touches the live CLI, cache, or network).

## Wiring

Wired in this repo's `.claude/settings.json` as a `Stop` hook:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/hooks/plugin-autorefresh/autorefresh.sh",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```
