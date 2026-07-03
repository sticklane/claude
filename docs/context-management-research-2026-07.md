# Context Management for Long-Running Agents: Vendor Guidance Survey (2026-07)

> Deep-research run 2026-07-03 (79/103 agents completed; 24 verification agents
> failed on usage credits, so OpenAI/Google/Meta/xAI legs are UNVERIFIED — all
> findings below are Anthropic primary sources, 3-vote verified). Commissioned
> for `specs/orchestrator-context/SPEC.md` (drain & co. self-managing context).
> The OpenAI/Google leg was closed by a same-day follow-up run — see
> "Follow-up findings (2026-07-03)" below.

## Summary

Anthropic's mid-2026 published guidance (engineering blog, platform docs, cookbook) converges on a clear doctrine: context degradation ("context rot") begins well before the hard token limit, so long-running agents should manage context proactively with a three-layer toolkit — server-side compaction for whole-window growth, tool-result clearing for stale re-fetchable data, and file-based external memory for anything that must survive a session boundary — adopting whichever layer matches the observed bottleneck. Critically, Anthropic states that compaction alone is insufficient for multi-context-window work: the prescribed pattern is a fresh-session relaunch that resumes from durable artifacts (a progress log, a feature/scope checklist, an init-script pointer, and git history), set up deliberately by an initializer session, with each fresh instance reading those files and then running a verification check rather than trusting them blindly. The memory tool's auto-injected protocol codifies the design assumption for orchestrators: assume interruption at any moment, so any state not written to external files is lost. For a file-based toolkit like /drain that already commits queue state to task files, the adoption path is: relaunch on proactive token thresholds (not on failure), keep a done/next progress log updated at every task boundary, and make the fresh instance's first acts be read-state-then-verify. Note: all claims that survived verification are Anthropic sources; OpenAI/Google/Meta/xAI guidance was not confirmed (verification infrastructure errors), so cross-vendor comparison remains open.

## Verified findings

### Context rot is the documented degradation signal

**Confidence: high** — Context rot is the documented degradation signal: model recall accuracy measurably decreases as context-window token count grows, meaning agents degrade before hitting the hard context limit — this is the stated basis for proactive (threshold-based, not failure-based) context management.

Evidence: Both the engineering post and the 2026-03 cookbook state verbatim: 'as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases.' The cookbook adds: 'even before the hard context limit is reached, the agent may be getting less out of each token.' Anthropic cites Chroma's 18-model empirical study; degradation is framed as 'a performance gradient rather than a hard cliff.' (Merged claims 0 and 7, both confirmed 3-0.)

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools

### Anthropic prescribes a three-layer decision framework matched to the observed bottleneck

**Confidence: high** — Anthropic prescribes a three-layer decision framework matched to the observed bottleneck: compaction (summarize and reinitiate) is the first lever when the whole window grows too large; tool-result clearing is the safest, lightest-touch form of compaction for stale re-fetchable data (default trigger 100,000 input tokens, keeping the 3 most recent tool-use/result pairs, oldest cleared first); file-based memory moves information out of the window so it survives across sessions. Start with only the layer matching the actual bottleneck, since each adds tuning cost.

Evidence: Engineering post: 'Compaction typically serves as the first lever... One of the safest lightest touch forms of compaction is tool result clearing.' Cookbook (verbatim): 'compaction compresses the whole window when it grows too large, clearing drops stale re-fetchable data inside the window, and memory moves information out of the window so it survives across sessions... start with the one that matches the bottleneck you're actually observing.' Context-editing docs confirm defaults: trigger 100k input tokens, keep 3 tool pairs, oldest first. Nuance: the source permits layering all three; 'only' means 'start with'. (Merged claims 1, 8, 15, each 3-0.)

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools
- https://platform.claude.com/docs/en/build-with-claude/context-editing

### Cache economics rule for clearing

**Confidence: high** — Cache economics rule for clearing: clearing tool results invalidates cached prompt prefixes, so Anthropic provides the clear_at_least parameter to ensure enough tokens are cleared per clear event to make breaking the prompt cache economically worthwhile; cache-write costs are incurred on each clear, with subsequent requests reusing the newly cached prefix. Frequent small clears are the anti-pattern; batch clearing amortizes the cost.

