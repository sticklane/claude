---
name: onboard
description: Prepares an existing repository for agentic development across Claude Code, Codex, and Antigravity - scouts the codebase, writes concise shared AGENTS.md guidance with a Claude bridge, configures only supported runtime permissions, and offers quality gates. Use on first contact with a repo, or when the user says "set this repo up for agents", "make this codebase agent-ready", or "bootstrap AGENTS.md".
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
- `## State`: where open work lives — bd plus its status command if the repo
  uses the spec pipeline (`specs/` holds definitions and evidence only), else
  `docs/TASKS.md`, else "no task tracking".

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

Configure only the current runtime's native permission surface; never launch
or configure another runtime as a substitute. Claude Code may receive a
`.claude/settings.json` allowlist covering exactly the verified commands
(test/lint/build, plus staging and committing) with a deny on publishing.
Codex uses its sandbox/approval configuration rather than Claude permission
syntax. Antigravity uses its native terminal policy and sandbox; it has no
equivalent checked-in per-command allowlist. The build skill's `reference.md`
and `runtimes/<runtime>.md` own the respective templates. Merge existing
configuration rather than overwriting it, and do not invent a broader grant
to make the shapes look identical.

When Codebase-Memory is installed, configure only the active runtime's native
MCP surface with the toolkit launcher. Add an "Answering structure questions"
section to the repo's **AGENTS.md** that routes architecture, qualified
symbols, callers, dependencies, and impact to Codebase-Memory before scouts
or file reads. Point to the `codebase-memory` skill for its progressive query
ladder and coverage rules. If MCP is unavailable, prescribe `rg` over a
bounded path set plus small reads and require an explicit coverage caveat.

## 5. bd queue setup

Once per machine, before the per-repo steps below (confirm rather than
redo if already present): the `agentic@agentic-toolkit` plugin, and `bd`
pinned 1.1.0 (`brew install beads`).

Per repo:

1. `bd init`, curated: keep the AGENTS.md snippet it writes, gitignore
   `.beads/interactions.jsonl`, and commit the `issues.jsonl` export.
2. `/gate` to install the Stop hook — with `.beads/` present from
   step 1, its installer also copies the bd-compliance check to
   the active runtime's project hook directory and wires it as a separate
   native Stop handler — plus format-on-edit if wanted.
3. Add the active runtime's equivalent of a `bd` command grant to its
   project permissions (§4) — the grant class whose absence measurably
   killed tool adoption before.
4. Seed the queue: file the repo's first epics and issues from
   whatever plan exists, so `bd ready` has answers on day one.

## 6. Offer the next layer

Ask which the user wants now (don't install unasked):

- `/gate` — Stop-hook check gate, auto-format, protected files. It runs the
  toolkit's `bin/install-gates` (hooks generated from `templates/`, merged
  into existing settings, idempotent) rather than hand-writing hooks.
- `REVIEW.md` — repo-specific code-review tuning (severity redefinitions,
  nit caps, skip rules like "anything CI already enforces"). Note the scope:
  it's read by the managed GitHub Code Review service; local agent review
  rules belong in shared `AGENTS.md` guidance unless they are genuinely
  runtime-specific.

Close by reporting what was created and each command's verification
evidence, ending with:
`Next stage: /idea <first feature> (human-launched)`.
