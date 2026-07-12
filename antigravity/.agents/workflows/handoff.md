---
description: Write a self-contained HANDOFF.md and move work to a fresh conversation
---

Use the handoff skill (.agents/skills/handoff/SKILL.md) and follow it exactly, applying it to whatever arguments follow the command. If no arguments were given and the skill needs a target, ask for it.

An autonomous run refreshing under its session-refresh directive uses the same skill's refresh-over-carry path: write the handoff, surface the resume pointer, and end the turn — never spawn a detached continuation (the skill cites the "Awaited children, never detached" policy).
