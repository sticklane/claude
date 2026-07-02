---
name: distill
description: Captures this conversation's corrections, surprises, and repeated procedures into AGENTS.md or new skills so the next conversation doesn't repay for them. Use at the end of a task, after the user corrects a mistake, or whenever the same instructions have been given twice.
---

Compounding engineering: every mistake becomes a rule, every repeated
procedure becomes a skill. A conversation whose learnings die with its
context was partially wasted. (Antigravity's auto knowledge base is
best-effort — write learnings explicitly; don't rely on auto-capture.)

## 1. Harvest

Scan THIS conversation for:
- Corrections: places the user redirected you, or a review caught something
  you'd have shipped.
- Surprises: commands, conventions, or gotchas discovered the hard way.
- Repetition: instructions given more than once, here or in prior sessions.

## 2. Route each finding

| Finding | Destination |
|---|---|
| Broadly applicable fact/command an agent can't infer from code | `AGENTS.md` (one terse line) |
| Convention scoped to part of the tree | nested `AGENTS.md` in that subdirectory |
| Multi-step procedure likely to recur | New skill in `.agents/skills/<name>/SKILL.md` |
| A procedure only humans should trigger | New workflow in `.agents/workflows/<name>.md` |
| One-off, or inferable from the code itself | Nowhere — write nothing |

Gate every AGENTS.md addition with: "would removing this line cause a
future agent to make a mistake?" If no, it's bloat — a bloated AGENTS.md
gets ignored and costs tokens every conversation.

## 3. Write

- AGENTS.md: append the terse line under the right heading; if the file
  nears 200 lines, prune something weaker in the same edit.
- New skills: `description` in third person stating what it does AND when
  to use it (concrete trigger phrases); body under 500 lines; heavy
  reference material in a separate file in the skill directory.
- Show the user a one-line summary per learning captured (or "nothing worth
  keeping" — a valid outcome).
