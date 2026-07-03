# Multi-Agent Orchestration: Vendor Guidance Survey (2026-07)

> Deep-research run 2026-07-03 (103 agents; every claim below survived 3-vote
> adversarial verification against primary sources). Commissioned to decide how
> ultracode/Workflow orchestration should integrate into this toolkit — the
> resulting design is `specs/ultra-mode/SPEC.md`.

## Summary

All three vendors converge on the same core split: put control flow in deterministic code wherever the task is well-defined, and reserve model-driven orchestration for genuinely open-ended decisions. Anthropic canonizes this as workflows (predefined code paths: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer) versus agents, proves orchestrator-workers in its production Research system (+90.2% over single-agent, at ~15x token cost), and in Claude Code exposes it as three modes (parallel worktrees, subagents, agent teams) plus an Agent SDK where hooks carry deterministic control and the Agent tool carries model-driven delegation. OpenAI is even blunter: default to one agent, orchestrate via code (while-loop evaluator, output-to-input chaining, asyncio.gather fan-out) when speed/cost/determinism matter, and use handoffs vs agents-as-tools only when the "who owns the final answer" question demands it. No Google DeepMind ADK/A2A claims survived verification, so that leg rests on unverified material and is omitted. For the skill toolkit: codify as scripts the pipeline chaining (idea→critique→breakdown→build), capped parallel fan-out, a bounded (2-4 cycle) evaluator loop that prefers runnable acceptance commands over LLM judges, prompted effort-scaling tiers, and file-based resume-from-checkpoint state; leave model-driven the decomposition judgment inside breakdown, routing inside autopilot, and subagent delegation — with subagents returning only light summaries and a single-call rubric judge (not multi-judge voting) as the default verifier, reserving voting for adversarial critique passes.

## Verified findings

### Anthropic's foundational guidance defines the deterministic-vs-model-driven axis

**Confidence: high** — Anthropic's foundational guidance defines the deterministic-vs-model-driven axis: workflows are LLMs/tools orchestrated through predefined code paths, agents are LLMs dynamically directing their own processes; prefer workflows for well-defined tasks, agents only when flexibility is needed — and Anthropic explicitly endorses hybrids where decision points are either software-defined conditional logic or AI-driven routing on intermediate results.

Evidence: "Workflows are systems where LLMs and tools are orchestrated through predefined code paths... workflows offer predictability and consistency for well-defined tasks, whereas agents are the better option when flexibility and model-driven decision-making are needed at scale." The enterprise whitepaper adds: "Sequential workflows can leverage either software-defined decision points... or AI-driven routing where models decide application control flow based on intermediate results... This hybrid approach allows for both the reliability of predetermined paths and the flexibility to adapt." Verified verbatim against both primary sources; still Anthropic's current published position as of mid-2026.

- https://www.anthropic.com/research/building-effective-agents
- https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf

### Anthropic names five composable workflow building blocks — prompt chaining, rout

**Confidence: high** — Anthropic names five composable workflow building blocks — prompt chaining, routing, parallelization (sectioning and voting variants), orchestrator-workers, and evaluator-optimizer — as the recommended patterns for agentic systems, presented as a complexity continuum rather than prescriptions.

Evidence: "Orchestrator-Workers: A central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results. Evaluator-Optimizer: One LLM call generates a response while another provides evaluation and feedback in a loop." All five patterns verified verbatim in the primary source under 'Building blocks, workflows, and agents'; the post notes "These building blocks aren't prescriptive."

- https://www.anthropic.com/research/building-effective-agents

### Anthropic's production Research feature validates orchestrator-workers at scale

**Confidence: high** — Anthropic's production Research feature validates orchestrator-workers at scale: a lead agent plans and spawns specialized subagents exploring the query in parallel; the Opus 4 lead + Sonnet 4 subagent configuration outperformed single-agent Opus 4 by 90.2% on Anthropic's internal research eval — but the gain concentrates on breadth-first parallelizable queries, token spend explained ~80% of variance, and Anthropic says multi-agent is not suited to most coding tasks or high-dependency shared-context work.

