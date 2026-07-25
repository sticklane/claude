# Waiting-loop tier gate: not buildable on today's hook input

Status: closed — doctrine-only outcome (no mechanism shipped)
Priority: P2
Breakdown-ready: false
Issue: agentic-z7b.1

## Problem

`.claude/rules/token-discipline.md`'s Session refresh section says "A waiting
main loop is a scheduler, not a thinker" — a poller that idles past the
prompt-cache TTL must run cheap-tier, never frontier-tier. That is doctrine
with no mechanical enforcement. The cost is measured, not hypothetical:
`specs/archive/session-refresh-automation/SPEC.md` records 4 watch-then-act
sessions spending $36 of $95 (38%) purely re-warming cache to poll, with no
work done between wakes.

The proposed mechanism was a `PreToolUse` warn-hook on the loop-shaped calls
(`ScheduleWakeup`, `CronCreate`, a `/loop` invocation) that fires only when
the calling session is frontier-tier, and is silent otherwise.

## Finding: the session's model tier is NOT inspectable at that moment

The Claude Code hooks reference settles it against the mechanism. Source:
https://code.claude.com/docs/en/hooks (fetched 2026-07-25).

Verbatim:

> Only [`SessionStart`](#sessionstart) hooks can receive a `model` field, and
> it is not guaranteed to be present.

and, in the same passage:

> There is no `$CLAUDE_MODEL` environment variable.

The documented common input fields every hook receives are `session_id`,
`prompt_id`, `transcript_path`, `cwd`, `permission_mode`, `effort`, and
`hook_event_name`, plus `agent_id` / `agent_type` under `--agent` or inside a
subagent. `PreToolUse` adds only `tool_name`, `tool_input`, and `tool_use_id`.
No member of that set carries a model, model id, or model tier.

This is the same wall that killed the 2026-07-12 Agent-depth warn-hook
recorded in `.claude/rules/token-discipline.md` ("the hook input schema
exposed no dispatch-depth field and no reliable running-agent tier marker"):
one more tier-shaped gate the hook payload cannot express.

### Why the two near-misses do not rescue it

**`effort` is not model tier.** `PreToolUse` does receive an `effort` object
(`"low"`/`"medium"`/`"high"`/`"xhigh"`/`"max"`, also exposed as
`$CLAUDE_EFFORT`), and it is the closest available signal. It is the wrong
one: the doctrine's cost driver is the per-token price of re-warming a fat
context on a frontier model, and a frontier model at `effort: low` pays
frontier cache-write rates all the same. Gating on `effort` would fire on
cheap-tier-at-high-effort sessions (a false positive that trains the warning
away) and stay silent on the exact frontier-at-low-effort poller the rule
targets.

**Persisting `SessionStart`'s `model` into a session-keyed state file, then
reading it from `PreToolUse`, is a guess, not a mechanism.** Two documented
defects:

- The field is optional by spec — "It can be omitted, for example after
  `/clear` or when a session is restored through conversation recovery, so
  check for the field before reading it". A gate whose input is absent on
  every `/clear` is silent exactly where long sessions live.
- The cached value goes stale and the hook cannot know. `SessionStart`'s
  documented sources are `startup`, `resume`, `clear`, `compact`, and `fork`;
  a mid-session `/model` switch is not among them, so a session that starts
  cheap and is switched to a frontier model never re-fires the hook. The
  stored value would then assert "cheap-tier" for a frontier poller — a gate
  that reports the compliant case while the violation runs.

A warn-hook that is silent after `/clear` and wrong after `/model` is worse
than the doctrine line it would replace, because it reads as coverage.

## Decision

No hook shipped. The rule stays doctrine-only, with a one-line pointer to this
spec so the next session that reaches for the same gate finds the finding
instead of re-deriving it (`.claude/rules/token-discipline.md`, Session
refresh section).

## What would unblock it

Any ONE of:

1. A model/model-tier field on the `PreToolUse` hook input (or on the common
   input fields), documented as always present.
2. A `$CLAUDE_MODEL` environment variable visible to hook commands — the docs
   currently deny its existence outright.
3. A `SessionStart`-equivalent event that fires on model change, which would
   make the persist-and-read design sound rather than staleness-prone.

## Re-check trigger

Re-open this spec only when the hooks reference changes. The check is one
command; it passes (exit 0) while the capability is still absent:

```bash
curl -fsSL https://code.claude.com/docs/en/hooks \
  | grep -q 'There is no `\$CLAUDE_MODEL` environment variable'
```

A non-zero exit means the sentence is gone from the docs and the finding above
must be re-derived before any gate is built on it.

## Acceptance criteria

Runnable, from the repo root; each states its expected result.

```bash
# 1. The finding exists on disk.
test -f specs/waiting-loop-tier-gate/SPEC.md                          # exit 0

# 2. It carries the verbatim primary-source citation.
grep -c 'There is no `\$CLAUDE_MODEL` environment variable' \
  specs/waiting-loop-tier-gate/SPEC.md                                # >= 1

# 3. It names the primary source URL.
grep -c 'https://code.claude.com/docs/en/hooks' \
  specs/waiting-loop-tier-gate/SPEC.md                                # >= 1

# 4. The doctrine rule points at the finding.
grep -c 'no model field on PreToolUse' \
  .claude/rules/token-discipline.md                                   # == 1

# 5. No guessed mechanism was shipped: no waiting-loop hook exists.
ls hooks/ | grep -c 'waiting-loop\|loop-tier'                         # == 0

# 6. Nothing outside specs/ and the one rule file changed.
git diff --name-only main...HEAD \
  | grep -cv '^\(specs/waiting-loop-tier-gate/\|\.claude/rules/token-discipline\.md$\)'  # == 0
```

## Out of scope

Enforcing the wake-budget arm (already shipped as `hooks/session-refresh/`),
and any change to `~/.claude/settings.json` or files outside this repo.
