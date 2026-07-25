# loop-tier-warn hook

A `PreToolUse` hook that warns — never blocks — when a frontier-tier main
loop is about to become a waiting loop. It fires on the loop-shaped tool
calls (`ScheduleWakeup`, `CronCreate`), reads the session's own model off
the transcript named in the hook payload's `transcript_path`, and injects
an advisory (`hookSpecificOutput.additionalContext`) naming the cheap-tier
alternative when that model matches the frontier pattern. The doctrine it
enforces lives in `.claude/rules/token-discipline.md` under "Session
refresh"; the design finding lives in
`specs/waiting-loop-tier-gate/SPEC.md`.

## What it does

- Silent (empty stdout, exit 0) on a non-loop tool, a cheap-tier model, and
  every failure path — no `jq`, missing/unreadable `transcript_path`, a
  malformed transcript, no model entry yet. A broken guardrail must never
  break a tool call.
- Reads the last main-loop (`isSidechain` false) assistant entry's
  `message.model` from the transcript — the same transcript-read shape as
  `hooks/session-refresh/refresh-check.sh`. Each turn's entry records the
  model that produced it, so the read survives `/model` switches and
  `/clear` (both of which defeat any design caching `SessionStart`'s
  optional `model` field).
- On a frontier match, emits advisory JSON only. It never emits a
  `permissionDecision`; the tool call always proceeds.

## Trigger surface

`ScheduleWakeup` and `CronCreate` are the tool-call surfaces of the
session-scoped scheduled wakeups the hooks reference documents — its Stop
input's `session_crons` entries are "sourced from `CronCreate`,
`ScheduleWakeup`, and `/loop`". A `/loop` invocation is a slash command,
not a tool call, so it reaches this hook through the wakeup calls it
issues, not through a matcher of its own.

## Known limitation

The hooks reference notes the transcript "may lag the in-memory
conversation", so the model read can be one turn stale — e.g. on the first
loop call immediately after a `/model` switch. Accepted for a warn-only
hook; the next loop call re-reads the live value.

## Wiring (one user-run step)

This hook ships with the toolkit but is **not** auto-installed. Wire it in
your user settings at `~/.claude/settings.json` (replace `<TOOLKIT>` with
the toolkit checkout root):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "ScheduleWakeup|CronCreate",
        "hooks": [
          {
            "type": "command",
            "command": "<TOOLKIT>/hooks/loop-tier-warn/tier-check.sh"
          }
        ]
      }
    ]
  }
}
```

If `~/.claude/settings.json` already has a `hooks` block, add this entry
alongside the existing keys (or append it to an existing `PreToolUse`
array) rather than replacing the whole block. The script also gates on
`tool_name` itself, so a broader matcher stays safe. Restart or reload
sessions for the setting to take effect.

## Tuning

| Variable                     | Default | Meaning                                                        |
| ---------------------------- | ------- | -------------------------------------------------------------- |
| `LOOP_TIER_FRONTIER_PATTERN` | `fable` | case-insensitive ERE matched against the transcript's model id |

The default is the frontier-tier family pin from `runtimes/claude-code.md`.

## Tests

```sh
bash hooks/loop-tier-warn/test.sh
```

Also run by `scripts/check.sh` via `tests/test_loop_tier_warn_hook.sh`.