Evidence: "a multi-agent architecture with an orchestrator-worker pattern, where a lead agent coordinates the process while delegating to specialized subagents... outperformed single-agent Claude Opus 4 by 90.2%." Verified verbatim; figure is self-reported (internal eval). The same post's caveats (15x tokens, breadth-first suitability only) were confirmed by the verifier and matter for the toolkit recommendation.

- https://www.anthropic.com/engineering/multi-agent-research-system

### Token economics are the vendors' primary gate on multi-agent orchestration

**Confidence: high** — Token economics are the vendors' primary gate on multi-agent orchestration: Anthropic reports multi-agent systems use ~15x the tokens of chat (single agents ~4x) and, in its 2025/26 whitepaper, roughly 10-15x more than single agents; its guidance directs limited-budget teams to single agents or carefully designed parallel workflows, with simple queries never triggering expensive multi-agent paths.

Evidence: "agents typically use about 4x more tokens than chat interactions, and multi-agent systems use about 15x more tokens as chats" (engineering blog) and "Limited budget/tokens -> Single agents or carefully designed parallel workflows. Multi-agent systems use roughly 10-15x more tokens than single agents. Do the math on your expected volume" (whitepaper). Both verified verbatim in primary sources. Note the two documents use different baselines (vs chat vs single agent) — an internal inconsistency in Anthropic's own numbers, but both figures are genuinely published.

- https://www.anthropic.com/engineering/multi-agent-research-system
- https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf

### Anthropic's production budget mechanism is prompted effort-scaling rules rather 

**Confidence: high** — Anthropic's production budget mechanism is prompted effort-scaling rules rather than hard-coded caps: the orchestrator is instructed that simple fact-finding gets 1 agent with 3-10 tool calls, direct comparisons get 2-4 subagents with 10-15 calls each, and complex research can exceed 10 subagents — fixing an early failure mode of spawning 50 subagents for trivial queries. (Hard deterministic knobs like max_turns do exist elsewhere in the Agent SDK/Claude Code, so this is scoped to the Research system.)

Evidence: "Agents struggle to judge appropriate effort for different tasks, so we embedded scaling rules in the prompts... Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, complex research might use more than 10 subagents." Verified verbatim; verifier confirmed no hard-coded budget mechanism is documented for this system.

- https://www.anthropic.com/engineering/multi-agent-research-system

### Anthropic's verification guidance is layered

**Confidence: high** — Anthropic's verification guidance is layered: (a) for eval/judging, a single LLM-as-judge call with one prompt producing 0.0-1.0 scores plus pass/fail against a five-part rubric (factual accuracy, citation accuracy, completeness, source quality, tool efficiency) beat multi-judge schemes for consistency; (b) the evaluator-optimizer generate/critique loop (typically 2-4 cycles in their example) should be avoided when deterministic checks exist, criteria are unclear, or token budgets are strict; (c) voting with several different prompts is recommended specifically for reviewing code vulnerabilities.

Evidence: "a single LLM call with a single prompt outputting scores from 0.0-1.0 and a pass-fail grade was the most consistent and aligned with human judgements" (engineering blog, rubric verified verbatim); "Avoid when deterministic solutions exist, when evaluator workflows lack domain expertise for meaningful feedback..." and "Voting patterns work well for reviewing code vulnerabilities with several different prompts" (whitepaper, verified via pdftotext). Note: 2-4 cycles comes from a worked example, not a universal prescription; voting sits under parallelization, not evaluator-optimizer.

- https://www.anthropic.com/engineering/multi-agent-research-system
- https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf
- https://www.anthropic.com/research/building-effective-agents

### Anthropic handles resumability at two levels

**Confidence: high** — Anthropic handles resumability at two levels: production Research agents get durable execution that resumes from the point of error (retry logic + checkpoints) and summarize completed phases to external memory so the research plan survives context limits; the Agent SDK exposes session-based resume/fork via a session ID captured at init, with state stored as JSONL on the local filesystem (vs an Anthropic-hosted event log for Managed Agents).

