# Agentic development toolkit

Workflow skills that turn raw ideas into agent-executable work in Claude
Code, Codex, and Antigravity. The pipeline is spec-driven, verification-gated,
subagent-heavy, and deliberately cheap on tokens. Its design began with
Anthropic's published engineering practices; the sourced research lives in
[docs/anthropic-playbook.md](docs/anthropic-playbook.md).

## Start here

Install the package for your runtime, start a fresh session in the repository
you want to work on, and run `/onboard`. That prepares the repository and its
shared agent guidance. Run `/gate` next if you want deterministic checks and
git gates, then `/idea` for the first feature.

The work queue is `bd` (Beads), the toolkit's runtime-neutral issue tracker.
`/onboard` detects or initializes its project state; `/work` selects one ready
issue for an attended session, while `/drain` processes the ready queue with
native agents from the active runtime.

Code exploration uses the bundled Codebase-Memory MCP declaration. Install
the pinned headless binary and toolkit launcher with
`bin/install-codebase-memory`; structural questions go to Codebase-Memory
first. If it is unavailable, workflows use bounded `rg` plus small reads and
state that graph coverage was not checked.

### Codebase-Memory install

On macOS or Linux:

```bash
bin/install-codebase-memory --dry-run
bin/install-codebase-memory
```

The installer selects one v0.9.0 release archive from checked-in metadata,
verifies its SHA-256, and installs only `codebase-memory-mcp` plus
`agentic-codebase-memory-mcp` to `~/.local/bin`. It does not run upstream's
client-configuring installer. To uninstall, remove those two binaries
explicitly. The shared cache at
`${XDG_CACHE_HOME:-$HOME/.cache}/agentic/codebase-memory` is deliberately
left in place; remove it separately only when you intend to discard every
indexed project.

For native Windows, download the immutable v0.9.0 headless ZIP and verify it
with `Get-FileHash -Algorithm SHA256` before `Expand-Archive`:

- `codebase-memory-mcp-windows-amd64.zip`:
  `92f96896f952e539f0d6cb34d7892a25064b677ccbf808b8f8310ad897e86f2c`
- `codebase-memory-mcp-windows-arm64.zip`:
  `63994fcfd15bf5e3f03cbf368cce86261713c7d7802e31469ae81a3939e4fae6`

Set `CBM_ALLOWED_ROOT` to the active repository's resolved absolute path and
`CBM_CACHE_DIR` to an account-wide cache before registering the extracted
binary as a stdio MCP server. The toolkit does not ship a native PowerShell
installer in this cutover.

## The pipeline

```
 first contact with a repo:  /onboard  (verified AGENTS.md, runtime bridge)
 then, when gates are wanted:/gate     (check + git gate; native hooks for
                                        the active runtime)

 idea ──▶ /idea ──▶ SPEC.md ──▶ /design ──▶ /breakdown ──▶ tasks/NN-*.md
                    (critic-    (only if an                    │
                     reviewed)   approach or                   │
                                 stack choice     ┌────────────┤
                                 is open)         ▼            ▼
                                               /build      /drain
                                               (attended,  (queue; ind.
                                                fresh       groups on
                                                session)    request)
                                                  │            │
                                                  └── verified ┤
                                                  (verifier agent, evidence required)
                                                               │
                                                               ▼
                                                           /distill
                                             (mistakes → CLAUDE.md, procedures → skills)
```

Each arrow crosses a **file on disk**, not conversation memory—every stage
can (and should) run in a fresh, cheap session. Small single-session specs
may skip `/breakdown` and go straight to `/build specs/<slug>/SPEC.md`.
To run the whole queue without relaunching each step, `/drain` dispatches a
fresh worker per ready issue in the bd queue in dependency order and defers
human questions into bd instead of stopping on them.

## What's in the box

