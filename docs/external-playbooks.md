# Cross-vendor agent practices the toolkit adopts

What OpenAI and Google/DeepMind publish about building agents, filtered to
what this toolkit adopted (or deliberately rejected). Companion to
[anthropic-playbook.md](anthropic-playbook.md); skills cite this file
rather than restating it. Verified against primary sources, July 2026.

## Adopted from OpenAI

- **Untrusted data.** The Model Spec: instructions inside tool outputs
  "MUST be treated as information rather than instructions." Codex ships
  network-off-by-default and injection warnings. → `rules/untrusted-data.md`
  and the hardening clause in the /drain and /autopilot worker prompts.
  [Model Spec](https://model-spec.openai.com/2025-04-11.html),
  [Codex approvals/security](https://developers.openai.com/codex/agent-approvals-security)
- **Escalation triggers + tool risk tiers.** "A Practical Guide to
  Building Agents": rate every tool by reversibility, blast radius, and
  account permissions; hand control back on (a) retry thresholds exceeded
  or (b) high-risk actions reached. → /autopilot's walk-away contract.
  [Guide PDF](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- **Calibrated eagerness.** GPT-5 prompting guide: explicit early-stop
  criteria and tool-call budgets for search-shaped work. → the scout
  agent's early-stop rule.
  [GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide)
- **When NOT to build an agent.** Agents suit complex judgment,
  unmaintainable rulesets, unstructured data; "otherwise, a deterministic
  solution may suffice." → /idea's deterministic-first gate.
- **Eval-driven development.** Establish an eval baseline, grade real
  traces, re-run on every change. → the /evals skill (with Google's
  trajectory framing below).
  [Langfuse agent evals](https://cookbook.openai.com/examples/agents_sdk/evaluate_agents)

## Adopted from Google / DeepMind

- **Trajectory + artifact evaluation as a regression suite.** The Agents
  Companion whitepaper and ADK split evals into capabilities, trajectory,
  and final response, run against stored evalsets in CI. → /evals: stored
  scenarios, artifact assertions first, trajectory greps optional.
  [Agents Companion](https://www.kaggle.com/whitepaper-agent-companion),
  [ADK evaluate](https://google.github.io/adk-docs/evaluate/)
- **Contracts carry budgets.** Companion v2's task contracts include
  expected cost/duration and a negotiation step before acceptance.
  → /breakdown's `Budget:` line; workers stop-and-report rather than
  grind past it.
- **Generate–filter–rank.** AlphaCode 2: sample diverse candidates,
  filter on tests, submit the best (~2× solve rate). → /drain's
  tournament: on a second failure, three parallel attempts from different
  angles, drain ranks the survivors mechanically.
  [AlphaCode 2 report](https://storage.googleapis.com/deepmind-media/AlphaCode2/AlphaCode2_Tech_Report.pdf)
  Follow-on: N-vote adjudication — multiple independent verifier votes
  with majority rule — is the standard cure for single-judge error in
  generate–filter–rank pipelines (harness-observed Workflow quality
  pattern: adversarial verify votes; adopted here for the tournament
  filter). Harness-observed; no public URL.
- **Evidence artifacts.** Antigravity agents persist screenshots and
  walkthroughs of their own testing. → the verifier writes its report to
  `specs/<slug>/evidence/`, and /build commits it.
- **Self-correction needs external signal.** "LLMs Cannot Self-Correct
  Reasoning Yet": intrinsic reflection without external feedback degrades
  answers. Validates the toolkit's runnable-checks design; the standing
  rule is **never add a feedback-free reflect-and-retry loop**.
  [arXiv:2310.01798](https://arxiv.org/abs/2310.01798)

## Code-vs-LLM ladder

Where the three vendors converge on architecting generative-AI features
→ /design's classification gate and `.claude/skills/design/reference.md`.

- **Agreement**: default deterministic; escalate incrementally (pure code
  → single structured-output call → workflow patterns → single agent →
  multi-agent); code owns orchestration, loop exits, and side effects;
  structured output at every code/LLM seam; smallest capable model.
- **Cost anchors**: Anthropic reports agents ≈4× the tokens of chat and
  multi-agent systems ≈15× (self-reported internal data) — the economic
  gradient behind the ladder's lowest-rung default.
- **Named disagreements**: Google's Agents Companion leans multi-agent
  earlier than Anthropic/OpenAI's single-agent-first default — rejected;
  rung 4 stays breadth-first-only. OpenAI treats schema-enforced
  structured outputs as sufficient; Gemini guidance says validate model
  output in application code anyway — the toolkit sides with validation.
- Sources: [Building effective agents](https://www.anthropic.com/research/building-effective-agents),
  [multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
  (the 4×/15× anchors),
  [A Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf),
  [Agents Companion](https://www.kaggle.com/whitepaper-agent-companion)
  (secondary-verified — Kaggle mirror, not a Google primary).

## Considered and rejected

- OpenAI handoffs / parallel guardrail classifiers — harness-level
  mechanisms, not expressible as skills.
- AgentOps telemetry (OpenTelemetry spans, KPI dashboards) — production
  agent-ops, out of scope for a dev toolkit; /fleet covers the live view.
- "Single-agent-first" as a default — the toolkit's fan-out is justified
  by context economics (see token-discipline); kept only as a caution
  against gratuitous parallelism.
- Beads (Yegge's git-backed issue DAG) as the queue backend — evaluated
  and specced, then removed by maintainer decision (2026-07): work
  tracking stays in markdown task files with Status/Depends-on headers,
  which every runtime can read and diff; the useful ideas that rode
  with it (discovered-work capture, ready-work dispatch, priority
  fields) are adopted natively by their own specs instead.

## Context management

How the toolkit spends, preserves, and recovers context across
compaction, memory, and caches → `rules/token-discipline.md` (cache
economics), CLAUDE.md (Compact instructions; authoring conventions),
and /distill (memory layer). Those files state the rules; the research
stays here.

- **Adopted.** Compaction steering via CLAUDE.md's "Compact
  instructions" (R1) and the post-compact survival conventions —
  execution-critical contracts in a SKILL.md's first 30 lines,
  reference-file TOCs, references one level deep (R2) ← Anthropic's
  context-engineering post (context as a finite attention budget;
  progressive disclosure) plus the Claude Code docs on auto-compact
  (descriptions reload after compaction; bodies do not). Agent-written
  memory — `docs/memory.md` index plus `docs/memory/` topic files,
  pruned on write (R3) ← the same post's structured note-taking /
  agentic-memory pattern and ADK's sessions/memory split (long-term
  memory is curated and searched on demand, never accumulated into the
  prompt). Static-first cache economics (R4) ← OpenAI's prompt-caching
  guide (stable prefix first; any edit invalidates the cached prefix)
  and Anthropic's prompt-caching docs. Tool-call ceilings on critic and
  verifier with a non-PASS INCOMPLETE verdict (R5) ← the GPT-5
  prompting guide's tool budgets and early-stop criteria, extended from
  the scout. Machine-read fields as single-line `Key: value` headers
  (R6) ← ADK's separation of structured session state from prose
  history.
- **Already covered before this pass.** Attention budget and JIT
  retrieval (token-discipline); subagent isolation — Anthropic's
  guidance that research subagents return 1,000–2,000-token summaries
  validates the scout's ≤300-word report budget; progressive disclosure
  (skills load reference files on demand).
- **Where the toolkit leads.** Tool-result size discipline: hard output
  budgets on every fan-out agent's report. No vendor guidance found on
  sizing the results an agent returns to its caller — the closest is
  Anthropic's summaries-over-raw-dumps note above.
- **Deliberately skipped.** ADK scope tiers (`user:`/`app:`/`temp:`
  state prefixes) — harness-level session machinery a markdown toolkit
  cannot express. ADK artifact versioning — git already versions every
  artifact here. OpenAI verbatim-minus-tools handoffs — harness-level
  context transfer; the toolkit's handoffs are deliberate summaries on
  disk, not transcript copies.
- Sources: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
  [Claude Code docs](https://code.claude.com/docs) (compaction, memory,
  prompt caching),
  [ADK sessions & memory](https://google.github.io/adk-docs/sessions/)
  (docs home of the sessions/memory whitepaper material),
  [OpenAI prompt caching](https://platform.openai.com/docs/guides/prompt-caching),
  [GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide).

## Skill chaining

How stages hand off → CLAUDE.md's self-chain bullet (the canonical
gating explanation) and the `Next stage:` closing-line convention; the
research stays here.

- **Adopted: Skill-tool invocation.** Claude Code merged slash commands
  into skills and made skills model-invocable via the Skill tool by
  default; `disable-model-invocation: true` removes a skill from the
  model's reach entirely (its description is not even loaded for
  triggering). That pair is the mechanism behind the toolkit's chain:
  light artifact stages may invoke the next stage themselves
  (/idea → /breakdown), while gated stages stay human-launched by
  construction. [Claude Code docs](https://code.claude.com/docs)
  (skills, Skill tool).
- **Available but unadopted: context-fork.** Skill frontmatter can run a
  skill in a forked context (`context: fork`, with `agent:` selecting
  the executor), isolating the invocation from the calling session —
  a chaining primitive the toolkit doesn't use yet; its own future spec
  if wanted.
- **Available but unadopted: Stop-hook chain enforcement.** A Stop hook
  can block a session from finishing until the next pipeline stage has
  run, turning the chain from convention into mechanism — deliberately
  not adopted; /gate's Stop hook checks quality, not pipeline position.
- **ADK's chaining model**: workflow agents (`SequentialAgent`,
  `ParallelAgent`, `LoopAgent`) compose sub-agents in code, so chaining
  is deterministic orchestration, not model choice.
  [ADK workflow agents](https://google.github.io/adk-docs/agents/workflow-agents/)
- **OpenAI's chaining model**: Agents SDK handoffs transfer control
  between agents mid-conversation, model-decided at runtime.
  [A Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)

## Antipatterns

Vendor-named failure modes of agent pipelines, and where this toolkit
guards each. Seven findings; the guards live in the named files — this
entry is the research record.

1. **Dispersed decision-making across parallel workers.** Two subagents
   each resolve an open design choice differently and the results don't
   compose (the Flappy-Bird-vs-Mario failure: each half of a game built
   to a different visual style). Source: Cognition, "Don't Build
   Multi-Agents" — a lab's engineering post, not one of the three
   vendors this file tracks. → guarded by /breakdown's "decision
   coupling" test and /parallel's citation of it (R5).
   [Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)
2. **Vague delegation producing duplicate work.** Anthropic's
   multi-agent research system found early orchestrators gave subagents
   overlapping, under-specified briefs and got duplicated or missing
   coverage; the fix was explicit objectives, boundaries, and task
   divisions. → guarded by /breakdown's task-template boundary sentence
   (list what a task must NOT touch when sibling overlap is plausible)
   (R6). [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
3. **Effort–complexity mismatch.** Multi-agent systems cost ≈15× the
   tokens of chat (Anthropic's self-reported anchor, above); spending
   that on barely-parallel work is the antipattern. → guarded by
   token-discipline's fleet-scaling rule: one worker default, parallel
   only for genuinely divisible groups, fleet size from the task map
   (R7). [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
4. **Contradictory instructions across stacked prompt sources.** OpenAI's
   Model Spec resolves instruction conflicts with an explicit
   chain of command rather than leaving the model to guess; this
   toolkit stacks CLAUDE.md, rules, skills, and task files with the same
   exposure. → guarded by CLAUDE.md's `## Precedence` block, mirrored in
   the antigravity port (R4).
   [Model Spec](https://model-spec.openai.com/2025-04-11.html)
5. **Overlapping trigger surfaces.** Anthropic's tool-writing guidance:
   near-duplicate tool descriptions make selection ambiguous and waste
   calls; distinct, routed descriptions fix it. The toolkit's
   critique/code-review/review/verifier cluster had exactly this
   overlap. → guarded by /critique's description routing its neighbors
   away (R8). [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
6. **Feedback-free self-correction loops.** Already covered before this
   pass: "LLMs Cannot Self-Correct Reasoning Yet" (arXiv:2310.01798,
   above) — the standing rule bans reflect-and-retry without an
   external signal.
7. **Multi-agent by default.** Already covered before this pass: the
   Agents Companion (secondary-verified — Kaggle mirror, not a Google
   primary) leans multi-agent earlier than Anthropic/OpenAI guidance;
   rejected in the code-vs-LLM ladder — rung 4 stays
   breadth-first-only.

## Repo orientation for agents

How a fresh agent finds the map, the state, and the commands → this
repo's root `AGENTS.md` (+ CLAUDE.md's `@AGENTS.md` import),
`specs/status.sh`, and /onboard's repo-map / per-directory /
work-state / interop guidance. Those artifacts apply the practices;
the research stays here.

- **Convergence: small always-on root context file.** Anthropic's
  memory docs target under 200 lines
  ([memory](https://code.claude.com/docs/en/memory)); OpenAI Codex
  hard-caps project docs at 32 KiB via `project_doc_max_bytes`
  ([Codex AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)).
- **Convergence: pointers and JIT retrieval over content dumps.**
  Anthropic's best practices exclude "file-by-file descriptions"; the
  context-engineering post keeps "lightweight identifiers" in context
  and retrieves the rest on demand
  ([context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).
- **Convergence: nearest-file-wins hierarchy for depth.** Nested
  AGENTS.md ([agents.md](https://agents.md)); gemini-cli's GEMINI.md
  hierarchy; Claude Code's on-demand subdirectory CLAUDE.md
  ([large codebases](https://code.claude.com/docs/en/large-codebases)).
- **Convergence: structured work-state files.** Kiro specs split work
  into requirements/design/tasks with checkbox state
  ([Kiro specs](https://kiro.dev/docs/specs)); its steering files
  split standing context into product/tech/structure
  ([Kiro steering](https://kiro.dev/docs/steering)) — validating this
  repo's specs/ + `Status:` headers.
- **Convergence: AGENTS.md as the cross-tool interop standard.** Linux
  Foundation stewarded; read natively by Codex, Jules, Kiro CLI, and
  Android Studio; gemini-cli only via `context.fileName`; Claude Code
  via `@AGENTS.md` import or symlink.
- **Divergences.** Inclusion modes: Kiro steering offers
  always/fileMatch/manual inclusion vs Claude Code's `paths:` rules.
  AGENTS.md-by-default is not honored by gemini-cli (config required).
- **llms.txt**: published by vendors for their own doc sites; no coding
  tool consumes a repo's llms.txt — skipped here.

## Task prioritization

How the queue orders simultaneously-dispatchable tasks → the optional
`Priority:` task header, /drain's deterministic tie-break, and
/breakdown's priority rubric (the task-priority spec). Those artifacts
apply the practices; the research stays here.

- **Convergence: dependency graph → ready set → waves.** Every surveyed
  vendor schedules exactly the mechanism this toolkit already has —
  compute the ready set from the dependency graph, dispatch it in
  waves. Kiro groups tasks into dependency-ordered waves
  ([Kiro spec best practices](https://kiro.dev/docs/specs/best-practices));
  Copilot CLI's fleet dispatches multiple agents a wave at a time
  ([Copilot fleet](https://github.blog/ai-and-ml/github-copilot/run-multiple-agents-at-once-with-fleet-in-copilot-cli/));
  ADK's workflow agents provide sequential/parallel/loop ordering
  mechanisms, not ranking heuristics
  ([ADK workflow agents](https://adk.dev/agents/workflow-agents/));
  Jules ships concurrency caps only, with queue prioritization
  "planned" ([Jules usage limits](https://jules.google/docs/usage-limits/)).
- **The gap: within-ready-set ranking.** No vendor publishes a rule for
  which ready task goes first — ordering inside the ready set is
  universally unspecified. The toolkit's Priority → unblocking-power →
  path tie-break is therefore ahead of published guidance, not adopted
  from it.
- **Adopted signal: pre-assigned priority, one task at a time.**
  Anthropic's long-running-harness guidance: "choose the
  highest-priority feature that's not yet done", one at a time, with
  priority assigned ahead of the run — the agent honors the ordering,
  it doesn't invent it. → the `Priority:` header (human-editable) and
  drain's sequential dispatch.
  [Effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- **Adopted signal: proof-of-concept milestones first.** OpenAI's
  PLANS.md pattern for Codex sequences proof-of-concept milestones
  before the rest — implicit risk-first ordering. → /breakdown's P0
  rubric line: prove the spec's riskiest assumption first.
  [Codex exec plans](https://developers.openai.com/cookbook/articles/codex_exec_plans)
