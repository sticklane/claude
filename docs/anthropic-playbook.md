# How Anthropic builds with Claude Code — the playbook

A distillation of Anthropic's published material on how their own teams use
Claude Code, current as of July 2026. This is the reference the toolkit in
this repo is built from; each section cites its sources (index at bottom).

## Headline facts

- ~90% of Claude Code's own code is written by Claude Code; company-wide
  estimates run 70–90%, with ~80% of new production code Claude-authored
  [S12, S13].
- Boris Cherny (Claude Code's creator) reports 100% of his code has been
  Claude-written since late 2025 — progression: 20% at launch (Feb 2025) →
  30% (May 2025) → 100% (Nov 2025) [S12, S10].
- The core doctrine behind all of it: **"the context window is the most
  important resource to manage"** [S2] and **"give Claude a way to verify its
  work — it will 2–3x the quality of the final result"** [S10].

## The canonical workflows

### 1. Explore → Plan → Code → Commit [S2]

The flagship loop for uncertain or multi-file work:

1. **Explore** in plan mode — Claude reads and answers questions, changes nothing.
2. **Plan** — ask for a detailed implementation plan; edit it directly
   (Ctrl+G) before approving. Escalate thinking on hard design points
   ("think" < "think hard" < "ultrathink").
3. **Implement** against the plan; write tests; run them; fix.
4. **Commit** with a descriptive message; open a PR.

Explicit caveat: **skip planning when you could describe the diff in one
sentence**. Planning overhead on trivial changes is waste. (Frontier note:
by mid-2026 Boris skips plan mode entirely in favor of auto mode plus
verification gates [S10]; the docs still teach it as the default.)

### 2. Verification-first / closed-loop TDD [S2, S10]

"Claude stops when the work *looks* done. Without a check it can run, 'looks
done' is the only signal." The escalation ladder:

- In the prompt: "run the tests after implementing".
- Session-wide: a `/goal` condition re-checked every turn.
- Deterministic: a Stop hook that blocks turn-end until a check script passes.
- Fresh-eyes: a verification subagent that tries to refute the result —
  "the agent doing the work isn't the one grading it."

Classic TDD loop: write failing tests → confirm they fail → commit tests →
implement without touching tests → iterate → commit. Demand **evidence over
assertion**: test output, the command run, a screenshot.

### 3. Interview-to-spec (idea → agent-executable work) [S2]

For larger features: start minimal and have Claude interview you
(AskUserQuestion) about implementation, UX, edge cases, and tradeoffs, "until
we've covered everything, then write a complete spec to SPEC.md" — then
**execute the spec in a fresh session** with clean context. The best specs
are self-contained: they name files and interfaces, state what's out of
scope, and end with an end-to-end verification step. "Time spent making the
spec precise pays off more than time spent watching the implementation."

### 4. Subagent fan-out [S2, S7, S4]

Exploration, test runs, and doc-reading happen in disposable subagent
contexts; only a 1–2k-token summary returns to the main conversation.
Patterns: parallel research across modules, isolating high-volume output
("run the suite, report only failures"), and chained specialists. The
built-in Explore agent runs Haiku and reads excerpts, not whole files.

### 5. Multi-Claude writer/reviewer [S2]

One session implements; a second session with fresh context reviews the diff
against criteria ("report gaps, not style preferences"). Fresh context
matters: a model won't be biased toward code it just wrote. Caveat: a
reviewer prompted to find gaps always finds some — fix what changes behavior,
don't chase everything.

### 6. Parallel sessions, worktrees, and fan-out at scale [S2, S10]

Git worktrees give each session an isolated checkout. Boris runs ~5 local
instances plus 5–10 web sessions, with a dedicated analysis-only worktree.
Batch migrations: generate the task list, then loop `claude -p "migrate
$file ..." --allowedTools ...` headlessly, or fan out to dozens of
worktree-isolated agents each producing its own tested PR.

### 7. Compounding engineering [S10]

"Every single time Claude makes a mistake, I don't tell it to do it
differently. I tell it to write it to the CLAUDE.md, or make a skill... then
Claude can just run forever." Rules of thumb: anything done more than once a
day becomes a skill; the team CLAUDE.md changes multiple times a week;
learnings land in CLAUDE.md as part of the PR that surfaced them.

### 8. Course-correction hygiene [S2, S10]

Esc to stop, rewind to checkpoints, `/clear` between tasks. The key rule:
**after two failed corrections on the same issue, clear and rewrite the
initial prompt** — "a clean session with a better prompt almost always
outperforms a long session with accumulated corrections." Named failure
modes: the kitchen-sink session, correcting-over-and-over, the over-specified
CLAUDE.md, the trust-then-verify gap, infinite exploration.

## How teams apply it [S1]

- **Data Infrastructure**: debugged a Kubernetes outage from dashboard
  screenshots; new hires onboard by pointing Claude at the codebase +
  CLAUDE.md instead of a data catalog.
- **Claude Code team**: autonomous loops for peripheral/prototype work,
  close supervision for core logic (Vim bindings shipped largely autonomously).
- **Security**: stack-trace-driven incident response (~3x faster);
  moved from "design doc → janky code → give up on tests" to Claude-guided TDD.
- **Inference**: writes tests and fixes in unfamiliar languages (Rust).
- **Data Science**: one-shot React/TypeScript dashboards without knowing TS.
- **Growth Marketing**: sub-agent pipeline generating hundreds of ad
  variations from a CSV; **Legal**: non-engineers shipped a phone-tree
  routing prototype.
- Cross-cutting: best results come from augmenting human workflows, treating
  Claude as a thought partner, and sharing discoveries across teams.

## Token-cost doctrine [S2, S4, S8]

- Benchmarks: ~$13/dev/active day average; under $30/day for 90% of users.
  Track with `/usage` and `/context`.
- **Match model to task**: Haiku for search/mechanical subagent work, the
  session model for judgment. Counterpoint: Boris runs Opus for everything
  because less steering often nets out faster [S10] — but he still delegates
  consumption to cheap subagents.
- **Just-in-time retrieval**: pass identifiers (paths, queries), not
  contents; let subagents read and return condensed summaries. Target "the
  smallest set of high-signal tokens that maximizes the likelihood of the
  desired outcome" [S4].
- **Session hygiene**: `/clear` between tasks; directed `/compact`; specs and
  task files on disk as the durable memory, never the conversation.
- **CLAUDE.md is a per-session tax**: keep it under ~200 lines; per line ask
  "would removing this cause mistakes?"; move procedures into skills, which
  load on demand (progressive disclosure: name+description at startup, body
  when invoked, reference files only when needed) [S3, S9].
- Prefer CLI tools over MCP servers where equivalent; plan mode / specs exist
  to avoid the most expensive token sink of all: **implementing the wrong thing**.

## Source index

| # | Source |
|---|--------|
| S1 | How Anthropic teams use Claude Code — https://claude.com/blog/how-anthropic-teams-use-claude-code |
| S2 | Claude Code best practices — https://code.claude.com/docs/en/best-practices |
| S3 | Agent Skills engineering post — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| S4 | Effective context engineering — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| S5 | Building agents with the Claude Agent SDK — https://claude.com/blog/building-agents-with-the-claude-agent-sdk |
| S6 | Skills docs — https://code.claude.com/docs/en/skills |
| S7 | Subagents docs — https://code.claude.com/docs/en/sub-agents |
| S8 | Costs docs — https://code.claude.com/docs/en/costs |
| S9 | Skill authoring best practices — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| S10 | How Boris uses Claude Code — https://howborisusesclaudecode.com/ |
| S11 | GitHub Actions docs — https://code.claude.com/docs/en/github-actions |
| S12 | Fortune, Jan 29 2026 — https://fortune.com/2026/01/29/100-percent-of-code-at-anthropic-and-openai-is-now-ai-written-boris-cherny-roon/ |
| S13 | VentureBeat — https://venturebeat.com/technology/anthropic-says-80-of-its-new-production-code-is-now-authored-by-claude-how-your-enterprise-can-keep-up |
