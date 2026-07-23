# session-refresh hook

A `UserPromptSubmit` hook that flags a session running over its wake budget.
On every prompt submit it reads `transcript_path` from the hook's own stdin
payload and computes the budget directly from that one transcript file — no
`agentprof` dependency, no shelling out to a separate process, no windowed
re-parse of transcript history (2026-07-23 decoupling: `agentprof` stays the
tool for general cost-attribution digging; this guardrail only needs to be
cheap and always available).

The budget arms and their rationale live in `.claude/rules/token-discipline.md`
under "Session refresh". Defaults: **250k-token context size** or **3
re-primes**.

## What it does

- Silent (empty stdout, exit 0) under budget, on any parse error, and when
  `jq` is absent or `transcript_path` is missing/unreadable — a broken
  guardrail must never break a prompt.
- Reads the session's own transcript (a JSONL file, one line per turn) and
  scans its main-loop (`isSidechain` false) assistant lines that carry a
  `usage` object, in file order:
  - **Context-size arm** — the most recent such line's
    `input_tokens + cache_read_input_tokens` is this turn's live context
    size. This is exactly `agentprof`'s own "ctx" definition
    (`agentprof/internal/costsummary/costsummary.go`), mirrored rather than
    reinvented so the two tools stay conceptually consistent — but it is a
    single live reading of the current turn, not a percentile over a
    window like `agentprof`'s `p90_ctx`.
  - **Re-prime arm** — counts how many main-loop calls past the first show a
    `cache_creation_input_tokens` spike past `REFRESH_REPRIME_THRESHOLD`, the
    same labeling rule and default `agentprof` uses for its `reprime_count`
    (`agentprof/internal/claude/claude.go`).
- Injects the directive when either arm is past budget. Injects text only;
  it never ends the session or kills work. The session (or its human) acts
  on the directive.
- A malformed or truncated trailing transcript line (the file mid-write when
  the hook fires) does not blank out the read — lines before it still drive
  the computation.

## Requirements

- `jq` on `PATH`. That's it — no external binary, no build step.

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

| Variable                    | Default  | Meaning                              |
| --------------------------- | -------- | ------------------------------------ |
| `REFRESH_CTX_BUDGET`        | `250000` | context-size arm (tokens)            |
| `REFRESH_REPRIME_BUDGET`    | `3`      | re-prime count arm                   |
| `REFRESH_REPRIME_THRESHOLD` | `50000`  | cache-creation spike ceiling that labels one call a re-prime |

## Tests

```sh
bash hooks/session-refresh/test.sh
```

The tests drive the hook against synthetic transcript JSONL fixtures
(`fixtures/`), covering both over-budget arms, sidechain-usage exclusion, a
malformed trailing line, the under-budget and missing-transcript-path
no-ops, and the missing-`jq` no-op. They never read real session data.
