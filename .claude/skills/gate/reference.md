# Quality-gate lifecycle adapters

`bin/install-gates` owns generated gate files. This reference explains the
runtime contracts behind them; do not copy these descriptions into a target
repo by hand.

## Table of contents

Installed layers · Runtime selection · Stop gate · Protected files ·
Auto-format · Beads compliance · Operational checks

Verified in July 2026 against the current official hook documentation for
[Claude Code](https://code.claude.com/docs/en/hooks),
[Codex](https://learn.chatgpt.com/docs/hooks), and
[Antigravity](https://antigravity.google/docs/hooks).

## Installed layers

Every non-generic project gets two runtime-independent layers:

- `scripts/check.sh`, the canonical project check.
- The git pre-commit hook, containing only fast staged-file checks.

Every project also gets native protected-file and auto-format lifecycle hooks.
Non-generic projects get a Stop gate. A repo containing `.beads/` gets the
bd-compliance Stop hook as a separate handler. Generic projects have no
canonical check, so they do not get the quality Stop gate.

| Runtime | Config | Scripts | Guidance |
| --- | --- | --- | --- |
| Claude Code | `.claude/settings.json` | `.claude/hooks/*.sh` | `CLAUDE.md` |
| Codex | `.codex/hooks.json` | `.codex/hooks/*.sh` | `AGENTS.md` |
| Antigravity | `.agents/hooks.json` | `.agents/hooks/*.sh` | `AGENTS.md` |

The installer merges existing JSON opaquely, keeps unrelated hooks and
top-level keys, and appends only missing agentic handlers. Re-running the same
runtime is byte-idempotent.

## Runtime selection

Pass `--runtime claude-code|codex|antigravity`. `AGENTIC_RUNTIME` is the
non-interactive equivalent; an explicit flag wins. An unknown runtime is an
error. The installer never invokes an agent CLI and never installs a
different runtime as fallback.

Claude Code remains the default only for backward compatibility with older
direct installer calls. A skill invocation must pass its active runtime
explicitly.

## Stop gate

The shared `templates/stop-gate.sh` reads the active runtime's native payload,
finds the repo root, and runs `scripts/check.sh`. Its result translation is:

| Runtime | Block/continue result | Allow result | Loop signal |
| --- | --- | --- | --- |
| Claude Code | failure text on stderr, exit 2 | exit 0 | `stop_hook_active` |
| Codex | `{"decision":"block","reason":"…"}` | `{}` | `stop_hook_active` |
| Antigravity | `{"decision":"continue","reason":"…"}` | `{"decision":"allow"}` | `executionNum` |

The adapter permits the next stop attempt after one forced retry. This is
deliberate loop safety, so describe the behavior as a one-retry gate rather
than “cannot stop until green.” Antigravity also permits stop handling when
`fullyIdle` is false; active background work is not a completed session.

An unattended worker can make a sanctioned mid-red stop by beginning its final
message with `DEFERRED`, `BLOCKED`, or `INCOMPLETE`. Codex supplies
`last_assistant_message` directly. Claude Code supplies a transcript path.
Antigravity does not expose a stable final-message field, so its one-retry cap
is the hard loop boundary.

The gate fails open only when its input is unusable, `jq` is unavailable, or
`scripts/check.sh` is missing/unreadable. A real non-zero check result is
always translated into the runtime's native continuation result.

## Protected files

`templates/pre-tool-protect.sh` denies `.env*`, lockfiles, and `.git/` paths.
It extracts edited paths from:

- Claude Code: `.tool_input.file_path`.
- Codex: every `Add File`, `Update File`, `Delete File`, and `Move to` header
  in the native `apply_patch` command.
- Antigravity: `.toolCall.args.TargetFile` for
  `write_to_file`, `replace_file_content`, and
  `multi_replace_file_content`.

Claude Code blocks with exit 2. Codex returns
`hookSpecificOutput.permissionDecision: "deny"`. Antigravity returns
`decision: "deny"`. Unparseable inputs fail open with a warning.

This covers native file-edit tools, not arbitrary shell writes. If protection
must be hard, pair it with the active runtime's command permissions. A
session-scoped TDD variant may add the project's test glob after failing tests
are committed, then remove it for test-authoring work.

## Auto-format

`templates/post-tool-format.sh` uses the same native path extraction and runs
the matching project formatter:

- Python: `ruff format`, falling back to `uvx ruff format`.
- Go: `gofmt -w`.
- Web/config formats: repo-local Prettier, falling back to
  `npx --no-install prettier`.

Codex can edit several files in one `apply_patch`; each parsed target is
formatted. Current Antigravity `PostToolUse` input does not include the tool
call. The paired PreToolUse hook therefore records the allowed `TargetFile`
under a conversation-scoped temporary name, and PostToolUse consumes and
removes it. Antigravity PostToolUse always emits the required `{}` response.

Formatting is fail-open and never reverses an already-completed edit.

## Beads compliance

For repos with `.beads/`, the installer copies
`hooks/bd-compliance/check.sh` beside the other runtime hooks and registers it
as a separate Stop handler. It uses the same runtime-specific Stop result
translation as the quality gate. Separate handlers matter because one check
guards project quality while the other guards claimed issue state.

## Operational checks

- `jq` must be available.
- Installed scripts are mode 755.
- Codex project hooks require the user to review and trust their exact
  definitions through `/hooks`; installation must not bypass that review.
- Trigger protection, formatting, and a failing Stop check once before
  trusting the setup.
- Do not mix one runtime's input fields or result schema into another
  runtime's config.
- Do not shell out to Claude Code, Codex, or Antigravity from an adapter.
