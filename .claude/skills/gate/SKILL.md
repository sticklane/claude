---
name: gate
description: Installs deterministic quality gates in a project - a runtime-neutral check script and git pre-commit gate, plus native lifecycle Stop/format/protected-file hooks for Claude Code, Codex, or Antigravity. Use when the user wants agents to verify work before finishing, says "add quality gates" or "set up hooks", or after /onboard has established the check commands.
argument-hint: "[check command, e.g. 'npm test']"
---

Install gates that make quality checks deterministic instead of advisory.
Instruction files are advice an agent can drift from; `scripts/check.sh` and
the git pre-commit gate execute independently of the agent runtime. The
toolkit's `bin/install-gates` is the installer — never hand-write the files it
generates. It has native lifecycle adapters for Claude Code, Codex, and
Antigravity. Select the active runtime explicitly; never install another
runtime's adapter as a fallback and never launch another agent CLI.
Background on each hook contract is in [reference.md](reference.md).

## 1. Establish the check commands

From the current invocation, the active runtime's repository guidance, or
the build files — then RUN each one to
confirm it works and observe how long it takes (pipe long output through
`tail`, or delegate the run to a subagent — raw logs don't belong in the
main context). Gate rules:

- The Stop-hook check must be fast (seconds, not minutes) and deterministic.
  A flaky or slow gate is worse than none — it teaches everyone to bypass it.
- Prefer the narrowest reliable check (lint + typecheck + affected tests)
  over the full suite; the full suite belongs in CI.

## 2. Install via bin/install-gates

Identify the runtime that invoked this skill as one of `claude-code`, `codex`,
or `antigravity`. Run the toolkit's installer with that exact adapter (dry-run
first, then for real):

    <toolkit>/bin/install-gates --runtime <active-runtime> --dry-run <repo-path>
    <toolkit>/bin/install-gates --runtime <active-runtime> <repo-path>

It detects the stack and tier, generates `scripts/check.sh` and the git
pre-commit hook from `templates/`, installs the Stop / PostToolUse /
PreToolUse hook scripts, merges into the active runtime's existing project
hook config without disturbing it, archives a pre-existing pre-commit hook to
`pre-commit.pre-gates` (aborting rather than overwriting an occupied
archive), and stamps a Checks section into that runtime's guidance file. It is
idempotent — re-running is safe and byte-identical.

| Runtime | Project hook config | Hook scripts | Guidance |
| --- | --- | --- | --- |
| Claude Code | `.claude/settings.json` | `.claude/hooks/` | `CLAUDE.md` |
| Codex | `.codex/hooks.json` | `.codex/hooks/` | `AGENTS.md` |
| Antigravity | `.agents/hooks.json` | `.agents/hooks/` | `AGENTS.md` |

Codex requires project hook trust: after installation, use Codex's `/hooks`
view to review and trust the new definitions. Do not bypass that review on the
user's behalf.

> **The pre-commit hook mechanism is git-specific.** The installer writes a
> **git** pre-commit hook (into `.git/hooks/`), so its commit-time
> enforcement point exists only where the repo is git (or git-colocated). A
> non-colocated jj repo has no git pre-commit hook to install into and needs
> a different enforcement point — a jj-native hook equivalent or another
> pre-write gate — which this skill does not yet provide (documented
> limitation, not solved here). The Stop / PostToolUse / PreToolUse hooks are
> harness-level and runtime-specific, not VCS-specific. Install only the
> adapter the active runtime actually supports.

What it installs (semantics in reference.md):

1. **Stop gate**: re-runs `scripts/check.sh` on every stop attempt and
   asks the active runtime to continue with the failure output as reason.
   The adapter uses native output: Claude Code exit 2, Codex
   `decision:block`, or Antigravity `decision:continue`. Loop safety permits
   the next stop attempt rather than trapping the session. A final message beginning
   with a verdict line (`DEFERRED`, `BLOCKED`, or `INCOMPLETE`) is a
   sanctioned stop the hook lets through — unattended workers stop mid-red
   by contract, and blocking them would trap them in a loop (mechanism in
   reference.md).
2. **Auto-format**: `PostToolUse` on `Edit|Write` piping the edited file to
   the project's formatter — using the equivalent native file-tool matcher
   and payload under Antigravity.
3. **Protected files**: `PreToolUse` on `Edit|Write` denying edits to
   `.env*`, lockfiles, and `.git/`, again through the active runtime's native
   decision format.

Hand-config only where the installer doesn't reach: during TDD builds,
optionally protect the project's test glob so the implementing agent cannot
make tests pass by editing them through Edit/Write (Bash writes need a
permission `deny` rule too — the reference covers pairing them). Offer but
don't force session-scoped alternatives (`/goal "<condition>"` for one task
rather than permanent hooks).

## 3. Verify the gates fire

Trigger each hook once and show the evidence: make a formatting-violating
edit (auto-format fixes it), attempt a protected edit (blocked), and end a
turn with a failing check (Stop hook blocks with the failure as reason).
An uninstalled-but-described gate is the trust-then-verify gap in miniature.

Commit the selected runtime's project hook config and hook scripts so the
whole team's agents on that runtime get the same gates; with gates in place,
tasks qualify for an unattended `/goal`-bounded `/build` run (or `/drain` for
a queue). Close with:
`Next stage: /build specs/<slug>/tasks/NN-*.md (human-launched; /goal-bound
it per build/reference.md for an unattended-feeling run)`.
