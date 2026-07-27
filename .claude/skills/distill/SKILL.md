---
name: distill
description: Captures this session's corrections, surprises, and repeated procedures into shared AGENTS.md guidance, memory topics, or portable skills so the next session does not repay for them. Use proactively at the end of a task, after the user corrects a mistake, or whenever the same instructions have been given twice. Trigger phrases - "/distill", "distill this session", "capture what we learned".
model: opus
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

## 1a. Unattended invocation (e.g. from drain)

Distill runs unattended when a stage self-chains into it — drain's terminal
distill has no live human to interview. Use the runtime's native question UI
only where an interactive human is present; when none is
(background/headless), never block on a question — skip the interview
gracefully rather than erroring, and
"nothing worth keeping" stays a valid outcome. A candidate learning that
genuinely needs a human decision is NOT dropped or guessed: file it as a
`decide` entry under the repo-root `HUMAN.md`'s `## Agent-filed blockers`
section (grammar in `.claude/rules/human-blockers.md`, cited not restated) and
name it in the summary.

For an orchestrated run, Harvest (§1) also mines the run's committed artifacts,
not only this session's transcript: task-file `## Decisions` and `## Progress`
entries, critique/gate findings files, screen/sweep incident reports, and
drain's own exit checklist.

## 2. Route each finding

| Finding                                                        | Destination                                                                       |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Broadly applicable fact/command an agent can't infer from code | Root `AGENTS.md` (one terse line)                                                  |
| Too narrow or too long for AGENTS.md, but worth keeping        | Topic file under `docs/memory/`, indexed in `docs/memory.md`                      |
| Convention scoped to part of the tree                          | Root `AGENTS.md`, with the affected path named explicitly                         |
| Multi-step procedure likely to recur                           | `.claude/skills/<name>/SKILL.md` plus a relative `.agents/skills/<name>` symlink |
| One-off, or inferable from the code itself                     | Nowhere — write nothing                                                           |

Gate every AGENTS.md addition with: "would removing this line cause a future
agent to make a mistake?" If no, it's bloat — bloated AGENTS.md files get
ignored and cost tokens every single session.

Work-shaped findings — a bug spotted, doc drift, a scoped follow-up — are
not learnings and don't route through the table above: file each in bd the
moment it surfaces (the repository's Beads guidance, cited not restated),
with a `discovered-from` link where a current issue exists. A distill that ends
with unfiled work-shaped findings has captured the lesson and dropped the
work.

A concrete bad-vs-better EXAMPLE PAIR (a caught piece of bad prose or bad
code with an agreed fix) routes to /example-corpus, not to the table above
— the corpus stores calibration pairs; this skill stores rules.

## 3. Write

- AGENTS.md: append the terse line under the right heading; if the file
  nears 200 lines, prune something weaker in the same edit. Batch all
  AGENTS.md writes into one edit at session end — mid-session guidance
  churn invalidates the cached prompt prefix (see the Cache economics
  section of `.claude/rules/token-discipline.md`).
- Runtime overlays: do not put shared guidance in `CLAUDE.md`,
  `.claude/rules/`, Codex config, or Antigravity config. Use one of those
  only for a fact that genuinely applies to that runtime alone. Preserve an
  existing Claude Code `@AGENTS.md` bridge; never duplicate its imported text.
- Memory layer: AGENTS.md remains the home for always-on shared rules; lessons
  too narrow or too long for it go to a topic file under `docs/memory/`,
  with one line per topic file in the `docs/memory.md` index: path +
  a when-to-read trigger phrase. The index stays ≤200 lines and is
  loaded on demand (when a task matches a topic), never at session
  start. Each time /distill writes to the index, prune stale entries in
  the same edit — topics whose code or convention no longer exists, or
  that AGENTS.md now covers (this manual pass is the layer's only decay
  mechanism).
- New skills: directory-named command, third-person `description` stating
  what it does AND when to use it (concrete trigger phrases), body under 500
  lines, procedures as checklists. Heavy reference material goes in a
  separate file in the skill directory, loaded on demand. Keep the procedure
  canonical under `.claude/skills/` and expose that same directory to Codex
  and Antigravity with a relative `.agents/skills/` symlink; never copy it.
- Show the user a one-line summary per learning captured (or "nothing worth
  keeping" — a valid outcome), then close with:
  `Next stage: none — lessons land in shared guidance, memory, or a portable
  skill`.
