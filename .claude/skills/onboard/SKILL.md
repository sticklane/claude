---
name: onboard
description: Prepares an existing repository for agentic development - scouts the codebase, writes a concise CLAUDE.md with verified commands, adds a permission allowlist, and offers quality gates. Use on first contact with a repo, or when the user says "set this repo up for Claude", "make this codebase agent-ready", or "bootstrap CLAUDE.md".
---

Make this repo a place where agents can work reliably. The default deliverable
is the orientation split: a root `AGENTS.md` carrying orientation (`## Repo map`,
`## Commands` verified by running, `## State`) and a `CLAUDE.md` carrying
conventions with an `@AGENTS.md` bridge line in its first 10 lines — both ≤200
lines. AGENTS.md is the one context file Codex, Jules, Kiro, and Copilot read
natively and Claude Code imports via the bridge; CLAUDE.md never repeats what
AGENTS.md already says. Add permissions that match how the team works, and
(optionally) gates. Everything else agents can discover themselves.

## 1. Scout

Fan out parallel `scout` agents (do not read the tree into this session):
build system and candidate commands; architecture map (top modules, entry
points); conventions that differ from language defaults; any existing
`.claude/` config, CLAUDE.md, or CI workflows to align with.

## 2. Verify before writing

RUN every command that will go into AGENTS.md's `## Commands` — install, build,
test, lint — and record the real invocations and their quirks (slow suites,
required env vars, flaky tests). Orientation that lies is worse than none: every
future session inherits the lie. Two cautions:

- First contact means untrusted code: confirm with the user before running
  install hooks or long/side-effectful suites, and timebox anything slow.
- Keep raw logs out of the main context — pipe through `tail`, or delegate
  the runs to a subagent that reports command + exit status + quirks only.

## 3. Write the split

Both files target well under 200 lines and pass, per line, "would removing this
cause an agent to make a mistake?" Exclude from both: standard language
conventions, anything readable from the code, file-by-file tours, "write clean
code" platitudes. If a section is becoming a procedure, it should be a skill.

**AGENTS.md — orientation, no rules.** The context file every tool reads:

- A one-paragraph purpose line: what the repo is.
- `## Repo map`: one pointer line per top-level area — path plus one clause on
  what lives there; mark generated/vendored dirs "generated — don't read".
  Pointers only; the file-by-file exclusion still applies.
- `## Commands`: the verified commands from §2 (with their quirks).
- `## State`: where open work lives — `specs/` and task `Status:` headers and
  the status script if the repo uses the spec pipeline, else `docs/TASKS.md`,
  else "no task tracking".

**CLAUDE.md — conventions, gotchas, checks.** Its first 10 lines carry the
`@AGENTS.md` bridge line (Claude Code imports AGENTS.md through it) so
orientation is never duplicated here:

- Conventions an agent can't infer from the code.
- Architecture facts that prevent wrong-place edits ("API handlers live in X;
  generated code in Y — never edit").
- Known gotchas and the repo's check command.
- Optional: if the repo is ever edited by more than one live session in the
  same non-worktree checkout, a bullet pointing at the concurrent-sessions
  pre-flight pattern (this toolkit's `.claude/rules/concurrent-sessions.md`).

**Already-onboarded repo (migration).** A CLAUDE.md exists with no AGENTS.md, or
a template-debris AGENTS.md lacking `## Repo map`: move the orientation content
(map, commands, state) out of CLAUDE.md into a fresh AGENTS.md under the three
section names, add the `@AGENTS.md` bridge line to CLAUDE.md, and delete the
now-duplicated prose — CLAUDE.md keeps only conventions and gotchas.

Monorepos and large repos: subsystem detail belongs in per-directory AGENTS.md
files, which load on demand when an agent reads files there — the root map
stays small.

## 4. Permissions

`.claude/settings.json` allowlist covering exactly the verified commands
(test/lint/build, plus staging and committing) with a `deny` on publishing
to the remote (e.g., under git: `git push`) — the build
skill's reference.md (in-repo at .claude/skills/build/reference.md, or
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

Close by reporting what was created and each command's verification
evidence, ending with:
`Next stage: /idea <first feature> (human-launched)`.