Evidence: "we built systems that can resume from where the agent was when the errors occurred... agents summarize completed work phases and store essential information in external memory before proceeding to new tasks" (engineering blog); SDK docs verified live 2026-07-03: "Resume sessions later, or fork them to explore different approaches" with resume=session_id, and the comparison-table row "Session state | JSONL on your filesystem | Anthropic-hosted event log."

- https://www.anthropic.com/engineering/multi-agent-research-system
- https://code.claude.com/docs/en/agent-sdk/overview

### In Anthropic's Agent SDK, the deterministic/model-driven placement is concrete

**Confidence: high** — In Anthropic's Agent SDK, the deterministic/model-driven placement is concrete: the SDK exposes the exact Claude Code agent loop and context management as a Python/TypeScript library (CLI workflows translate directly, modulo the system-prompt preset); multi-agent orchestration is model-driven via the Agent tool spawning custom subagents (tracked by parent_tool_use_id); deterministic control is injected via lifecycle hooks (PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd, UserPromptSubmit) that validate, log, block, or transform behavior — there is no workflow-graph primitive.

Evidence: Verified live 2026-07-03: "The Agent SDK gives you the same tools, agent loop, and context management that power Claude Code... Workflows translate directly between them"; "Subagents are invoked via the Agent tool... Messages from within a subagent's context include a parent_tool_use_id field"; hooks tab lists all six named hooks with "validate, log, block, or transform agent behavior." Caveats: CLI-parity needs the claude_code system-prompt preset; hooks are the in-loop deterministic surface but host code chaining query() calls is also deterministic; a script-based Workflow tool also exists for large-scale orchestration.

- https://code.claude.com/docs/en/agent-sdk/overview
- https://code.claude.com/docs/en/agent-sdk/subagents

### Anthropic's March 2026 Claude Code guidance distinguishes three multi-agent mode

**Confidence: high** — Anthropic's March 2026 Claude Code guidance distinguishes three multi-agent modes with distinct use cases — Parallel Claude (independent instances in separate worktrees for unrelated tasks), Subagents (focused subtasks with isolated context returning summaries), Agent Teams (coordinated workstreams for one large task) — and recommends subagents specifically when the role is well-defined with scoped tools and success criteria, delegation can be hands-off, and context management is the goal; the ideal case is parallel investigation returning only a light summary to the main agent.

Evidence: Slide deck (dated 2026-03-24, downloaded and text-extracted) verified verbatim: "Parallel Claude: Working on multiple unrelated tasks at once, each in its own terminal and worktree | Subagents: Delegating focused subtasks from the main session with isolated context | Agent Teams: Splitting a large task into independent workstreams that coordinate" and "Ideal Use Case: Parallel experimentation or investigation of the codebase, only requiring a lighter amount of information to be returned to the main agent." Taxonomy corroborated by official docs. Caveats: webinar deck rather than formal docs; Agent Teams was in research preview.

- https://resources.anthropic.com/hubfs/Claude%20Code%20Advanced%20Patterns_%20Subagents,%20MCP,%20and%20Scaling%20to%20Real%20Codebases.pdf
- https://code.claude.com/docs/en/agent-teams

### OpenAI's Agents SDK docs explicitly favor code-based over LLM-driven orchestrati

**Confidence: high** — OpenAI's Agents SDK docs explicitly favor code-based over LLM-driven orchestration when determinism and predictable speed/cost/performance matter, and its documented code-orchestration patterns are exactly the ones a script toolkit would codify: structured outputs inspected by code for routing, agent chaining (output-to-input pipelines), a while-loop worker + evaluator agent iterating until acceptance criteria pass (LLM-as-judge), and parallel fan-out via plain asyncio.gather — no bespoke orchestration framework.

