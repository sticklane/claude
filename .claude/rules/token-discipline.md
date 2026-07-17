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
  When a task map genuinely supports concurrency, cap the fleet at a 3–5
  concurrent-writer window (three focused writers often beat five
  scattered ones; >5 is reserved for read-only breadth-first fan-outs) and
  let /drain's rolling top-up keep it full — refilling on each collected
  verdict, not at a wave barrier — rather than launching a fixed batch and
  idling finished workers behind the slowest. This tightens the sizing
  guidance; it does not change the opt-in default above. The cross-vendor
  evidence for both the window and the rolling claim-next design is in
  docs/external-playbooks.md (cited, not restated).
- **Drain-shaped freehand requests → route into `/drain`.** When the
  human's live message is drain-shaped ("drain the …", "work through the
  remaining tasks in specs/…"), invoke the `/drain` skill rather than
  improvising an unstructured dispatch loop — the skill's window/baton/
  verdict machinery is what keeps a dispatch loop cheap and safe, and
  improvised loops are how the measured ~$1,406/week of unstructured
  orchestration happened (specs/drain-wake-cost/EVIDENCE.md). The
  drain-shaped live message IS the launch authorization (the skill's
  launch contract; docs/human-gates.md); absent one, recommend `/drain`
  and never launch it on the human's behalf.
- **Large codebase, scout not converging → the orchestrating session (never
  `scout`) may `ToolSearch` for a connected code-search MCP tool.** When
  repeated `scout` dispatches on a fuzzy/semantic query aren't converging on
  a large repo and such a server _happens to be connected_ this session, the
  orchestrating session — `scout` cannot `ToolSearch` — runs a `ToolSearch`
  to discover it and prefers it over further scout rounds. Advisory and
  conditional on a server being connected, never a hard dependency; when
  each choice fits, and how to install `claude-context` or `code-index-mcp`,
  is in docs/guides/large-codebase-context.md.
