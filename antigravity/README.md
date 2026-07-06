# Using this toolkit with Google Antigravity

Antigravity natively supports the Agent Skills standard (`SKILL.md`, since
Feb 2026) and reads `AGENTS.md`, so most of the toolkit ports directly.
This directory is the ready-to-copy port.

## Install

From your project's root:

```bash
cp -r ~/agentic-toolkit/antigravity/.agents .
cp ~/agentic-toolkit/antigravity/AGENTS.md .        # merge if you have one
git add .agents AGENTS.md && git commit -m "Add agentic development toolkit"
```

(Older Antigravity builds read `.agent/` instead of `.agents/` — if skills
don't appear, copy to `.agent/` as well.) For global install, skills can go
in `~/.gemini/config/skills/`; check your build's path in Customizations.

**Verify**: open the Customizations panel — the skills and workflows should
be listed. Type `/idea` in the agent input to test a workflow.

## What maps to what

| Claude Code version | Antigravity version |
|---|---|
| Skills in `.claude/skills/` | Same skills in `.agents/skills/` (auto-trigger by description) |
| `/idea`, `/build`, etc. slash commands | Workflows in `.agents/workflows/` — same names, same `/command` invocation |
| `CLAUDE.md` + `rules/token-discipline.md` | `AGENTS.md` (always-on by definition) |
| `scout`/`critic`/`verifier` subagents | Skills with the same names + discipline; run them in a **fresh Agent Manager conversation** when fresh eyes matter (review, verification) |
| Hooks in `.claude/settings.json` | `.agents/hooks.json` (different JSON shape — the gate skill's reference has the port) |
| Permission allowlists in settings.json | Terminal Execution Policy (Settings UI): Off/Auto/Turbo + deny list — not a checked-in file |
| `/goal`, Stop-hook gates | Artifact review: implementation plan pause + walkthrough evidence, plus PostToolUse hooks |
| `/fleet` open-agents dashboard | Not ported — Antigravity's Agent Manager is this surface natively |
| `/workboard` cross-repo work dashboard | Ported as-is — it also reads Antigravity's own `brain/` artifacts, covering what the Agent Manager can't see (other tools, specs, git, Claude Code sessions) |
| Skill self-chaining (/idea invokes /breakdown via the Skill tool) | Not ported — workflows are human-launched in the Agent Manager, so the port keeps printed pointers between stages |
| Tier language (scout/session/deep/frontier-tier) + `.claude/runtime.md` tier pins | Same tier vocabulary in `AGENTS.md`; the tier→model mapping is recorded in `runtimes/antigravity.md` (model choice is a human selection in the Agent Manager model picker, not a pinnable flag) |
| Ultracode workflow scripts (`.claude/workflows/*.js`) | Human-dispatched launch-list workflows — no scripted fan-out in Antigravity; the port's existing workflows already express the degraded pattern |
| `workflow-author` skill | Not ported — its entire job is authoring `.claude/workflows/*.js` for the Claude-Code-specific `Workflow` tool, and Antigravity has no scripted fan-out primitive to author against |

The human-launch gates and their rationale: the toolkit repo's
docs/human-gates.md — in Antigravity every workflow is human-launched
natively, so the gates hold by construction.

## What degrades (be aware)

- **No enforced cheap subagents.** Claude Code's scout is Haiku, read-only,
  tool-restricted by config. Antigravity can't statically pin a subagent's
  model/tools; the scout/critic/verifier skills carry the discipline as
  instructions, and fresh-context isolation means opening a new Agent
  Manager conversation yourself (pick a Flash-class model for scouting).
- **Verification gates are softer.** There's no session-scoped `/goal` and
  the Stop hook fires at session end, not turn end. Compensate with: the
  implementation-plan review pause (don't set "Always Proceed" for core
  work), walkthrough artifacts as the evidence record, and PostToolUse
  hooks for lint/format.
- **Permissions aren't in the repo.** Terminal Execution Policy lives in
  the settings UI per machine. For unattended runs, set the deny list
  (push, deploy, rm) there — the autopilot workflow walks through it.
- **Workflow args are free text** (no `$ARGUMENTS` templating) and workflow
  files cap at 12,000 characters.

## Keeping the two ports in sync

The Claude Code files (`.claude/`) are the source of truth. When a skill
changes there, mirror the change here — the bodies are deliberately close
to identical, with platform-specific bits (subagent spawning, hooks JSON,
fresh-session mechanics) swapped out.
