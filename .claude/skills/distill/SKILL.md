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
| Too narrow or too long for CLAUDE.md, but worth keeping | Topic file under `docs/memory/`, indexed in `docs/memory.md` |
| Convention scoped to part of the tree | `.claude/rules/<name>.md` with `paths:` frontmatter |
| Multi-step procedure likely to recur | New skill in `.claude/skills/<name>/SKILL.md` |
| One-off, or inferable from the code itself | Nowhere — write nothing |

Gate every CLAUDE.md addition with: "would removing this line cause a future
agent to make a mistake?" If no, it's bloat — bloated CLAUDE.md files get
ignored and cost tokens every single session.

## 3. Write

- CLAUDE.md: append the terse line under the right heading; if the file
  nears 200 lines, prune something weaker in the same edit. Batch all
  CLAUDE.md writes into one edit at session end — mid-session CLAUDE.md
  churn invalidates the cached prompt prefix (see the Cache economics
  section of `.claude/rules/token-discipline.md`).
- Memory layer: CLAUDE.md remains the home for always-on rules; lessons
  too narrow or too long for it go to a topic file under `docs/memory/`,
  with one line per topic file in the `docs/memory.md` index: path +
  a when-to-read trigger phrase. The index stays ≤200 lines and is
  loaded on demand (when a task matches a topic), never at session
  start. Each time /distill writes to the index, prune stale entries in
  the same edit — topics whose code or convention no longer exists, or
  that CLAUDE.md now covers (this manual pass is the layer's only decay
  mechanism).
- New skills: directory-named command, third-person `description` stating
  what it does AND when to use it (concrete trigger phrases), body under 500
  lines, procedures as checklists. Heavy reference material goes in a
  separate file in the skill directory, loaded on demand.
- Show the user a one-line summary per learning captured (or "nothing worth
  keeping" — a valid outcome), then close with:
  `Next stage: none — lessons land in CLAUDE.md/rules`.
