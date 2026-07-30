# gate-scope-warn hook

A **user-level** `Stop` hook that tells you when the repository you are working
in is gated but its gate never loaded.

## The gap it closes

Claude Code reads project hooks from the session's project directory. A session
launched at `$HOME` that then works in `~/claude` gets none of
`~/claude/.claude/settings.json`'s hooks — not its Stop gate, not its
bd-compliance check, not its formatter.

Nothing announces that. The gate is not bypassed and no error is raised; it was
simply never there. Measured 2026-07-29 on this machine: a session whose
project root was `/Users/sjaconette` landed **21 commits in `~/claude` with zero
Stop-hook runs**, while the repository's git `pre-commit` review gate fired on
every single one. Git hooks are repository-scoped and Claude Code hooks are
session-scoped, so the weak gate — a self-review the committing agent records
for itself — stayed loud while the strong gate stayed silent. Reading the
commit log afterwards, every commit looks reviewed.

This has to be wired at user level. A project hook cannot warn you about
project hooks that did not load.

## What it does

Prints to stderr and exits 0 when **all** of these hold:

- the session's `cwd` resolves to a git root,
- that root has a readable `scripts/check.sh`,
- that root's `.claude/settings.json` declares at least one `Stop` hook, and
- that root is not `$CLAUDE_PROJECT_DIR`.

The message names the repository, says its gate has not run, and gives both
remedies: run `scripts/check.sh` by hand, or restart the session with that
repository as its project root.

Silent in every other case, including a correctly-scoped session, a repository
with no gate installed, a repository with a check script but no Stop hook of
its own (nobody asked for a gate there), and `stop_hook_active: true`.

## What it does NOT do

**It never blocks.** It reports a gap that already happened — the commits are
made by the time a Stop hook runs — so exiting non-zero would trap the session
without undoing anything. Warn-only follows `hooks/loop-tier-warn/`'s
precedent.

**It does not run the check for you.** Running an arbitrary repository's
`scripts/check.sh` from a user-level hook would fire in every repo you visit,
including one another session is actively working in. Deciding whether a
blocking or auto-running mode is wanted is tracked separately.

**It does not detect which repositories you committed to.** It reports on the
repository containing the session's `cwd` at Stop time. A session that commits
in one repo and ends in another is not covered.

## Requirements

- `jq` on `PATH`. Absent, the hook is a silent no-op, like every other
  fail-open path here: a broken advisory must never break a stop.

## Wiring (user level, one step)

Add to `~/.claude/settings.json` — **not** a project `settings.json**, which is
the exact scoping this hook exists to detect:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/claude/hooks/gate-scope-warn/scope-check.sh"
          }
        ]
      }
    ]
  }
}
```

## Tests

```sh
bash hooks/gate-scope-warn/test.sh     # authoritative cases
bash tests/test_gate_scope_warn.sh     # the same suite, inside scripts/check.sh
```

The suite drives the hook against throwaway fixture repositories under
`mktemp -d`, covering the mismatch, the correctly-scoped case, both
not-my-business cases, loop protection, subdirectory resolution, and every
fail-open path. It never reads real session data.

`scripts/check.sh` enumerates root `tests/test_*.sh` only, so the root wrapper
is what puts these cases inside the gate — a hook-local `test.sh` alone is a
suite the gate never runs.