Evidence: Verified live 2026-07-03, verbatim: "While orchestrating via LLM is powerful, orchestrating via code makes tasks more deterministic and predictable, in terms of speed, cost and performance"; "Running the agent that performs the task in a while loop with an agent that evaluates and provides feedback, until the evaluator says the output passes certain criteria"; "Chaining multiple agents by transforming the output of one into the input of the next... Running multiple agents in parallel, e.g. via Python primitives like asyncio.gather." Caveat: docs frame code-vs-LLM as mix-and-match tradeoffs rather than a flat recommendation; 'evaluator-optimizer' is Anthropic's term for what OpenAI calls the while-loop/judge pattern.

- https://openai.github.io/openai-agents-python/multi_agent/

### OpenAI's orchestration guidance is deliberately conservative and ownership-centr

**Confidence: high** — OpenAI's orchestration guidance is deliberately conservative and ownership-centric: start with one agent and add specialists only when they materially improve capability isolation, policy isolation, prompt clarity, or trace legibility; the primary multi-agent design choice is who owns the final user-facing answer — handoffs (specialist takes over the conversation, declared statically as handoffs: [billingAgent, handoff(refundAgent)]) versus agents-as-tools (manager stays in control, agent.asTool()). The developer deterministically constrains the routing surface in code; the model picks the route at runtime (handoffs are surfaced to the LLM as transfer_to_* tools).

Evidence: Verified live 2026-07-03, verbatim: "Start with one agent whenever you can. Add specialists only when they materially improve capability isolation, policy isolation, prompt clarity, or trace legibility"; "The first design choice is deciding who owns the final user-facing answer at each branch of the workflow"; Python SDK docs confirm "Handoffs are represented as tools to the LLM." Caveat: the ownership question is the primary choice within LLM-driven orchestration; the code-vs-LLM orchestration choice sits above it.

- https://developers.openai.com/api/docs/guides/agents/orchestration
- https://openai.github.io/openai-agents-python/handoffs/

### What-to-adopt for the git-tracked skill toolkit (idea/critique/breakdown/build/d

