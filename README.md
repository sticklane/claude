# Agentic development toolkit

Skills and subagents that turn raw ideas into agent-executable work, modeled
on how Anthropic's own teams use Claude Code — spec-driven, verification-
gated, subagent-heavy, and deliberately cheap on tokens. The research this is
built from, with citations, lives in [docs/anthropic-playbook.md](docs/anthropic-playbook.md).

## The pipeline

```
 first contact with a repo:  /onboard  (verified CLAUDE.md, permissions)
 once per repo:              /gate     (Stop-hook check gate, auto-format,
                                        protected files)

 idea ──▶ /idea ──▶ SPEC.md ──▶ /design ──▶ /breakdown ──▶ tasks/NN-*.md
                    (critic-    (only if an                    │
                     reviewed)   approach or                   │
                                 stack choice     ┌────────────┼────────────────┐
                                 is open)         ▼            ▼                ▼
                                               /build      /parallel      /autopilot
                                               (attended,  (independent   (unattended,
                                                fresh       tasks, work-   gated, walk
                                                session)    tree agents)   away)
                                                  │            │                │
                                                  └── verified ┴────────────────┘
                                                  (verifier agent, evidence required)
                                                               │
                                                               ▼
                                                           /distill
                                             (mistakes → CLAUDE.md, procedures → skills)
```

Each arrow crosses a **file on disk**, not conversation memory — every stage
can (and should) run in a fresh, cheap session. Small single-session specs
may skip `/breakdown` and go straight to `/build specs/<slug>/SPEC.md`.
To run the whole queue without relaunching each step, `/drain` dispatches a
fresh worker per unblocked task in dependency order and defers human
questions into the task files instead of stopping on them.

## What's in the box

| Piece | What it does |
|---|---|
| `/onboard` | First contact with an existing repo: scouts it, writes a CLAUDE.md whose every command was actually run, adds a permission allowlist |
| `/idea` | Interviews you about a raw idea, scouts the codebase, writes an agent-ready `SPEC.md` with runnable acceptance criteria, critic-reviewed |
| `/design` | Resolves open tech/architecture choices: parallel agents investigate candidates, judged on agent-buildability; decision recorded in the spec and CLAUDE.md |
| `/breakdown` | Splits a spec into one-session task files with dependencies and a parallelization map |
| `/build` | Executes one task: scout-explore → proportional plan → test-first implement → independent verify → simplification pass → commit |
| `/parallel` | Dispatches an independent task group to concurrent worktree-isolated agents |
| `/autopilot` | Unattended execution with guardrails: classifies the task (peripheral vs core), scopes permissions, sets a bounded goal, launches background or headless |
| `/drain` | Works the whole task queue unattended: one fresh worker per unblocked task, questions deferred into the task files and batched at the end, resumable from `Status` lines after any `/clear` |
| `/gate` | Installs deterministic quality gates: a Stop hook that blocks "done" until checks pass, auto-format on edit, protected-file denies |
| `/critique` | Adversarial review of any spec, plan, or diff |
| `/distill` | Compounding engineering: session learnings → CLAUDE.md lines, rules, or new skills |
| `/handoff` | Writes a resume-from-scratch handoff file, then you `/clear` |
| `/fleet` | Dashboard of this session's open agents — running/queued/completed/failed, status tiles + timeline, as a self-contained HTML snapshot |
| `scout` agent | Haiku, read-only, low effort — answers "where/how does X work" so the main session never reads files to look around |
| `critic` agent | Attacks specs/plans/diffs; high-signal only — confidence-scored findings, false positives filtered the way Anthropic's own review pipeline does |
| `verifier` agent | Fresh-eyes check of finished work against acceptance criteria, including overfitting-to-tests; evidence over assertion |
| `rules/token-discipline.md` | Always-loaded token economics: delegate consumption, match model to task, one task per session |

## Why this shape (the Anthropic practices it encodes)

- **Interview-to-spec, then execute in a fresh session** — "time spent making
  the spec precise pays off more than time spent watching the implementation."
