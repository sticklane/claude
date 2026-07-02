# Agentic development toolkit

Skills and subagents that turn raw ideas into agent-executable work, modeled
on how Anthropic's own teams use Claude Code — spec-driven, verification-
gated, subagent-heavy, and deliberately cheap on tokens. The research this is
built from, with citations, lives in [docs/anthropic-playbook.md](docs/anthropic-playbook.md).

## The pipeline

```
 idea ──▶ /idea ──▶ SPEC.md ──▶ /breakdown ──▶ tasks/NN-*.md
                    (critic-                     │
                     reviewed)     ┌─────────────┴─────────────┐
                                   ▼                           ▼
                             /build (one task,          /parallel (independent
                             fresh session)             tasks, worktree agents)
                                   │                           │
                                   └────────── verified ───────┘
                                   (verifier agent, evidence required)
                                               │
                                               ▼
                                           /distill
                              (mistakes → CLAUDE.md, procedures → skills)
```

Each arrow crosses a **file on disk**, not conversation memory — every stage
can (and should) run in a fresh, cheap session.

## What's in the box

| Piece | What it does |
|---|---|
| `/idea` | Interviews you about a raw idea, scouts the codebase, writes an agent-ready `SPEC.md` with runnable acceptance criteria, critic-reviewed |
| `/breakdown` | Splits a spec into one-session task files with dependencies and a parallelization map |
| `/build` | Executes one task: scout-explore → proportional plan → test-first implement → independent verify → commit |
| `/parallel` | Dispatches an independent task group to concurrent worktree-isolated agents |
| `/critique` | Adversarial review of any spec, plan, or diff |
| `/distill` | Compounding engineering: session learnings → CLAUDE.md lines, rules, or new skills |
| `/handoff` | Writes a resume-from-scratch handoff file, then you `/clear` |
| `scout` agent | Haiku, read-only, low effort — answers "where/how does X work" so the main session never reads files to look around |
| `critic` agent | Attacks specs/plans/diffs for ambiguity, missing failure modes, and unverifiable requirements |
| `verifier` agent | Fresh-eyes check of finished work against acceptance criteria; evidence over assertion |
| `rules/token-discipline.md` | Always-loaded token economics: delegate consumption, match model to task, one task per session |

## Why this shape (the Anthropic practices it encodes)

- **Interview-to-spec, then execute in a fresh session** — "time spent making
  the spec precise pays off more than time spent watching the implementation."
- **Verification gates everything** — "give Claude a way to verify its work
  and it will 2–3x the quality of the result." Acceptance criteria are
  runnable commands; a separate agent grades the work ("the agent doing the
  work isn't the one grading it").
- **Subagents protect the context window** — exploration, test noise, and
  review happen in disposable contexts; only conclusions return. The context
  window is the most important resource to manage.
- **One task, one session, one commit** — after two failed corrections,
  restart clean; a better prompt beats a longer session.
- **Compounding engineering** — every mistake becomes a CLAUDE.md line or a
  skill, so no session repays for a lesson already learned.

## Token-cost design

- Scouts run **Haiku at low effort**; the expensive model only ever sees
  their ~300-word reports.
- Skills load **on demand** (only name+description cost anything at session
  start); heavy reference material stays in `docs/`, read only when needed.
- Specs/tasks/handoffs on disk mean sessions stay short and `/clear` is
  always safe — no 200k-token kitchen-sink conversations.
- `/parallel` warns that concurrency multiplies spend and refuses
  non-independent groups.
- The critic runs **before** implementation: a review costs ~1% of building
  the wrong thing.

## Install

- **Per project**: copy `.claude/` into the repo root (skills, agents, and
  rules are all project-scoped and version-controlled — share them with your
  team).
- **Globally**: copy the contents of `.claude/skills/` and `.claude/agents/`
  into `~/.claude/skills/` and `~/.claude/agents/`.
- Specs land in `specs/<slug>/` in whatever repo you run the pipeline in.

## Extending it

Don't add to this toolkit by hand — use it on itself: when you correct Claude
twice about the same thing, run `/distill`. Skill-authoring conventions live
in [CLAUDE.md](CLAUDE.md).
