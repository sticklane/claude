---
description: Prepare an existing repo for agentic development (verified AGENTS.md, guardrails)
---

Use the onboard skill (.agents/skills/onboard/SKILL.md) and follow it exactly, applying it to whatever arguments follow the command. If no arguments were given and the skill needs a target, ask for it.

Indexed-repo note: when the target repo is indexed (a `.context/` directory at its root, or `ctx` resolving on PATH), make sure the guardrails leave `ctx` structure queries runnable — the Claude-Code allowlist analog is `Bash(ctx *)` — so agents run the code-structure index (`ctx tree`/`sig`/`refs`/`deps`) index-first instead of grepping. Antigravity has no checked-in permissions allowlist, so this is a Terminal Execution Policy guardrail check (don't deny-list `ctx`), not a new allowlist entry.
