# session-refresh hook

A `UserPromptSubmit` hook that flags a session running over its wake budget.
On every prompt submit it reads the session id from the hook's stdin payload,
asks `agentprof` for that session's re-prime count and p90 main-loop context,
and — past either arm of the wake budget — injects a directive telling the
session to write a `/handoff` and end rather than carrying its accumulated
context into another cache-re-priming wake.

The budget arms and their rationale live in `.claude/rules/token-discipline.md`
under "Session refresh"; agentprof owns the re-prime definition (this hook
never re-implements it). Defaults: **3 re-primes** or a **250k-token p90
context**.

## What it does

- Silent (empty stdout, exit 0) under budget, on any agentprof error, and when
  the `agentprof` binary or `jq` is absent — a missing profiler must never
  break a prompt.
- Injects the directive only when `reprime_count >= 3` **or** `p90_ctx >=
  250000` for the current session.
- Injects text only; it never ends the session or kills work. The session (or
  its human) acts on the directive.

## Requirements

- `jq` on `PATH`.
- The `agentprof` binary on `PATH` (or its path in `AGENTPROF_BIN`). Build it
  with `cd agentprof && go build -o agentprof .` and put it on `PATH`, or
  point `AGENTPROF_BIN` at the built binary. Without it the hook is a no-op.

## Wiring (one user-run step)

This hook ships with the toolkit but is **not** auto-installed. To cover every
repo's sessions, wire it globally in your user settings at
`~/.claude/settings.json`. Add a `UserPromptSubmit` entry pointing at this
script's absolute path (replace `<TOOLKIT>` with the toolkit checkout root):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<TOOLKIT>/hooks/session-refresh/refresh-check.sh"
          }
        ]
      }
    ]
  }
}
```

If `~/.claude/settings.json` already has a `hooks` block, add the
`UserPromptSubmit` array alongside the existing keys (or append this entry to
an existing `UserPromptSubmit` array) rather than replacing the whole block.
Restart or reload sessions for the setting to take effect.

## Tuning

Override the defaults in the hook's environment:

| Variable                 | Default  | Meaning                              |
| ------------------------ | -------- | ------------------------------------ |
| `REFRESH_REPRIME_BUDGET` | `3`      | re-prime count arm                   |
| `REFRESH_CTX_BUDGET`     | `250000` | p90 context-token arm                |
| `REFRESH_SINCE_DAYS`     | `2`      | agentprof `--since` look-back window |
| `AGENTPROF_BIN`          | —        | explicit agentprof path              |

## Tests

```sh
bash hooks/session-refresh/test.sh
```

The tests drive the hook against synthetic summary fixtures via a fake
`agentprof` double (`fixtures/`), covering both over-budget arms, the
under-budget and session-absent no-ops, and the missing/erroring-binary
no-ops. They never read real session data.