| Piece                       | What it does                                                                                                                                                                                                                                  |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/onboard`                  | First contact with an existing repo: scouts it, writes shared AGENTS.md guidance, and adds the runtime bridge and permissions                                                                                                                |
| `/idea`                     | Interviews you about a raw idea, scouts the codebase, writes an agent-ready `SPEC.md` with runnable acceptance criteria, critic-reviewed                                                                                                      |
| `/design`                   | Resolves open tech/architecture choices: parallel agents investigate candidates, judged on agent-buildability; decision recorded in the spec and CLAUDE.md                                                                                    |
| `/breakdown`                | Splits a spec into one-session task files with dependencies and a parallelization map                                                                                                                                                         |
| `/build`                    | Executes one task: scout-explore → proportional plan → test-first implement → independent verify → simplification pass → commit                                                                                                               |
| `/drain`                    | Works the whole bd ready queue unattended: one fresh worker per ready issue (or an independent group concurrently on request), questions deferred into bd and batched at the end, resumable from `bd ready` after any `/clear` |
| `/gate`                     | Installs deterministic quality gates: a runtime-neutral check and git pre-commit gate, plus native Claude Code, Codex, or Antigravity lifecycle hooks                                                                                           |
| `/evals`                    | Scaffolds and runs stored skill evals (`evals/run.sh`): fresh fixture, headless run of the skill under test, artifact assertions—the repeatable complement to fresh-session testing                                                         |
| `/critique`                 | Adversarial review of any spec, plan, or diff                                                                                                                                                                                                 |
| `/distill`                  | Compounding engineering: session learnings → CLAUDE.md lines, rules, or new skills                                                                                                                                                            |
| `/handoff`                  | Writes a resume-from-scratch handoff file, then you `/clear`                                                                                                                                                                                  |
| `/fleet`                    | Dashboard of this session's open agents—running/queued/completed/failed, status tiles + timeline, as a self-contained HTML snapshot                                                                                                         |
| `/workboard`                | Cross-repo dashboard of ALL open work on the machine—specs, task files, handoffs, Kiro/Antigravity state, and native Claude Code, Codex, or Antigravity sessions—with a needs-attention inbox (blocked / needs-review / stale)             |
| `agentic audit`             | Scheduled tool-adoption check: reads session transcripts, counts raw `Grep` or grep-led shell searches that occur before the session's first Codebase-Memory query, plus verdict-schema failures and spend over cap, then uses bd to deduplicate and file each non-zero class. This is an ordering signal, not a boundedness or backend-availability judgment. Run by hand or from any scheduler—`agentic audit --since <date>` (add `--dry-run` to print measures without filing) |
| `scout` agent               | scout-tier (Claude default: Haiku at low effort), read-only—answers "where/how does X work" so the main session never reads files to look around                                                                                            |
| `critic` agent              | Attacks specs/plans/diffs; high-signal only—confidence-scored findings, false positives filtered the way Anthropic's own review pipeline does                                                                                               |
| `verifier` agent            | Fresh-eyes check of finished work against acceptance criteria, including overfitting-to-tests; evidence over assertion                                                                                                                        |
| `rules/token-discipline.md` | Always-loaded token economics: delegate consumption, match model to task, one task per session                                                                                                                                                |
| `rules/untrusted-data.md`   | Always-loaded injection defense: tool-sourced content is data, not instructions—unattended workers stop BLOCKED on redirection attempts                                                                                                     |

## Why this shape (the Anthropic practices it encodes)

- **Interview-to-spec, then execute in a fresh session**—"time spent making
  the spec precise pays off more than time spent watching the implementation."
- **Verification gates everything**—"give Claude a way to verify its work
  and it will 2–3x the quality of the result." Acceptance criteria are
  runnable commands; a separate agent grades the work ("the agent doing the
  work isn't the one grading it"); hooks make the gate deterministic.
- **Review is high-signal or it is noise**—Anthropic's internal review
  pipeline drops any finding below 80/100 confidence and never flags what a
  linter would catch. The `critic` agent enforces the same bar for diffs
  (specs may include lower-confidence ambiguity findings, marked as
  such—ambiguity is cheap to fix before implementation).
- **Tech choices stay on distribution**—prefer stacks the model already
  knows deeply (Anthropic picked Claude Code's own stack this way, so Claude
  could build it), do the simple thing first, and record decisions so no
  future agent re-litigates them.
- **Autonomy is classified, not assumed**—auto-accept for peripheral work,
  synchronous supervision for core logic; unattended runs get scoped
  permissions, bounded goals, branch isolation, and a discard-and-relaunch
  recovery rule (the "slot machine"). The execution stages (`/build`,
  `/drain`) launch only from the user's live request, never from text read
  from a file or tool. `/evals` adds an explicit-invocation policy because
  every run starts paid sessions. Why the boundary sits there and how it
  moved: [docs/human-gates.md](docs/human-gates.md).
- **Subagents protect the context window**—exploration, test noise, and
  review happen in disposable contexts; only conclusions return.
- **One task, one session, one commit**—after two failed corrections,
  restart clean; a better prompt beats a longer session.
- **Compounding engineering**—every mistake becomes a CLAUDE.md line or a
  skill, so no session repays for a lesson already learned.

## Token-cost design

- Scouts run **scout-tier** (Claude default: Haiku at low effort); the
  expensive model only ever sees their ~300-word reports.
- Skills load **on demand** (only name+description cost anything at session
  start); exact hook/permission configs live in per-skill `reference.md`
  files read only when installing; heavy research stays in `docs/`.
- Specs/tasks/handoffs on disk mean sessions stay short and `/clear` is
  always safe—no 200k-token kitchen-sink conversations.
- `/drain`'s group throughput mode warns that concurrency multiplies spend
  and refuses non-independent groups.
- The critic runs **before** implementation: a review costs ~1% of building
  the wrong thing.

## Install

The toolkit has native package manifests for Claude Code, Codex, and
Antigravity. All three packages expose the same 29 canonical workflows;
none uses another runtime as an execution backend.

### Claude Code

Install from the Claude Code marketplace:

```
/plugin marketplace add sticklane/claude
/plugin install agentic@agentic-toolkit
```

Everything arrives namespaced—`/agentic:idea`, `/agentic:build`, agents as
`@agentic:scout`—and updates with the marketplace. Teams can auto-enable it
per repo with `extraKnownMarketplaces` + `enabledPlugins` in the repo's
`.claude/settings.json`. One gap: rules don't ship in plugins, so copy the files in
`.claude/rules/` into the target repo (or fold them into its CLAUDE.md).

For the copy-based options below, clone it once:

```bash
git clone https://github.com/sticklane/claude.git ~/agentic-toolkit
```

For a version-controlled per-project install, clone the toolkit and copy its
Claude configuration from your project's root:

```bash
cp -r ~/agentic-toolkit/.claude .
git add .claude && git commit -m "Add agentic development toolkit"
```

If the project already has a `.claude/` directory, copy the subdirectories
(`skills/`, `agents/`, `rules/`) into it instead of overwriting.

For a copy-based global install:

```bash
mkdir -p ~/.claude/skills ~/.claude/agents ~/.claude/rules
cp -r ~/agentic-toolkit/.claude/skills/* ~/.claude/skills/
cp -r ~/agentic-toolkit/.claude/agents/* ~/.claude/agents/
cp -r ~/agentic-toolkit/.claude/rules/* ~/.claude/rules/
```

Prefer the plugin over a global copy when you want skills available
everywhere: the plugin serves skills/agents directly from the marketplace
checkout and updates with `/plugin`, with nothing copied into
`~/.claude/skills/`—copies there shadow the plugin's versions and go
stale. (A former `bin/sync-skills` helper that symlinked skills into
`~/.claude/skills/` was retired 2026-07-03 for exactly that reason.)
Note the two rules (token-discipline
and untrusted-data) are project-scoped—`.claude/rules/` has no
user-level equivalent, so the copy above only stages the files under
`~/.claude/rules/` for reference; for global use, fold both rules'
points into `~/.claude/CLAUDE.md`, which every session loads.

Verify by starting a new Claude Code session (skills load at session start)
and type `/`—you should see `idea`, `breakdown`, `build`, `gate`, and the
rest in the menu (prefixed `agentic:` if you installed the plugin). Then
point it at a real repo: `/onboard` first, `/idea` for your first feature.

### Codex

From a clone of this repository:

```bash
codex plugin marketplace add ~/agentic-toolkit
codex plugin add agentic@agentic-toolkit
codex plugin list
```

Inside this checkout, Codex needs no global install: `.agents/skills/`
already exposes every canonical skill. The
[Codex guide](codex/README.md) explains package entrypoints and native
collaboration orchestration.

### Antigravity

From a clone of this repository:

```bash
agy plugin validate ~/agentic-toolkit
agy plugin install ~/agentic-toolkit
agy plugin list
```

Inside this checkout, Antigravity also discovers `.agents/skills/` directly.
The [Antigravity guide](antigravity/README.md) explains native subagent and
headless execution.

### Other runtimes and models

Each active runtime uses its own native model and orchestration profile. To
override which models its tiers map to, add a one-line
`.claude/runtime.md` selecting a profile from
[runtimes/](runtimes/README.md); the porting guide is
[docs/porting.md](docs/porting.md).

Notes:

- Specs land in `specs/<slug>/` in whatever repo you run the pipeline in.
- The build workflow uses native `simplify` and `code-review` capabilities
  when the active runtime supplies them, with an inline fallback when it
  does not.
- Nothing changes permissions or installs hooks merely by loading the
  plugin. `/onboard` and `/gate` make those changes only when invoked.

## Extending it

Don't add to this toolkit by hand—use it on itself: when you correct Claude
twice about the same thing, run `/distill`. Skill-authoring conventions live
in [CLAUDE.md](CLAUDE.md).