**Confidence: medium** — What-to-adopt for the git-tracked skill toolkit (idea/critique/breakdown/build/drain/parallel/autopilot): CODIFY AS DETERMINISTIC WORKFLOW SCRIPTS — (1) pipeline chaining idea→critique→breakdown→build with file artifacts as the interface (Anthropic prompt-chaining + OpenAI agent chaining; the existing file-based specs/tasks are exactly the recommended handoff medium); (2) parallel fan-out in /parallel and /drain as a scripted gather over independent task files, with a hard cap and effort tiers written into the dispatch prompt (1 agent/3-10 calls for simple, 2-4 for comparisons, 10+ only for genuinely breadth-first work) since prompted scaling rules are Anthropic's proven anti-runaway mechanism and multi-agent costs ~10-15x; (3) verification as a scripted gate that prefers runnable acceptance commands over LLM judges (both vendors: avoid evaluator loops when deterministic checks exist), falling back to a single-call rubric judge with 0-1 score + pass/fail, bounded at 2-4 evaluator-optimizer cycles in a code-owned while loop (OpenAI's pattern) inside /build and /autopilot; (4) resumability as checkpoint files per task (phase summaries + resume-from-error), matching Anthropic's durable-execution/external-memory design and the SDK's session-resume model; (5) Stop/PostToolUse hooks (already the /gate skill) as the deterministic in-loop enforcement layer. LEAVE MODEL-DRIVEN — decomposition judgment inside /breakdown, routing/next-task selection inside /autopilot (Anthropic's endorsed hybrid: script owns the loop, model owns decisions on intermediate results), subagent delegation with light-summary returns, and /critique as the one place voting/multi-prompt review is justified (Anthropic recommends voting for adversarial code review). Default remains single-agent per OpenAI unless the task is breadth-first and worth the token multiple.

Evidence: Synthesis finding: every element traces to a verified claim above (chaining/parallelization/evaluator patterns, prompted effort-scaling, prefer-deterministic-checks, single-call rubric judge, voting for code review, checkpoint/resume, subagent light-summary criterion, single-agent default). Marked medium because the mapping onto this specific toolkit is the researcher's interpretation, not vendor-attributed.

- https://www.anthropic.com/research/building-effective-agents
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://openai.github.io/openai-agents-python/multi_agent/
- https://developers.openai.com/api/docs/guides/agents/orchestration
- https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf
- https://resources.anthropic.com/hubfs/Claude%20Code%20Advanced%20Patterns_%20Subagents,%20MCP,%20and%20Scaling%20to%20Real%20Codebases.pdf

## Follow-up findings (2026-07-03)

The missing Google DeepMind leg was re-attempted on 2026-07-03 in a follow-up
deep-research run (106 agents, primary sources only). The relevant ADK pages
were fetched live — workflow-agents, loop-agents, runtime/resume,
multi-agents, a2a/intro, custom-agents — but **zero claims about
SequentialAgent/ParallelAgent/LoopAgent, deterministic-vs-model-driven
placement, verification/judging, budgets, resumability, or A2A survived
3-vote verification**. After two attempts the leg remains open: this report
still cannot make cited statements about Google's orchestration approach,
and the Anthropic-vs-OpenAI framing stands as-is.

Indirectly relevant corroboration from the same run's context-management leg
(see docs/context-management-research-2026-07.md, "Follow-up findings"):
both OpenAI and Google externalize agent state as first-class services
outside the context window — OpenAI via persistent Sessions and serializable
RunState with durable recovery deferred to Temporal/Dapr/Restate/DBOS,
Google via ADK's SessionService/State/Memory tiers with explicit
end-of-session ingestion. That cross-vendor pattern independently supports
the adopt-list's file-based resume-from-checkpoint state and the
fresh-relaunch-from-durable-artifacts doctrine. Nothing on the adopt-list
changes.

## Caveats

The Google DeepMind leg of the comparison is still missing after two attempts: no claims about ADK workflow agents (Sequential/Parallel/Loop), the A2A protocol, or Gemini Enterprise orchestration survived 3-vote verification in either the original 2026-07-03 run or the same-day follow-up re-attempt (which fetched the primary ADK workflow-agent and A2A pages but confirmed nothing), so this report cannot make cited statements about Google's approach — the deterministic-vs-model-driven comparison here is effectively Anthropic vs OpenAI, and the ADK leg remains an open question. Two Anthropic claims were refuted (the Hooks/CLAUDE.md/MCP responsibility mapping, and a sequential/hierarchical two-pattern taxonomy), so those framings should not be repeated. Anthropic's token-overhead figures are internally inconsistent across publications (15x vs chat in the June 2025 engineering blog; 10-15x vs single agents in the Dec 2025 whitepaper) and are self-reported internal data, as is the 90.2% eval improvement. The March 2026 three-modes guidance comes from a webinar slide deck (Agent Teams was in research preview), not formal documentation. OpenAI's docs frame code-vs-LLM orchestration as tradeoffs to mix and match, slightly softer than 'recommends.' Time-sensitivity: SDK surfaces (Agent tool naming, Workflow tool, hooks list) reflect docs as fetched 2026-07-03 and change quickly; the 'typically 2-4 cycles' evaluator bound comes from a worked example, not a universal prescription. The final what-to-adopt finding is interpretive synthesis, not vendor-attributed guidance.

## Open questions

- How does Google's ADK actually place deterministic (SequentialAgent/ParallelAgent/LoopAgent) vs model-driven (LlmAgent transfer) control flow, and does A2A add anything a solo single-machine toolkit would use? This leg needs a fresh verified research pass.
- Which baseline is right for budgeting: is multi-agent ~4x or ~10-15x the cost of a single agent? Anthropic's two publications disagree, and the answer changes the break-even for /parallel and /autopilot fan-out.
- Does Claude Code's script-based Workflow tool (mentioned in SDK docs but not deeply verified here) subsume the need for hand-rolled workflow scripts in the toolkit, and what are its budget/resume semantics?
- What is the empirically best judge configuration for code tasks specifically — Anthropic's single-call rubric judge was validated on research outputs, while its voting recommendation targets code vulnerabilities; no verified source tested judges on build-task acceptance.