- **Multi-page browser walks delegate per page; cap direct screenshots.** A
  `claude-in-chrome`-driven site walk that screenshots after each navigation
  blows context — a proven incident died with "Prompt is too long" mid-task,
  and the same-task RETRY succeeded only by delegating page-by-page scouting
  to subagents (the RETRY-succeeded-via-delegation evidence in
  specs/context-blowout-subagent-guards' Problem/Research-grounding sections).
  So for any multi-page or multi-step browser-automation walk,
  route each page-check through a subagent that returns a short verdict rather
  than accumulating raw screenshots in the orchestrating session's context;
  keep at most 2 direct-context screenshots per turn in the main session, and
  send anything beyond that cap through a subagent. Pure existence/state-check
  pages go to `scout` (this section's opening bullet), but `scout` has no MCP
  tool grant — its `.claude/agents/scout.md` frontmatter grants `Read`,
  `Grep`, `Glob`, `Bash(git log *)`, `Bash(git show *)`, `Bash(ls *)`, and
  `Bash(wc *)` — so it cannot drive `mcp__claude-in-chrome__*` tools; reserve
  `general-purpose` or a purpose-built agent for pages needing an interaction
  sequence.

## Model and effort matching

Four rungs, cheapest first — don't pay frontier-model rates to run `grep`:

- scout-tier → mechanical or lookup work (Claude default: Haiku at low
  effort; the `scout` default).
- session-tier → ordinary judgment work done directly in the session
  (specs, review, tricky implementation): the conversation's own model.
  Distinct from drain's _dispatched_ implementation workers, below — those
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

**Freehand fan-out (dispatch outside a skill).** Mechanical fan-out work
dispatched outside a skill uses the typed pinned agents
(scout/verifier/implementation-worker) or passes an explicit cheap-tier
`model` override to general-purpose; bare general-purpose at the session
model is reserved for judgment work. This applies the rungs above to
freehand dispatch — it does not change them. The default matters because
general-purpose inherits the session's frontier model, so at $0.067/call it
ran *costlier* than the opus-pinned implementation-worker at $0.057/call over
the 2026-07 agentprof week (specs/drain-wake-cost/EVIDENCE.md) — a mechanical
fan-out on the session's frontier model is the tier ladder inverted.

## Dispatch authoring

When a skill spawns agents, its prompt text must make these choices
explicit — model/effort tier, return budget, and any loop bound — instead
of letting them default silently:

- **An untyped agent must not spawn another untyped agent without an
  explicit model override** — nesting is where model inheritance compounds.
  The untyped set is the exact-match catch-all enumeration
  `agent:claude` / `agent:agentic:claude` / `agent:general-purpose` /
  `agent:agentic:general-purpose` (specs/untyped-agent-fanout/SPEC.md R4;
  any other `agent:*` frame — e.g. `agent:claude-code-guide`, which merely
  shares the `agent:claude` prefix — is typed and breaks the chain). Each
  inherits the caller's model, so stacked untyped frames compound
  frontier-tier cost at every level — the tier ladder inverted, at depth
  (specs/untyped-agent-fanout/SPEC.md; the 2026-07-11 $123 nested-chain
  leak). This extends "Freehand fan-out" above from a single frame to
  nested dispatch: give the child a typed pinned agent (scout / verifier /
  implementation-worker) or pass it an explicit cheap-tier `model`
  override. **Feasibility, decided 2026-07-12 — doctrine-only, no hook:** a
  PreToolUse warn-hook on Agent calls was scoped and NOT shipped because
  the hook input schema exposes no dispatch-depth field and no reliable
  running-agent tier marker (`agent_type` surfaces only inside a subagent
  and is undocumented for the main session), so a correct
  untyped-under-untyped warn cannot be built from it; this stays a doctrine
  line, warn-only in spirit, until the hook API exposes caller type or
  depth.
- **Awaited children, never detached (maintainer policy, 2026-07-09).**
  Fresh context comes from the subagent boundary — a worktree-isolated
  worker with a blank context — never from detachment. Every spawned
  agent has a parent that waits for it and collects its result before
  moving on (synchronous dispatch); no fire-and-forget sub-verifiers, no
  orphaned children outliving the step that spawned them, no detached
  orchestrator generations where an attended parent can supervise
  instead. A worker that spawns its own verifier awaits it inline the
  same way. Scoped exception, as of 2026-07-11 (a524797, "Maintainer
  decision 2026-07-11 (explicit, supersedes this morning's attended-only
  tightening): no pipeline step forces a human"): drain's
  generation-boundary self-relaunch — the detached headless generation a
  drain run spawns at its own baton pass to keep working the queue — is a
  sanctioned carve-out from the "no orphaned children outliving the step
  that spawned them" clause, not a violation of it. It is compliant
  because it is a _continuation_ of an already-human-launched drain run,
  not a new unauthorized launch (docs/human-gates.md: the human gates
  govern a run's launch, not its self-chaining continuation on
  already-granted scope), so no per-generation human checkpoint is
  required. This is a point-in-time carve-out scoped to drain's relaunch
  specifically — not a general reopening of detachment; a future
  maintainer who retightens the policy should strike this sentence rather
  than read it as the rule's permanent shape.
- **Background-dispatched agents can't interactively interview a human.**
  `AskUserQuestion` isn't available to an `Agent`-tool-spawned background
  worker (confirmed 2026-07-11: an `/idea`-invoking dispatch fell back to
  asking in plain prose and stalled until the orchestrator relayed an
  answer via `SendMessage`). Brief a dispatched worker fully enough
  upfront that it doesn't need to ask — resolve genuinely open questions
  yourself before dispatch, or accept the extra round-trip if one surfaces
  anyway. Don't design a dispatch prompt around "the worker will just ask."

- **Await, don't poll.** Await background children via the harness's
  completion notifications (or a `Monitor` until-loop where the harness
  offers one); never poll them with chained short sleeps — after the
  harness blocks a `sleep`, chaining shorter sleeps is the same
  blocked-sleep antipattern in chunks, and is banned. `run_in_background:
false` on the Agent tool is advisory, not guaranteed — the harness may
  still launch a long-running dispatch in the background regardless
  (observed 2026-07-12 on multi-turn `implementation-worker` calls).
  Treat every dispatch as potentially backgrounded: don't treat a
  background launch as an error when you asked for synchronous, just wait
  for the completion notification.

- **Tier by stage type.** Mechanical stages (search, fetch, extract,
  grep-like scouting, conformance checks) run on Haiku / `effort: low`;
  judgment stages (implementation, verification, judging, synthesis) keep
  the session model, raising effort only for the hardest verify/judge
  stages (docs/anthropic-playbook.md, "Token-cost doctrine"). Review work
  splits by altitude: reviewing individual code blocks (style,
  conformance, mechanical correctness) is scout-tier; reviewing
  APIs, architecture, structure, and abstraction is judgment work on a
  high-quality model — the critic's deep-tier pin
  (docs/external-playbooks.md, "The new-SDLC spectrum").
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
- **Remind deferred-tool workers to load the schema first.** When a
  dispatched worker is likely to call a deferred tool — `Monitor` is the
  evidenced case, and the same holds for the general class of deferred tools
  the harness lists but does not pre-load — the dispatch prompt must tell it
  to batch-load the tool's schema via `ToolSearch` before the first call,
  batched in one call rather than probed one tool at a time. Don't lean on
  the harness's own per-session system-reminder alone: it already lists the
  deferred tools, yet a guessed-parameter `Monitor` call still threw
  `InputValidationError` and burned a round trip (the guessed-parameter
  evidence in specs/context-blowout-subagent-guards' Problem section), so the
  explicit in-prompt reminder is the extra layer this repo's guidance can
  supply on top of it.

## Session hygiene

- One task per session — light artifact stages may self-chain per
  CLAUDE.md's conventions. When a task completes, `/clear` and start the
  next from its task file rather than carrying dead context forward.
- Long-running work should be resumable from artifacts on disk (specs, task
  files, notes in `docs/`), never from conversation memory. If a session is
  getting heavy mid-task, write a handoff file and restart from it.
- Don't re-run searches or re-read files already established this session;
  don't paste large command output back into the conversation — summarize it.

## Session refresh

A long-lived autonomous session that idles past the prompt-cache TTL between
wakes rewrites its whole accumulated context at cache-write rates before
doing any work — cache re-priming was 26% of one overnight window's cost
(specs/session-refresh-automation, which pins the 30-day numbers below).
Three points govern the shape:

- **A waiting main loop is a scheduler, not a thinker.** A main loop that
  expects to idle past the cache TTL — a watch-then-act poller, a self-paced
  wakeup loop — runs cheap-tier (or launchd), dispatching each event's
  judgment work to an awaited fresh subagent; never a frontier-tier main loop
  that re-warms a fat context just to poll.
- **Every autonomous session carries a wake budget** — refresh-over-carry.
  When observed re-primes or estimated context-rewrite cost crosses the
  budget, the session refreshes (writes a `/handoff` artifact and ends, or
  batons where a sanctioned baton exists) instead of sleeping again.
- **Budget defaults: 3 re-primes or a 250k-token context, tunable.** Pinned
  from the 30-day profile (specs/session-refresh-automation): 3 is the
  re-prime median deliberately — the median is the behavior being changed —
  and 250k sits between the context p50 and p90 so the flag marks the heavy
  tail, not normal sessions.

The drain-specific verdict-count baton stays owned by specs/drain-wake-cost
(cited, not restated); this doctrine covers the freehand and watch-then-act
sessions drain's border doesn't reach.

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
