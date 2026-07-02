# How Anthropic builds with Claude Code — the playbook

A distillation of Anthropic's published material on how their own teams use
Claude Code, current as of July 2026. This is the reference the toolkit in
this repo is built from; each section cites its sources (index at bottom).

## Headline facts

- ~80% of new code merged into Anthropic's production codebases is
  Claude-authored (up from low single digits at Claude Code's Feb 2025
  launch); Claude Code itself is 80–90% Claude-written [S12, S13, S22].
- Boris Cherny (Claude Code's creator) hasn't hand-edited code since Nov
  2025; he ships 20–30 PRs/day from ~5 parallel instances [S12, S17, S18].
- Every internal PR goes through the multi-agent Code Review product before
  a human approves; "a human still approves, but Claude does the review"
  [S16, S17].
- The core doctrine behind all of it: **"the context window is the most
  important resource to manage"** [S2] and **"give Claude a way to verify
  its work — it will 2–3x the quality of the final result"** [S10].

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
by mid-2026 Boris skips plan mode in favor of auto mode plus verification
gates, and "once there is a good plan, it will one-shot the implementation
almost every time" [S10, S18]; the docs still teach plan mode as the default.)

### 2. Verification-first / closed-loop TDD [S2, S10]

"Claude stops when the work *looks* done. Without a check it can run, 'looks
done' is the only signal." The escalation ladder:

- In the prompt: "run the tests after implementing".
- Session-wide: a `/goal` condition re-checked every turn by a fresh model.
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
outperforms a long session with accumulated corrections." Boris prefers
rewind-and-reprompt over correcting: "that keeps the failed attempt in your
context." Named failure modes: the kitchen-sink session,
correcting-over-and-over, the over-specified CLAUDE.md, the
trust-then-verify gap, infinite exploration.

## How they keep quality up

### Multi-agent review with aggressive false-positive filtering [S16, S19, S20]

Anthropic's shipped Code Review — "the exact same code review product that
we use internally at Anthropic for every single pull request" [S17] — is a
three-stage pipeline: parallel finder agents, each examining the diff from a
different dimension → independent verification of every finding → severity
ranking into one high-signal comment. Results of dogfooding: before it, 16%
of internal PRs got substantive review comments; now 54% do, and under 1% of
findings are marked incorrect [S16].

The published pipeline prompts [S19, S20] encode the discipline:

- "**CRITICAL: We only want HIGH SIGNAL issues**" — flag only code that
  fails to compile, produces definitely-wrong results, or violates an
  explicitly quotable CLAUDE.md rule.
- "If you are not certain an issue is real, do not flag it. False positives
  erode trust and waste reviewer time."
- Every finding gets a 0–100 confidence score from a separate agent;
  **findings under 80 are dropped**.
- Never flag: pre-existing issues on unmodified lines, anything a linter/
  typechecker/CI will catch, pedantic nitpicks "a senior engineer would not
  flag", style not required by CLAUDE.md.

Repo-specific tuning goes in a `REVIEW.md` (severity redefinitions, nit
caps, skip rules like "anything your CI already enforces", verification
bars like "behavior claims need a file:line citation") [S16]. Humans stay
in the loop by design: review output never approves or blocks a PR.

### Deterministic gates: hooks and /goal [S14, S15]

- **Stop hooks** run a check script when Claude tries to finish; exit code 2
  blocks the turn from ending and feeds the failure back. Guard with the
  `stop_hook_active` input field; Claude Code overrides after 8 consecutive
  blocks without progress (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it).
  Exit code 1 does NOT block — policy hooks must exit 2.
- **PostToolUse** hooks auto-format every edited file (style leaves the
  review surface entirely). **PreToolUse** hooks deny edits to protected
  files — and a hook `permissionDecision: "deny"` holds even in
  `bypassPermissions` mode.
- **/goal** sets a completion condition; after each turn a fresh small model
  judges the transcript and sends Claude back to work with a reason if the
  condition isn't met. Conditions must be demonstrable in the transcript
  ("npm test exits 0" — the agent must run it) and bounded ("or stop after
  20 turns"). Completion "is decided by a fresh model rather than the one
  doing the work."

### Anti-gaming and anti-slop [S2, S14, S21]

- TDD anti-gaming: be explicit you're doing TDD "so that it avoids creating
  mock implementations"; commit the failing tests before implementing so
  tampering shows in the diff; tell Claude not to modify tests; use
  "independent subagents to verify that the implementation isn't overfitting
  to the tests." A PreToolUse deny on test globs makes it physical.
- Anti-over-engineering: "Chasing every finding leads to over-engineering:
  extra abstraction layers, defensive code, and tests for cases that can't
  happen. Tell the reviewer to flag only gaps that affect correctness or the
  stated requirements" [S2].
- Simplification as a standing pass: the bundled `/simplify` runs a
  cleanup-only review (reuse, simplification, efficiency, altitude) and
  applies fixes; the code-simplifier agent's rule is "Never change what the
  code does - only how it does it", including "removing unnecessary comments
  that describe obvious code" [S21].
- Subjective linting: wrap `claude -p` in a build script as a project
  linter for what static tools can't see — typos, stale comments,
  misleading names [S2].

## How they choose tech

### Stay on distribution [S18]

Claude Code's own stack (TypeScript, React/Ink for the terminal UI, Bun) was
chosen "to be 'on distribution' — technologies Claude already knows well...
We wanted a tech stack which we didn't need to teach: one where Claude Code
could build itself." The corollary for everyone else: prefer mainstream,
heavily-documented technology; an exotic stack means every session pays a
teaching tax forever.

### Do the simple thing first — and delete code as models improve [S18]

"With every design decision, we almost always pick the simplest possible
option... We try to put as little code as possible around the model." Every
model release, they delete scaffolding ("with the 4.0 models, we deleted
around half the system prompt"). Boris's anti-orchestration stance: "Don't
box in the model with rigid workflows" [S17].

### Constrain through CLAUDE.md, decide through parallel investigation [S2, S5]

Tech choices are constraints recorded in CLAUDE.md ("architectural decisions
specific to your project"), and prompts default to "without libraries other
than the ones already used in the codebase." For genuinely open choices,
Boris fans out: "I'll ask it to investigate a few paths in parallel... use
three agents to do it... Claude will kind of pick the best option and then
summarize that" [S5]. Prototype velocity substitutes for deliberation —
20+ throwaway prototypes of one feature in two days [S18]; the Data Science
team's lesson runs the other way for tooling: build "persistent analytics
tools instead of throwaway notebooks" [S1].

### Architect FOR agents [S22, S2]

From the C-compiler experiment (16 parallel Claudes, ~2,000 sessions, ~$20k,
100k lines of Rust that compiles Linux): "the task verifier is nearly
perfect, otherwise Claude will solve the wrong problem." Agent-friendly
architecture means: near-perfect, fast verifiers; low-noise test output
("if there are errors, Claude should write ERROR" — thousands of useless
bytes cause time blindness); README/progress files because every agent
wakes with no context; decomposition that shards work across independent
files; a known-good oracle where possible. Plus: typed languages with a
code-intelligence (LSP) plugin give precise navigation and automatic error
detection after edits; CLI tools beat MCP servers for context efficiency [S2].

## How they let agents run unattended

### Task classification: the peripheral/core split [S1]

The Claude Code team's own tip: "distinguish between tasks that work well
asynchronously (peripheral features, prototyping) versus those needing
synchronous supervision (core business logic, critical fixes)." Auto-accept
loops for the edges — "review the 80% complete solution before taking over
for final refinements" — synchronous, prompt-by-prompt work for the core.
Security Engineering's variant: "commit your work as you go" with periodic
check-ins. RL Engineering: "supervised autonomy" with frequent checkpointing.

### The slot machine [S1]

The Data Science pattern for exploratory bets: "commit their state, let
Claude work autonomously for 30 minutes, and either accept the solution or
restart fresh if it doesn't work. Starting over often has a higher success
rate than trying to fix Claude's mistakes." Recovery from a failed
autonomous run is discard-and-relaunch, not debugging the run.

### The mechanism ladder [S14, S23, S24]

- **Auto mode**: an ML classifier reviews each action (deliberately blind to
  tool results so the agent can't talk it into approvals); built because
  users approved ~93% of permission prompts anyway — measured false-positive
  rate 0.4%, false-negative 17% on real internal tool calls. Falls back to
  prompting after repeated blocks; aborts in `-p` mode.
- **Permission rules** in checked-in `.claude/settings.json`: allow the
  verified build/test/git commands, deny push/deploy; "if a tool is denied
  at any level, no other level can allow it."
- **Sandboxing**: OS-level (`/sandbox`: Seatbelt/bubblewrap) limits writes
  to CWD and prompts per network domain; the published devcontainer ships a
  default-deny iptables firewall. `--dangerously-skip-permissions` is only
  defensible inside a network-isolated container — and even there
  credentials in the container are exfiltratable by a malicious repo.
- **Headless**: `claude -p` with `--allowedTools`, `--max-turns`, and
  `--permission-mode dontAsk` (the CI baseline: unapproved tools abort
  instead of hanging).
- **Recurring**: `/loop` (local, auto-expires after 7 days), `/schedule`
  (cloud routines), GitHub Actions on cron. Agent teams (experimental) add
  a hard authority boundary: "a teammate cannot approve a permission prompt
  or supply consent on your behalf."

### Coordination without an orchestrator [S22]

The C-compiler swarm coordinated through the filesystem: agents claim tasks
by writing lock files to a `current_tasks/` directory, work in Docker,
merge their own conflicts, and "when it finishes one task, it immediately
picks up the next" — the harness is dumb, the verifier is smart. That's the
published blueprint for scaling beyond a handful of parallel sessions.

### The walk-away contract [S10, S2]

What makes leaving safe: a gate that decides success (goal/Stop hook/CI),
evidence requirements ("pull requests that it came up with, verified end to
end, it has screenshots for me" [S17]), branch/worktree isolation so
recovery is cheap, and notification hooks so "dozens of Claudes" can signal
when they need input. Trust is calibrated, not assumed: auto mode was
red-teamed "with thousands of transcripts and prompt-injection attacks"
before Boris stopped reading permission prompts [S10].

## How teams apply it [S1]

- **Data Infrastructure**: debugged a Kubernetes outage from dashboard
  screenshots; new hires onboard by pointing Claude at the codebase +
  CLAUDE.md instead of a data catalog.
- **Claude Code team**: autonomous loops for peripheral/prototype work,
  close supervision for core logic (Vim bindings: ~70% of the final
  implementation from Claude's autonomous work).
- **Security**: stack-trace-driven incident response (10–15 min → ~5 min);
  moved from "design doc → janky code → give up on tests" to Claude-guided
  TDD; Claude Security now scans all Anthropic codebases weekly and fixes
  findings autonomously [S17].
- **Inference**: writes tests and fixes in unfamiliar languages (Rust).
- **Data Science**: one-shot React/TypeScript dashboards (5,000-line apps)
  without knowing TS.
- **Growth Marketing**: sub-agent pipeline generating hundreds of ad
  variations from a CSV; **Legal**: non-engineers shipped a phone-tree
  routing prototype.
- Cross-cutting: best results come from augmenting human workflows, treating
  Claude as a thought partner, and sharing discoveries across teams.

## Token-cost doctrine [S2, S4, S8]

- Benchmarks: ~$13/dev/active day average; under $30/day for 90% of users.
  Track with `/usage` and `/context`. (Internally, Anthropic deliberately
  leaves engineers unmetered — tokens are cheaper than engineer time [S17].)
- **Match model to task**: Haiku for search/mechanical subagent work, the
  session model for judgment. Counterpoint: Boris runs Opus at max effort
  for everything — "cheaper models use more tokens fixing mistakes" [S17] —
  but still delegates consumption to cheap subagents.
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
| S1 | How Anthropic teams use Claude Code — https://claude.com/blog/how-anthropic-teams-use-claude-code (full original: https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf) |
| S2 | Claude Code best practices — https://code.claude.com/docs/en/best-practices |
| S3 | Agent Skills engineering post — https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| S4 | Effective context engineering — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| S5 | Latent Space: Claude Code interview (Cherny, Wu) — https://www.latent.space/p/claude-code |
| S6 | Skills docs — https://code.claude.com/docs/en/skills |
| S7 | Subagents docs — https://code.claude.com/docs/en/sub-agents |
| S8 | Costs docs — https://code.claude.com/docs/en/costs |
| S9 | Skill authoring best practices — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| S10 | How Boris uses Claude Code — https://howborisusesclaudecode.com/ |
| S11 | GitHub Actions docs — https://code.claude.com/docs/en/github-actions |
| S12 | Fortune, Jan 29 2026 — https://fortune.com/2026/01/29/100-percent-of-code-at-anthropic-and-openai-is-now-ai-written-boris-cherny-roon/ |
| S13 | VentureBeat — https://venturebeat.com/technology/anthropic-says-80-of-its-new-production-code-is-now-authored-by-claude-how-your-enterprise-can-keep-up |
| S14 | Hooks guide — https://code.claude.com/docs/en/hooks-guide (reference: /en/hooks) |
| S15 | /goal docs — https://code.claude.com/docs/en/goal |
| S16 | Code Review announcement + docs — https://claude.com/blog/code-review ; https://code.claude.com/docs/en/code-review |
| S17 | Boris Cherny @Scale fireside + Lenny's Podcast (Feb 2026) — https://sozai.app/transcript/fireside-chat-boris-cherny-claude-code/ ; https://www.lennysnewsletter.com/p/head-of-claude-code-what-happens |
| S18 | Pragmatic Engineer: How Claude Code is built / Building Claude Code — https://newsletter.pragmaticengineer.com/p/how-claude-code-is-built ; .../building-claude-code-with-boris-cherny |
| S19 | code-review plugin (claude-code repo) — https://github.com/anthropics/claude-code/blob/main/plugins/code-review/commands/code-review.md |
| S20 | code-review plugin (official marketplace variant) — https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-review/commands/code-review.md |
| S21 | code-simplifier plugin — https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md |
| S22 | Building a C compiler with a team of parallel Claudes — https://www.anthropic.com/engineering/building-c-compiler |
| S23 | Auto mode engineering post — https://www.anthropic.com/engineering/claude-code-auto-mode ; containment: https://www.anthropic.com/engineering/how-we-contain-claude |
| S24 | Sandboxing / permissions / headless docs — https://code.claude.com/docs/en/sandboxing ; /en/permissions ; /en/headless ; agent teams: /en/agent-teams |
