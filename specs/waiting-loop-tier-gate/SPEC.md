# Waiting-loop tier gate: buildable, shipped as hooks/loop-tier-warn/

Status: implemented — warn-hook shipped (hooks/loop-tier-warn/)
Priority: P2
Breakdown-ready: false
Issue: agentic-z7b.1

## Problem

`.claude/rules/token-discipline.md`'s Session refresh section says "A waiting
main loop is a scheduler, not a thinker" — a poller that idles past the
prompt-cache TTL must run cheap-tier, never frontier-tier. Until this spec
that was doctrine with no mechanical enforcement. The cost is measured, not
hypothetical: `specs/archive/session-refresh-automation/SPEC.md` records 4
watch-then-act sessions spending $36 of $95 (38%) purely re-warming cache to
poll, with no work done between wakes.

## Finding: the tier IS inspectable — via the transcript, not a hook field

An earlier revision of this spec concluded the gate could not be built and
closed doctrine-only. That conclusion was wrong. Its premise holds — no hook
input FIELD carries the model. Source:
https://code.claude.com/docs/en/hooks.md (fetched 2026-07-25), verbatim:

> Only [`SessionStart`](#sessionstart) hooks can receive a `model` field, and
> it is not guaranteed to be present. There is no `$CLAUDE_MODEL` environment
> variable.

But the common input fields every hook receives include `transcript_path`,
and the transcript it names records, on every main-loop assistant entry, the
model that produced that turn (`message.model`). Reading the last such entry
answers the tier question at the moment a `PreToolUse` hook fires:

```bash
jq -r 'select(.type=="assistant" and ((.isSidechain // false)==false))
   | .message.model' "$transcript" | tail -1
```

Verified live in this repo (returned the session's actual model id). The
in-repo precedent for exactly this read is
`hooks/session-refresh/refresh-check.sh`, which jq-parses main-loop
assistant lines off its own payload's `.transcript_path`.

This route defeats both objections that killed the `SessionStart`-caching
design the earlier revision considered:

- **Not stale after `/model`** — each turn's entry records the model in
  force for that turn; nothing is cached across the switch.
- **Not absent after `/clear`** — the read is from assistant entries, not
  from `SessionStart`'s optional `model` field.

The one real caveat is documented on the `transcript_path` row of the hooks
reference ("Common input fields"): the transcript is written asynchronously
and "may lag the in-memory conversation". Worst case is a one-turn-stale
model read on a WARN-only hook — accepted and recorded as a known
limitation in `hooks/loop-tier-warn/README.md`, not a blocker.

`effort` remains the wrong signal (a frontier model at `effort: low` still
pays frontier rates), and is not used.

## Shipped mechanism

`hooks/loop-tier-warn/tier-check.sh` — a `PreToolUse` hook on the
loop-shaped calls `ScheduleWakeup` and `CronCreate` (the tool-call sources
the hooks reference lists for session-scoped scheduled wakeups: its
`session_crons` entries are "sourced from `CronCreate`, `ScheduleWakeup`,
and `/loop`"; `/loop` is a slash command and reaches the hook through the
wakeup calls it issues). The hook:

- reads the payload's `transcript_path`, extracts the last main-loop
  assistant entry's `message.model`, and matches it against the frontier
  pattern (default `fable`, the frontier-tier family pin in
  `runtimes/claude-code.md`; tunable via `LOOP_TIER_FRONTIER_PATTERN`);
- on a match, injects an advisory (`hookSpecificOutput.additionalContext`)
  naming the model and the cheap-tier alternative — it never emits a
  `permissionDecision`, so the call always proceeds (warn, never block);
- is silent (empty stdout, exit 0) in every other case: non-loop tool,
  cheap-tier model, missing jq, missing/unreadable/malformed transcript —
  fail open, per the cache-economics rule that a hook must be silent when
  nothing needs saying.

Wiring is a user-run `~/.claude/settings.json` step documented in
`hooks/loop-tier-warn/README.md`; nothing outside the repo is modified by
the hook itself.

## Re-check trigger

Re-derive the finding if the hooks reference stops documenting the
transcript lag or the model-field absence this design is built around. The
check is one command against the markdown endpoint (the bare URL serves
rendered HTML where backtick literals become `<code>` tags and can never
match); it passes (exit 0) while the documented behavior stands:

```bash
curl -fsSL https://code.claude.com/docs/en/hooks.md \
  | grep -q 'There is no `\$CLAUDE_MODEL` environment variable'
```

## Acceptance criteria

Runnable from the repo root; each tests the behavior of the shipped hook,
not the presence of strings this spec types.

```bash
# 1. The hook's behavior suite passes: it warns for a frontier-tier
#    transcript, stays silent for a cheap-tier one, stays silent on a
#    malformed or missing transcript and on missing jq, and never blocks.
bash hooks/loop-tier-warn/test.sh                                      # exit 0

# 2. Frontier-tier loop call → parseable advisory JSON with no
#    permission decision (behavioral probe, independent of the suite).
printf '{"tool_name":"ScheduleWakeup","transcript_path":"hooks/loop-tier-warn/fixtures/frontier.jsonl","hook_event_name":"PreToolUse"}' \
  | bash hooks/loop-tier-warn/tier-check.sh \
  | jq -e '(.hookSpecificOutput.additionalContext | length > 0)
           and (.hookSpecificOutput | has("permissionDecision") | not)'  # exit 0

# 3. Cheap-tier loop call → zero bytes of output.
printf '{"tool_name":"ScheduleWakeup","transcript_path":"hooks/loop-tier-warn/fixtures/cheap.jsonl","hook_event_name":"PreToolUse"}' \
  | bash hooks/loop-tier-warn/tier-check.sh | wc -c                     # == 0

# 4. The hook is gated by the repo's canonical check (the suite is wired
#    into the tests/test_*.sh glob scripts/check.sh runs).
bash tests/test_loop_tier_warn_hook.sh                                  # exit 0
```

## Out of scope

Enforcing the wake-budget arm (already shipped as `hooks/session-refresh/`),
auto-installing the hook, and any change to `~/.claude/settings.json` or
files outside this repo.
