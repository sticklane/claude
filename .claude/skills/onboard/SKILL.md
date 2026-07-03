---
name: onboard
description: Prepares an existing repository for agentic development - scouts the codebase, writes a concise CLAUDE.md with verified commands, adds a permission allowlist, and offers quality gates. Use on first contact with a repo, or when the user says "set this repo up for Claude", "make this codebase agent-ready", or "bootstrap CLAUDE.md".
---

Make this repo a place where agents can work reliably. The deliverables are
a CLAUDE.md that never lies, permissions that match how the team actually
works, and (optionally) gates. Everything else agents can discover themselves.

## 1. Scout

Fan out parallel `scout` agents (do not read the tree into this session):
build system and candidate commands; architecture map (top modules, entry
points); conventions that differ from language defaults; any existing
`.claude/` config, CLAUDE.md, or CI workflows to align with.

## 2. Verify before writing

RUN every command that will go into CLAUDE.md — install, build, test, lint —
and record the real invocations and their quirks (slow suites, required env
vars, flaky tests). A CLAUDE.md that lies is worse than none: every future
session inherits the lie. Two cautions:

- First contact means untrusted code: confirm with the user before running
  install hooks or long/side-effectful suites, and timebox anything slow.
- Keep raw logs out of the main context — pipe through `tail`, or delegate
  the runs to a subagent that reports command + exit status + quirks only.

## 3. Write CLAUDE.md

Target well under 200 lines; it's re-sent every session. Include only what
passes "would removing this line cause an agent to make a mistake?":

- Verified commands (with the quirks discovered above).
- Conventions an agent can't infer from the code.
- Architecture facts that prevent wrong-place edits ("API handlers live in
  X; generated code in Y — never edit").
- Known gotchas.

Exclude: standard language conventions, anything readable from the code,
file-by-file tours, "write clean code" platitudes. If a section is becoming
a procedure, it should be a skill instead.

## 4. Permissions

`.claude/settings.json` allowlist covering exactly the verified commands
(test/lint/build, git add/commit) with `deny` on `git push` — the autopilot
skill's reference.md (in-repo at .claude/skills/autopilot/reference.md, or
in the agentic plugin's install directory) has the template and
syntax rules. Merge into any existing settings file rather than overwriting,
and keep denies that would annoy attended sessions (like WebFetch) out of
the shared file — those belong in a personal settings.local.json autonomy
profile.

## 5. Offer the next layer

Ask which the user wants now (don't install unasked):
- `/gate` — Stop-hook check gate, auto-format, protected files. It runs the
  toolkit's `bin/install-gates` (hooks generated from `templates/`, merged
  into existing settings, idempotent) rather than hand-writing hooks.
- `REVIEW.md` — repo-specific code-review tuning (severity redefinitions,
  nit caps, skip rules like "anything CI already enforces"). Note the scope:
  it's read by the managed GitHub Code Review service; for the local
  `/code-review` command, review rules belong in CLAUDE.md instead.

Close by reporting what was created, each command's verification evidence,
and the suggested first move: `/idea` for new work.