Evidence: Docs verbatim: 'Invalidates cached prompt prefixes when content is cleared... clear enough tokens to make the cache invalidation worthwhile. Use the clear_at_least parameter... You'll incur cache write costs each time content is cleared, but subsequent requests can reuse the newly cached prefix.' The strategy is not applied at all if the minimum cannot be cleared. Cookbook example uses clear_at_least of 10,000 input tokens. (Merged claims 10 and 16, each 3-0.) This is the only confirmed cache-economics guidance; broader clear-vs-compact TTL economics were not verified.

- https://platform.claude.com/docs/en/build-with-claude/context-editing
- https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools

### Anthropic's canonical external-memory mechanism is the file-based memory tool (released wi

**Confidence: high** — Anthropic's canonical external-memory mechanism is the file-based memory tool (released with Sonnet 4.5, now GA): a client-executed tool where Claude issues create/read/update/delete operations against a /memories directory that the application maps onto its own storage. When enabled, the API auto-injects a protocol — 'ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE', record status/progress/thoughts as you work, and 'ASSUME INTERRUPTION: Your context window might be reset at any moment, so you risk losing any progress that is not recorded' — with the model itself deciding what state to persist. This codifies the design assumption that unwritten progress is lost.

Evidence: Docs verbatim confirm client-side execution ('Claude requests file operations, and your application executes them'), the /memories prefix mapping, cross-session persistence, and the exact auto-injected protocol text including ASSUME INTERRUPTION. Engineering post confirms the Sonnet 4.5 public-beta launch and pairs it with 'structured note-taking' (NOTES.md, to-do lists) that agents re-read after context resets. Cookbook demo shows a fresh session reading prior session's memory file and resuming instead of re-researching. Caveats: the developer must implement the storage backend; the injected prompt encourages but does not guarantee memory-first reads. (Merged claims 2, 9, 11, 12, each 3-0.)

- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools

### Compact-vs-clear is not either/or

**Confidence: high** — Compact-vs-clear is not either/or: Anthropic's recommendation for long-running agents is to combine server-side compaction (auto-summarizes as the conversation approaches the context limit, keeping active context small) with file-based memory (preserves the information that must survive summarization).

Evidence: Docs verbatim: 'For long-running agents, consider using both: compaction keeps the active context small without client-side bookkeeping, and memory preserves the information that must survive summarization.' Minor tone caveat: 'consider using both' is a hedged suggestion, and the same page also offers client-side context editing as an additional pairing. (Claim 13, 3-0.)

- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

### Technique-to-task matching for orchestrators

**Confidence: high** — Technique-to-task matching for orchestrators: compaction suits tasks needing extensive conversational back-and-forth; structured note-taking suits iterative development with clear milestones; sub-agent architectures suit parallel research — with each subagent exploring extensively (tens of thousands of tokens) but returning only a condensed summary of roughly 1,000–2,000 tokens to the orchestrator, keeping the orchestrator's context lean.

Evidence: Verbatim: 'Compaction maintains conversational flow for tasks requiring extensive back-and-forth; Note-taking excels for iterative development with clear milestones; Multi-agent architectures handle complex research and analysis where parallel exploration pays dividends... returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens).' Consistent with Anthropic's multi-agent research system post. Framed as 'for example' guidance rather than hard mandate. (Claim 3, 3-0.)

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Automatic compaction alone is insufficient for long-running multi-context-window work

**Confidence: high** — Automatic compaction alone is insufficient for long-running multi-context-window work: Anthropic states that even a frontier model (Opus 4.5) on the Claude Agent SDK with compaction 'will fall short of building a production-quality web app' without additional harness structure — the failure modes being one-shot attempts and compaction failing to pass clear instructions to the next agent. The prescribed remedy is deliberate harness artifacts, not better summarization.

