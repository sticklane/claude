# Token discipline

Context is the scarce resource. Every token in the main conversation is
re-sent on every subsequent turn, so pollution compounds. Spend main-context
tokens on decisions; delegate consumption of raw material to subagents.

## Delegation defaults

- **Never read files into main context to "look around."** Use the `scout`
  agent (scout-tier, read-only; Claude default: Haiku) for any
  where/how/what-exists question. Fan out
  multiple scouts in parallel for independent questions; you keep the
  conclusions, not the file dumps.
- Read a file directly only when you are about to edit it, and prefer reading
  the relevant slice over the whole file.
- Verification, review, and research that produce lots of intermediate output
  belong in subagents (`verifier`, `critic`, `Explore`) whose transcripts are
  discarded — only their final report costs you anything.
- One worker is the default; scale the fleet only for genuinely divisible
  groups (the decision-coupling test in /breakdown), and size it by the
  task map, never a default maximum. Multi-agent work costs ~15× the
  tokens of a single session — barely-parallel work doesn't earn that.

## Model and effort matching

Four rungs, cheapest first — don't pay frontier-model rates to run `grep`:

- scout-tier → mechanical or lookup work (Claude default: Haiku at low
  effort; the `scout` default).
- session-tier → ordinary judgment work done directly in the session
  (specs, review, tricky implementation): the conversation's own model.
  Distinct from drain's *dispatched* implementation workers, below — those
  carry their own adopted Role pin regardless of what the session runs.
- deep-tier (Claude default: Opus 4.8) → heavy judgment above the session
  default: final review of a large diff, subtle-bug hunts, architecture
  critique. Also the adopted default for drain's implementation-worker
  dispatch (the `implementation-worker` agent pins this in its own
  frontmatter, independent of the calling session's model — runtimes/
  claude-code.md's Role pins table).
- frontier-tier (Claude default: Fable) → ONLY work that truly needs the
  strongest model: novel architecture decisions, security-critical review,
  or a retry after a deep-tier attempt failed.

Skills that spawn agents — at their actual spawn points: drain's attempt-1
implementation-worker dispatch, its relaunch and tournament workers, its
per-candidate verifier runs, /design's candidate investigators, an
on-demand verifier escalation — consult `.claude/runtime.md` tier pins (or,
where one exists, an agent definition's own frontmatter pin) and pass the
mapped model through the harness's model parameter. No config, or no pin
for the tier in question — and no agent-frontmatter pin either — → inherit
the session model (the deep
tiers are opt-in: profile rows are recommended pin values, not active
defaults). Pins bind Agent-tool dispatch and the headless fallback
templates alike — headless workers pass the same tier alias through the
template's `--model` flag.

## Dispatch authoring

When a skill spawns agents, its prompt text must make these choices
explicit — model/effort tier, return budget, and any loop bound — instead
of letting them default silently:

- **Tier by stage type.** Mechanical stages (search, fetch, extract,
  grep-like scouting, conformance checks) run on Haiku / `effort: low`;
  judgment stages (implementation, verification, judging, synthesis) keep
  the session model, raising effort only for the hardest verify/judge
  stages (docs/anthropic-playbook.md, "Token-cost doctrine").
- **Cap subagent returns at 1–2k tokens** — a structured verdict or
  distilled summary, never the transcript
  (docs/context-management-research-2026-07.md:66).
- **Bound evaluator-optimizer loops to 2–4 cycles**, and skip the
  generate/critique loop entirely when a deterministic check can decide
  the outcome (docs/orchestration-research-2026-07.md:58).
- **Default to a single-call rubric judge** — one prompt emitting scores
  and a pass/fail grade — over multi-judge voting
  (docs/orchestration-research-2026-07.md:58).
- **Place logic on the deterministic-vs-model-driven axis:** a script owns
  loops, fan-out, and gates; the model owns decomposition and routing
  (docs/orchestration-research-2026-07.md:16).
- **Scale effort in the dispatch prompt:** 1 agent / 3–10 calls for
  lookups; 2–4 agents / 10–15 calls for comparisons; 10+ agents only
  breadth-first (docs/orchestration-research-2026-07.md:50-52).
- **Externalize large artifacts, return a path.** When a worker's useful
  output is a large artifact (a full diff, a search-result dump, a log)
  rather than a verdict, have it write the artifact to disk and return the
  path — never paste it into the return message
  (docs/subagent-intermediate-output-research-2026-07.md, "externalize
  large artifacts").
- **Prefer a fresh dispatch over one growing thread.** On the model tiers
  this toolkit dispatches (Opus 4.5+/Sonnet 4.6+), extended-thinking blocks
  are kept by default and re-billed as input tokens on every subsequent
  turn — a concrete reason, beyond context rot, to hand a long task to a
  fresh subagent rather than let one thread's reasoning grow across many
  turns (docs/subagent-intermediate-output-research-2026-07.md,
  "thinking-token replay cost").

## Session hygiene

- One task per session — light artifact stages may self-chain per
  CLAUDE.md's conventions. When a task completes, `/clear` and start the
  next from its task file rather than carrying dead context forward.
- Long-running work should be resumable from artifacts on disk (specs, task
  files, notes in `docs/`), never from conversation memory. If a session is
  getting heavy mid-task, write a handoff file and restart from it.
- Don't re-run searches or re-read files already established this session;
  don't paste large command output back into the conversation — summarize it.

## Cache economics

- Prompts are cached static-first: stable content (rules, skill text,
  unchanged files) belongs at the front of prompts and must not churn
  mid-session.
- Editing CLAUDE.md or `.claude/rules/` mid-session invalidates the
  cached prefix for every later turn — batch such writes at session end
  (as /distill does).
- Tool-set changes bust caches: don't add/remove MCP servers or edit an
  agent's `tools:` list mid-run. Harness-managed deferred tool loading
  is exempt — it's designed for this.

## Cheap before expensive

- Critique the spec before implementing it (a `critic` pass costs ~1% of a
  wrong implementation).
- Make acceptance checks runnable commands, so verification is one cheap
  subagent instead of an interactive debugging spiral.

## Match the research tool to the question

- `deep-research` (fan-out → adversarial 3-vote verify → synthesize) earns
  its ~100-agent cost only for open-ended, multi-source questions where the
  claims are contestable. For closing a _known-source factual gap_ (the
  answer lives in specific official docs), dispatch a few targeted
  general-purpose agents told which URLs to hit and required to back every
  claim with a verbatim quote + URL or mark it UNVERIFIED — verification
  baked into one cheap agent. The adversarial verifier over-refutes plain
  documentation facts, so it can return nothing while the answer sat in the
  first doc.
- Keep `deep-research` args short. Long multi-line, quote-laden args have
  broken its Scope agent's structured output (retry-cap failure before any
  search runs).