- **Verification gates everything** — "give Claude a way to verify its work
  and it will 2–3x the quality of the result." Acceptance criteria are
  runnable commands; a separate agent grades the work ("the agent doing the
  work isn't the one grading it"); hooks make the gate deterministic.
- **Review is high-signal or it is noise** — Anthropic's internal review
  pipeline drops any finding below 80/100 confidence and never flags what a
  linter would catch. The `critic` agent enforces the same bar for diffs
  (specs may include lower-confidence ambiguity findings, marked as such —
  ambiguity is cheap to fix before implementation).
- **Tech choices stay on distribution** — prefer stacks the model already
  knows deeply (Anthropic picked Claude Code's own stack this way, so Claude
  could build it), do the simple thing first, and record decisions so no
  future agent re-litigates them.
- **Autonomy is classified, not assumed** — auto-accept for peripheral work,
  synchronous supervision for core logic; unattended runs get scoped
  permissions, bounded goals, branch isolation, and a discard-and-relaunch
  recovery rule (the "slot machine").
- **Subagents protect the context window** — exploration, test noise, and
  review happen in disposable contexts; only conclusions return.
- **One task, one session, one commit** — after two failed corrections,
  restart clean; a better prompt beats a longer session.
- **Compounding engineering** — every mistake becomes a CLAUDE.md line or a
  skill, so no session repays for a lesson already learned.

## Token-cost design

- Scouts run **Haiku at low effort**; the expensive model only ever sees
  their ~300-word reports.
- Skills load **on demand** (only name+description cost anything at session
  start); exact hook/permission configs live in per-skill `reference.md`
  files read only when installing; heavy research stays in `docs/`.
- Specs/tasks/handoffs on disk mean sessions stay short and `/clear` is
  always safe — no 200k-token kitchen-sink conversations.
- `/parallel` warns that concurrency multiplies spend and refuses
  non-independent groups.
- The critic runs **before** implementation: a review costs ~1% of building
  the wrong thing.

## Install

**Option A — plugin** (recommended: one command, works in every repo, local
and web/desktop sessions alike). In any Claude Code session:

```
/plugin marketplace add sticklane/claude
/plugin install agentic@agentic-toolkit
```

Everything arrives namespaced — `/agentic:idea`, `/agentic:build`, agents as
`@agentic:scout` — and updates with the marketplace. Teams can auto-enable it
per repo with `extraKnownMarketplaces` + `enabledPlugins` in the repo's
`.claude/settings.json`. One gap: rules don't ship in plugins, so copy
`.claude/rules/token-discipline.md` into the target repo (or fold it into
its CLAUDE.md).

For the copy-based options below, clone it once:

```bash
git clone https://github.com/sticklane/claude.git ~/agentic-toolkit
```

**Option B — per project** (version-controlled, shared with
your team). From your project's root:

```bash
cp -r ~/agentic-toolkit/.claude .
git add .claude && git commit -m "Add agentic development toolkit"
```

If the project already has a `.claude/` directory, copy the subdirectories
(`skills/`, `agents/`, `rules/`) into it instead of overwriting.

**Option C — global** (available in every repo, just for you):

```bash
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r ~/agentic-toolkit/.claude/skills/* ~/.claude/skills/
cp -r ~/agentic-toolkit/.claude/agents/* ~/.claude/agents/
```

Symlink instead of `cp` if you want `git pull` in `~/agentic-toolkit` to
update everything in place. Note the token-discipline rule is
project-scoped (`.claude/rules/` has no user-level equivalent) — for global
use, fold its points into `~/.claude/CLAUDE.md`.

**Verify**: start a new Claude Code session (skills load at session start)
and type `/` — you should see `idea`, `breakdown`, `build`, `gate`, and the
rest in the menu (prefixed `agentic:` if you installed the plugin). Then
point it at a real repo: `/onboard` first, `/idea` for your first feature.

**Option D — Google Antigravity** instead of the Claude Code CLI: the full
port lives in [antigravity/](antigravity/README.md) — same skills (native
Agent Skills support), the human-only commands as workflows, `AGENTS.md`
replacing CLAUDE.md, and hooks in Antigravity's format. From your project
root:

```bash
cp -r ~/agentic-toolkit/antigravity/.agents .
cp ~/agentic-toolkit/antigravity/AGENTS.md .    # merge if you have one
```

See [antigravity/README.md](antigravity/README.md) for the concept mapping
and what degrades (notably: no enforced cheap subagents, softer stop gates).

Notes:

- Specs land in `specs/<slug>/` in whatever repo you run the pipeline in.
- This toolkit layers on top of Claude Code's bundled commands — it assumes
  `/simplify` and `/code-review` exist rather than duplicating them.
- Nothing here changes permissions or installs hooks by itself; only
  `/onboard` and `/gate` write to `.claude/settings.json`, and they ask
  first.

## Extending it

Don't add to this toolkit by hand — use it on itself: when you correct Claude
twice about the same thing, run `/distill`. Skill-authoring conventions live
in [CLAUDE.md](CLAUDE.md).
