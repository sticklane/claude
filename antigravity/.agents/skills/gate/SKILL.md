---
name: gate
description: Installs deterministic quality gates in a project via Antigravity hooks - auto-format/lint after edits, protected-file denies, and command blocking. Use when the user wants automatic checks on agent work, says "add quality gates" or "set up hooks", or after onboarding establishes the check commands.
---

Install hooks that make quality checks deterministic instead of advisory.
AGENTS.md instructions are advice an agent can drift from; hooks execute
every time. Exact JSON and script templates are in [reference.md](reference.md)
— read it before writing any config.

## 1. Establish the check commands

From the user, AGENTS.md, or the build files — then RUN each one to confirm
it works and observe how long it takes (pipe long output through `tail`, or
delegate the run to a subagent — raw logs don't belong in the main context).
A flaky or slow gate is worse than none. Prefer the narrowest reliable
check (lint + typecheck + affected tests); the full suite belongs in CI.

## 2. Install (per reference.md)

1. **Post-edit check**: a `PostToolUse` hook on the file-writing tools that
   formats the edited file and runs the linter, feeding failures back to
   the agent as context.
2. **Protected files**: a `PreToolUse` hook denying writes to `.env*`,
   lockfiles, and generated code. During TDD tasks, optionally add the test
   glob so the implementing agent can't make tests pass by editing them
   (shell writes need the terminal deny list too).
3. **Command blocking**: a `PreToolUse` hook on `run_command` denying
   dangerous patterns — this backs up the Terminal Execution Policy deny
   list with something that lives in the repo.
4. Note what Antigravity does NOT have: a per-turn Stop gate (its Stop
   event fires at session end). The "done means verified" gate here is the
   artifact system: keep the implementation-plan review pause ON for core
   work, and require walkthrough artifacts to contain command output as
   evidence (the verifier skill checks this). A session ending with a
   verdict line (`DEFERRED`, `BLOCKED`, `INCOMPLETE`) is a sanctioned stop,
   not a failed exit — unattended workers stop mid-red by contract
   (details in reference.md).

## 3. Verify the gates fire

Trigger each hook once and show the evidence: a formatting-violating edit
(fixed), a protected-file write (denied), a denied command (blocked). An
uninstalled-but-described gate is the trust-then-verify gap in miniature.

Files land in `.agents/hooks.json` + `.agents/hooks/*.sh` — commit both so
the whole team's agents get the same gates.

`Next stage: /build specs/<slug>/tasks/NN-*.md (human-launched; run it
bounded per build.md's "Bounded, walk-away runs" for an unattended-feeling
run)`.