Evidence: Verbatim: 'compaction isn't sufficient. Out of the box, even a frontier coding model like Opus 4.5 running on the Claude Agent SDK in a loop across multiple context windows will fall short of building a production-quality web app if it's only given a high-level prompt.' The article prescribes an initializer agent writing feature-requirement JSON, claude-progress.txt, init.sh, and git commit checkpoints. Notably a self-critical first-party admission, not marketing. (Claim 4, 3-0.)

- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

### The prescribed handoff-artifact structure and session ritual for fresh-instance relaunch

**Confidence: high** — The prescribed handoff-artifact structure and session ritual for fresh-instance relaunch: an initializer session deliberately sets up (a) a progress log tracking done/next (claude-progress.txt), (b) a feature/scope checklist, and (c) a pointer to the startup/init script — paired with git commit history. Each fresh session opens by reading the progress notes and git logs, then runs a basic verification test to catch undocumented bugs before selecting the next unit of work (read state, then verify — don't trust blindly), and ends by writing a git commit and progress update. Together these let a fresh-context agent reconstruct state without replaying prior transcripts or re-exploring the codebase.

Evidence: Harness post verbatim: 'The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the claude-progress.txt file alongside the git history' and 'Start the session by reading the progress notes file and git commit logs, run a basic test on the development server to catch any undocumented bugs. End the session by writing a git commit and progress update.' Memory-tool docs' multi-session pattern independently prescribes the initializer session with progress log, feature checklist, and init-script reference, plus end-of-session updates and 'mark a feature complete only after end-to-end verification.' (Merged claims 5, 6, 14, each 3-0.)

- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

### What to adopt for the /drain orchestrator (synthesis of the above)

**Confidence: high** — What to adopt for the /drain orchestrator (synthesis of the above): (1) Handoff triggers — relaunch proactively on a token/context threshold (Anthropic's clearing default of 100k input tokens is a reasonable calibration point; degradation is a gradient, so hand off before limits, and treat repeated failed corrections or forgotten instructions as soft signals), and always at clean task boundaries since committed task files already checkpoint state. (2) Handoff artifact — a done/next progress log updated at every task boundary, the queue/scope checklist (already in committed task files), a pointer to any init/setup command, and descriptive git commits; assume interruption at any moment, so never let orchestration state exist only in context. (3) Fresh-instance startup ritual — read the progress log and git log first, run a cheap verification command to catch undocumented drift, then select the next queued task; re-read only the state files and the current task file, not prior transcripts. (4) Cache economics — a fresh relaunch that re-reads a compact state file is the cheap path; if staying in-session and clearing, clear in large batches (clear_at_least-style) since every clear invalidates the cached prefix and incurs a cache write.

Evidence: Derived recommendation, but every element maps to a 3-0 confirmed claim: proactive-threshold triggering follows from context rot (claims 0/7) and the 100k clearing default (claim 15); the artifact contents follow from claims 5 and 14; assume-interruption from claim 12; the read-then-verify ritual from claim 6; batch-clearing cache economics from claims 10/16; subagents-return-summaries (claim 3) supports keeping worker output out of orchestrator context. /drain's committed task files already satisfy the feature-checklist artifact; the main gaps versus Anthropic's prescription are an explicit done/next progress log, an end-of-session update discipline, and a startup verification step.

- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- https://platform.claude.com/docs/en/build-with-claude/context-editing
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools

## Follow-up findings (2026-07-03)

A same-day follow-up deep-research run (106 agents; 24 claims confirmed 3-0,
1 refuted, 0 unverified) closed the OpenAI/Google leg with primary sources
only, all fetched live 2026-07-03. The Anthropic re-verification leg (leg B)
produced zero surviving claims for the second time — see the rewritten
Caveats. This section answers the first open question below.

### OpenAI (Agents SDK + Cookbook)

- **Sessions are the sanctioned memory abstraction** (3-0 on three merged
  claims): history is auto-retrieved/prepended before each run and stored
  after, per session ID — "the session becomes the memory object."
  https://openai.github.io/openai-agents-python/sessions/ ·
  https://cookbook.openai.com/examples/agents_sdk/session_memory
- **Trimming AND compaction are built in** (3-0; the contrary claim refuted
  0-3): `SessionSettings(limit=N)` and `session_input_callback` for trimming;
  `OpenAIResponsesCompactionSession` auto-compacts (clears and rewrites
  history), with docs recommending disabling the auto trigger and calling
  `run_compaction()` manually at idle points for latency-sensitive apps.
  **This corrects the prior belief — carried in the follow-ups brief, though
  never asserted in this doc's findings — that OpenAI lacks built-in
  compaction; do not repeat the refuted call_model_input_filter framing.**
  https://openai.github.io/openai-agents-python/sessions/
- **An explicit trim-vs-summarize rule of thumb** (3-0 on three merged
  claims): trim (keep last N turns, deterministic) when tasks are
  local/independent; summarize (≤200-word synthetic summary with an
  anti-hallucination instruction) only when decisions, IDs, and constraints
  must survive — flagging summary drift, compounding errors, and context
  poisoning as the costs. Cookbook example patterns, not SDK API parameters.
  https://cookbook.openai.com/examples/agents_sdk/session_memory
- **Checkpointing model** (3-0 on four merged claims): persistent session
  backends (SQLite/SQLAlchemy/Redis/MongoDB/Dapr/hosted Conversations) carry
  history across restarts; the JS SDK's `RunState` is a serializable
  checkpoint (`toString()`/`fromString()`) taken at human-in-the-loop
  interruption points; durable failure recovery is deferred to
  Temporal/Dapr/Restate/DBOS rather than built into the SDK.
  https://openai.github.io/openai-agents-python/running_agents/ ·
  https://openai.github.io/openai-agents-js/openai/agents/classes/runstate/

### Google (ADK + Gemini)

- **ADK ships built-in compaction** (3-0 on two merged claims):
  `EventsCompactionConfig` with `token_threshold` and `compaction_interval`
  triggers; it summarizes-not-deletes, keeping `event_retention_size` recent
  events raw and overlapping `overlap_size` prior events into each new
  summary (Python; TypeScript uses TokenBasedContextCompactor, Java documents
  only interval/overlap). https://google.github.io/adk-docs/context/compaction/
- **Three-tier state architecture, all outside the context window** (3-0 on
  six merged claims): SessionService owns session lifecycle with swappable
  backends; `session.state` is a prefix-scoped scratchpad (`user:`, `app:`,
  `temp:`); Memory is a searchable cross-session store populated by explicit
  end-of-session ingestion (`add_session_to_memory`) — the sanctioned
  external-memory/handoff pattern is a queried service, not compaction of the
  live thread. https://google.github.io/adk-docs/sessions/ ·
  https://google.github.io/adk-docs/sessions/state/ ·
  https://google.github.io/adk-docs/sessions/memory/
- **Gemini cache economics** (3-0 on four merged claims): implicit caching is
  on by default for Gemini 2.5+ with stable-prefix ordering as the official
  hit-maximizing pattern; cached input is ~10% of standard price; explicit
  caches add a per-hour storage fee ($4.50/1M/hr Pro-tier, $1.00/1M/hr
  Flash-tier) — an idle carrying cost, unlike Anthropic's one-time TTL-based
  cache-write premium. https://ai.google.dev/gemini-api/docs/caching ·
  https://ai.google.dev/gemini-api/docs/pricing

### Does any of this change the adopt-list?

No. Nothing in the "What to adopt for the /drain orchestrator" finding is
overturned; the cross-vendor evidence independently corroborates the core
doctrine (relaunch from durable external artifacts; state owned by services
outside the window; summaries risk drift/poisoning). Three refinements:
(1) the open item "no concrete clear-vs-continue rule of thumb" now has a
vendor-explicit answer from OpenAI — trim/clear when turns are independent,
compact/summarize only when decisions/IDs/constraints must persist — which
maps directly onto /drain's relaunch-at-task-boundaries trigger and
strengthens it (drain's decisions live in committed task files, so
clear-and-relaunch is the right side of the criterion); (2) any residual
belief that OpenAI lacks built-in compaction should be deleted, and OpenAI's
disable-auto-compaction-run-manually-at-idle guidance parallels Anthropic's
clear-in-large-batches cache advice; (3) the cache-economics item gains a
Gemini footnote — implicit caching makes fresh-relaunch re-reads cheap
automatically, but explicit caches carry idle cost, so on Gemini prefer
implicit; irrelevant while the toolkit targets Claude.

### What did not close

Leg B (the six Anthropic re-verification targets) produced zero surviving
claims on this second attempt; Meta and xAI produced nothing at all, leaving
it unresolved whether they publish first-party guidance.

## Caveats

1) Vendor coverage for context management is now Anthropic + OpenAI + Google: the 2026-07-03 follow-up run closed the OpenAI (Agents SDK sessions/trimming/compaction/checkpointing) and Google (ADK compaction/session-state/memory, Gemini caching) legs with 24 unanimous primary-source claims. Meta and xAI remain uncovered — no surviving claims in either run, and it is unresolved whether they publish first-party agent context-management guidance at all. 2) The leg-B Anthropic items remain unverified after TWO attempts (infrastructure errors in the first run, zero surviving claims in the second): Claude Code's context-degradation symptoms and the '/clear after more than two failed corrections' threshold; auto-compact customization via CLAUDE.md and /compact <instructions>; the memory-tool warning-before-clear integration; compaction-as-primary vs context-editing positioning; and the Managed Agents checkpoint-and-relaunch pattern (wake(sessionId), getEvents(), durable session log, warning against irreversible pruning). Treat those as plausible but uncited. 3) One claim was formally refuted in the follow-up (call_model_input_filter as OpenAI's trimming mechanism / no built-in OpenAI compaction) — do not repeat that framing; also note OpenAI's trim/summarize strategies are official Cookbook example patterns, not SDK API parameters (the built-in equivalents are SessionSettings and OpenAIResponsesCompactionSession), and ADK's token_threshold is Python-specific with docs mid-migration from google.github.io/adk-docs to adk.dev. 4) Time-sensitivity: 'public beta' descriptors reflect launch-time status (Sonnet 4.5, Sept 2025); the memory tool is now GA and context editing uses beta headers that may change. All docs were verified live as of 2026-07-03; the cookbook page is dated 2026-03-20; Gemini pricing and minimum cache-token thresholds already changed across the 2.5→3.x lineup and will change again. 5) No confirmed source gives a numeric threshold for when an ORCHESTRATOR specifically should hand off to a fresh instance — the 100k default is for tool-result clearing, OpenAI's trim-vs-summarize criterion is qualitative, and the harness guidance prescribes task/feature boundaries rather than token counts; the adoption finding's trigger guidance is an inference. 6) Prompt-cache TTL economics for the Anthropic relaunch-vs-compact trade-off (5-minute vs 1-hour cache, cost of full re-read on relaunch) remain unquantified; only the clear_at_least invalidation rule is confirmed, and the new Gemini numbers are vendor-specific (implicit-cache savings are best-effort; the all-in explicit-cache discount is below 90% once storage is counted).

## Open questions

- What do OpenAI (Agents SDK sessions, trimming/summarization helpers) and Google (ADK session state, Gemini context caching) actually prescribe for compact-vs-clear and orchestrator handoff, and do they converge with Anthropic's file-based external-memory doctrine?
- Does Anthropic's Managed Agents architecture (wake(sessionId), getEvents(), durable session log, warning against irreversible pruning) hold up under verification — it would be the most direct published answer to 'should a long-running orchestrator hand off to a fresh instance of itself'?
- Is there a confirmed quantitative operator-facing threshold for clearing vs continuing (e.g., the unverified 'more than two failed corrections → /clear' rule in Claude Code best practices), or any published measurement of at what context fill fraction orchestration quality degrades?
- What are the concrete cache-economics of a full fresh relaunch (cold cache, re-reading state files) versus staying in-session with compaction, given prompt-cache TTLs and cache-write pricing — no verified source quantified this trade-off?