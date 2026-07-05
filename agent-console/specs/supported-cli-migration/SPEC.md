# Migrate skill/plugin/session enumeration to supported Claude Code CLIs

Status: done
Priority: P1
Source: holistic best-practices review (2026-07-04) — Anthropic docs research + `claude plugin list --json` discovery

## Problem

The dashboard enumerates skills, plugins, and live sessions by reading Claude
Code's **internal, undocumented** on-disk state. Anthropic's docs explicitly
warn that the session transcript format "is internal to Claude Code and changes
between versions, so scripts that parse these files directly can break on any
release." Two of these now have **documented, stable CLI surfaces** (verified
working in Claude Code 2.1.201):

- `claude plugin list --json` → array of `{id, version, scope, enabled,
  installPath, ...}`. Replaces scraping `~/.claude/plugins/installed_plugins.json`.
- `claude agents --json` → live sessions `{pid, cwd, sessionId, name, status,
  state, ...}`. Replaces scraping `~/.claude/sessions/*.json` PID records.

There is also a **correctness bug** this fixes: `installed_plugins.json` has no
enabled/disabled state, so the Skills view shows **disabled** plugins as active.
Confirmed: `auto-memory` is `enabled:false` yet its 6 skills render. The
original ask was "all *active* agent skills."

## Scope

1. Add a small `_claude_json(*args)` helper: run `claude <args> --json` via
   `shutil.which("claude")`, timeout ~8s, parse JSON, return `[]`/`{}` on any
   failure (offline-safe, same pattern as `gh_visibility`).
2. Plugins: source the active plugin set from `claude plugin list --json` instead
   of `_plugin_paths()`. Keep `installPath` for locating `skills/`,
   `commands/`, `agents/`. **Filter to `enabled == true`.** Fall back to the
   current file-scrape only if the CLI is unavailable.
3. Live sessions: source `live_sessions()` from `claude agents --json` (map
   `status`/`state` → active). Keep `os.kill` PID scraping only as fallback.
4. Skills view: keep the personal + project + plugin scans that have no CLI, but
   the plugin arm now derives from the CLI-reported install paths + enabled set.

## Acceptance

- Disabled plugins no longer appear in the Skills view (auto-memory absent while
  `enabled:false`; reappears if enabled).
- `live_sessions()` returns the same active session(s) as today when `claude` is
  present; with `claude` absent, behavior is unchanged (file fallback).
- `scripts/check.sh` green; a unit test asserts the enabled-filter and the CLI
  parsing on a captured `claude plugin list --json` fixture.
- README "Notes" updated: plugin/session data comes from supported CLIs, with a
  documented file-scrape fallback.

## Out of scope

- Sessions-index (`recent`/`stale`/`idle` history) and bundled built-in skills —
  no CLI exists; covered by [internal-format-drift-resilience].
