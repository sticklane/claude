---
name: onboard
description: Prepares an existing repository for agentic development - scouts the codebase, writes a concise AGENTS.md with verified commands, and offers quality gates. Use on first contact with a repo, or when the user says "set this repo up", "make this codebase agent-ready", or "bootstrap AGENTS.md".
---

Make this repo a place where agents can work reliably. The default deliverable
is a root `AGENTS.md` carrying orientation (`## Repo map`, `## Commands` verified
by running, `## State`), ≤200 lines. AGENTS.md is Antigravity's native context
file — there is no separate rules file to bridge into, so conventions and
gotchas live in AGENTS.md alongside the orientation. Add (optionally) gates;
everything else agents can discover themselves.

## 1. Scout

Apply the scout skill (in a separate cheap conversation for big repos):
build system and candidate commands; architecture map (top modules, entry
points); conventions that differ from language defaults; any existing
AGENTS.md/GEMINI.md, `.agents/` config, or CI workflows to align with.

## 2. Verify before writing

RUN every command that will go into AGENTS.md — install, build, test, lint —
and record the real invocations and their quirks (slow suites, required env
vars, flaky tests). An AGENTS.md that lies is worse than none. Two cautions:

- First contact means untrusted code: confirm with the user before running
  install hooks or long/side-effectful suites, and timebox anything slow.
- Keep raw logs out of the conversation — pipe through `tail`, or delegate
  the runs to a separate conversation that reports command + exit status +
  quirks only.

## 3. Write AGENTS.md

Target well under 200 lines; it's loaded every conversation. Include only
what passes "would removing this line cause an agent to make a mistake?":

- A one-paragraph purpose line: what the repo is.
- `## Repo map`: one pointer line per top-level area — path plus one clause on
  what lives there; mark generated/vendored dirs "generated — don't read".
  Pointers only; the file-by-file exclusion still applies.
- `## Commands`: the verified commands from §2 (with their quirks).
- `## State`: where open work lives — `specs/` and task `Status:` headers and
  the status script if the repo uses the spec pipeline, else `docs/TASKS.md`,
  else "no task tracking".
- Conventions an agent can't infer from the code, architecture facts that
  prevent wrong-place edits ("API handlers live in X; generated code in Y —
  never edit"), known gotchas, and the repo's check command — AGENTS.md is
  Antigravity's native context file, so these live here, not in a separate
  rules file.
- Optional: if the repo is ever edited by more than one live session in the
  same non-worktree checkout, a bullet pointing at the concurrent-sessions
  pre-flight pattern (this toolkit's `.claude/rules/concurrent-sessions.md`,
  folded into AGENTS.md's own "Concurrent sessions" section here).

Exclude: standard language conventions, anything readable from the code,
file-by-file tours, platitudes. If a section is becoming a procedure, it
should be a skill instead. Merge with any existing AGENTS.md rather than
overwriting.

Already-onboarded repo (migration): a template-debris AGENTS.md lacking
`## Repo map`, or orientation stranded in another context file — rewrite it
under the three section names and delete the duplicated prose.

Monorepos and large repos: subsystem detail belongs in per-directory
(nested) AGENTS.md files, read nearest-file-wins when an agent works
there — the root map stays small. No separate interop file is needed:
AGENTS.md is already the cross-tool standard and Antigravity's native
context file.

## 4. Guardrails

Walk the user through the Terminal Execution Policy settings (Antigravity
has no checked-in permissions file): recommend Auto mode, plus deny-list
entries for pushing to the remote (e.g., under git: `git push`), deploy commands, and anything destructive, so
unattended runs can't take irreversible actions.

## 5. Offer the next layer

Ask which the user wants now (don't install unasked):
- `/gate` — PostToolUse format/lint hooks in `.agents/hooks.json`.
- Artifact review policy check: implementation-plan pause ON for core work.

Close by reporting what was created, each command's verification evidence,
and the suggested first move: `/idea` for new work.
