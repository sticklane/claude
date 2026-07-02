---
name: gate
description: Installs deterministic quality gates in a project - a Stop hook that blocks "done" until the project's checks pass, auto-format on edit, and protected-file rules. Use when the user wants Claude to verify work before finishing, says "add quality gates" or "set up hooks", or after /onboard has established the check commands.
argument-hint: "[check command, e.g. 'npm test']"
---

Install hooks that make quality checks deterministic instead of advisory.
CLAUDE.md instructions are advice an agent can drift from; hooks execute
every time with zero exceptions. Exact JSON and script templates are in
[reference.md](reference.md) — read it before writing any config.

## 1. Establish the check commands

From $ARGUMENTS, CLAUDE.md, or the build files — then RUN each one to
confirm it works and observe how long it takes (pipe long output through
`tail`, or delegate the run to a subagent — raw logs don't belong in the
main context). Gate rules:

- The Stop-hook check must be fast (seconds, not minutes) and deterministic.
  A flaky or slow gate is worse than none — it teaches everyone to bypass it.
- Prefer the narrowest reliable check (lint + typecheck + affected tests)
  over the full suite; the full suite belongs in CI.

## 2. Install (per reference.md)

1. **Stop gate**: a script hook on `Stop` that re-runs the checks on every
   stop attempt and exits 2 with the failure output as reason, so Claude
   keeps working until green. Loop safety is Claude Code's built-in cap —
   it force-ends the turn after 8 consecutive blocks without progress
   (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it).
2. **Auto-format**: `PostToolUse` on `Edit|Write` piping the edited file to
   the project's formatter — style stops consuming review attention.
3. **Protected files**: `PreToolUse` on `Edit|Write` denying edits to
   `.env*`, lockfiles, and generated code. During TDD builds, optionally add
   the project's test glob so the implementing agent cannot make tests pass
   by editing them through Edit/Write (Bash writes need a permission `deny`
   rule too — the reference covers pairing them).
4. Offer but don't force: session-scoped alternatives (`/goal "<condition>"`
  for one task rather than permanent hooks).

## 3. Verify the gates fire

Trigger each hook once and show the evidence: make a formatting-violating
edit (auto-format fixes it), attempt a protected edit (blocked), and end a
turn with a failing check (Stop hook blocks with the failure as reason).
An uninstalled-but-described gate is the trust-then-verify gap in miniature.

Files land in `.claude/settings.json` + `.claude/hooks/*.sh` — commit both
so the whole team's agents get the same gates. Next step: with gates in
place, tasks qualify for `/autopilot`.
