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

## 1a. Unattended invocation (e.g. from drain)

Distill runs unattended when a stage chains into it — drain's terminal distill
has no live human to interview. Adopt the **"ask where available, else…"** idiom
(the same detection drain uses): interview only where an interactive human is
present; when none is (background/headless), never block on a question — skip
the interview gracefully rather than erroring, and "nothing worth keeping" stays
a valid outcome. A candidate learning that genuinely needs a human decision is
NOT dropped or guessed: file it as a `decide` entry under the repo-root
`HUMAN.md`'s `## Agent-filed blockers` section (the human-blockers grammar) and
name it in the summary.

For an orchestrated run, Harvest also mines the run's committed artifacts, not
only this conversation's transcript: task-file `## Decisions` and `## Progress`
entries, review/gate findings files, screen/sweep incident reports, and drain's
own exit checklist.

## 2. Route each finding

| Finding | Destination |
|---|---|
| Broadly applicable fact/command an agent can't infer from code | `AGENTS.md` (one terse line) |
| Too narrow or too long for AGENTS.md, but worth keeping | Topic file under `docs/memory/`, indexed in `docs/memory.md` |
| Convention scoped to part of the tree | nested `AGENTS.md` in that subdirectory |
| Multi-step procedure likely to recur | New skill in `.agents/skills/<name>/SKILL.md` |
| A procedure only humans should trigger | New workflow in `.agents/workflows/<name>.md` |
| One-off, or inferable from the code itself | Nowhere — write nothing |

Gate every AGENTS.md addition with: "would removing this line cause a
future agent to make a mistake?" If no, it's bloat — a bloated AGENTS.md
gets ignored and costs tokens every conversation.

## 3. Write

- AGENTS.md: append the terse line under the right heading; if the file
  nears 200 lines, prune something weaker in the same edit. Batch all
  AGENTS.md writes into one edit at conversation end — mid-conversation
  AGENTS.md churn invalidates the cached prompt prefix (see the Cache
  economics section of AGENTS.md).
- Memory layer: AGENTS.md remains the home for always-on rules; lessons
  too narrow or too long for it go to a topic file under `docs/memory/`,
  with one line per topic file in the `docs/memory.md` index: path +
  a when-to-read trigger phrase. The index stays ≤200 lines and is
  loaded on demand (when a task matches a topic), never at conversation
  start. Each time distill writes to the index, prune stale entries in
  the same edit — topics whose code or convention no longer exists, or
  that AGENTS.md now covers (this manual pass is the layer's only decay
  mechanism).
- New skills: directory-named command, `description` in third person stating
  what it does AND when to use it (concrete trigger phrases); body under 500
  lines; procedures as checklists; heavy reference material in a separate
  file in the skill directory.
- Show the user a one-line summary per learning captured (or "nothing worth
  keeping" — a valid outcome).

`Next stage: none — lessons land in AGENTS.md/rules`.
