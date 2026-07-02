---
name: distill
description: Captures this session's corrections, surprises, and repeated procedures into CLAUDE.md, rules, or new skills so the next session doesn't repay for them. Use proactively at the end of a task, after the user corrects a mistake, or whenever the same instructions have been given twice.
---

Compounding engineering: every mistake becomes a rule, every repeated
procedure becomes a skill. A session whose learnings die with its context was
partially wasted.

## 1. Harvest

Scan THIS session for:
- Corrections: places the user redirected you, or a verifier/critic caught
  something you'd have shipped.
- Surprises: commands, conventions, or gotchas you discovered the hard way
  (wrong test invocation, hidden config, non-obvious dependency).
- Repetition: instructions given more than once, here or in prior sessions.

## 2. Route each finding

| Finding | Destination |
|---|---|
| Broadly applicable fact/command an agent can't infer from code | `CLAUDE.md` (one terse line) |
| Convention scoped to part of the tree | `.claude/rules/<name>.md` with `paths:` frontmatter |
| Multi-step procedure likely to recur | New skill in `.claude/skills/<name>/SKILL.md` |
| One-off, or inferable from the code itself | Nowhere — write nothing |

Gate every CLAUDE.md addition with: "would removing this line cause a future
agent to make a mistake?" If no, it's bloat — bloated CLAUDE.md files get
ignored and cost tokens every single session.

## 3. Write

- CLAUDE.md: append the terse line under the right heading; if the file
  nears 200 lines, prune something weaker in the same edit.
- New skills: directory-named command, third-person `description` stating
  what it does AND when to use it (concrete trigger phrases), body under 500
  lines, procedures as checklists. Heavy reference material goes in a
  separate file in the skill directory, loaded on demand.
- Show the user a one-line summary per learning captured (or "nothing worth
  keeping" — a valid outcome).
