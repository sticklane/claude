# Subagent Intermediate-Output Token Savings: Vendor Guidance Survey (2026-07)

> Targeted primary-source research, 2026-07-05: one scout over this repo's
> existing doctrine plus four targeted general-purpose research agents (one
> per lab: Anthropic, OpenAI, Google DeepMind, DeepSeek), each required to
> back every claim with a verbatim quote + URL or mark it UNVERIFIED.
> Commissioned by an `/idea` research request: what do the major labs publish
> about saving tokens — particularly in subagents/multi-agent systems — by
> changing what intermediate state gets output or carried forward, and is
> there anything this toolkit should adopt.

## Summary

All four labs converge on the same core doctrine this toolkit already
implements: a subagent should explore extensively but return only a
distilled summary, never its full transcript, back to the orchestrator
(`.claude/rules/token-discipline.md`'s "cap subagent returns at 1–2k
tokens" is close to a direct quote of Anthropic's own number). Two
additional, concrete, and previously-uncodified techniques survived
verification and are worth adopting: (1) large intermediate artifacts
(diffs, search dumps, logs) should be written to disk with only a path
returned, not pasted into the subagent's report — Anthropic's own
multi-agent research system does exactly this; (2) on the model tiers this
toolkit actually dispatches (Opus 4.5+/Sonnet 4.6+), extended-thinking
blocks are kept by default and re-billed as input tokens on every
subsequent turn, which is a concrete, model-specific reason (beyond the
existing context-rot rationale) to prefer a fresh subagent dispatch over
letting one thread's reasoning grow across many turns. Reasoning/thinking
token handling was flagged as a gap in this repo's prior context-management
research doc — this closes that gap for the vendors it names.

## Verified findings

### Universal: subagents return distilled summaries, not transcripts

**Confidence: high.** All four labs' published guidance converges: a
subagent/sub-task should explore using many tokens internally but return
only a short, distilled result.

- Anthropic: "Each subagent might explore extensively, using tens of
  thousands of tokens or more, but returns only a condensed, distilled
  summary of its work (often 1,000-2,000 tokens)."
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic Agent SDK: "Intermediate tool calls and results stay inside the
  subagent; only its final message returns to the parent" — the subagent
  gets none of "the parent's conversation history or tool results."
  https://code.claude.com/docs/en/agent-sdk/subagents
- OpenAI: `nest_handoff_history` "collapses the prior transcript into a
  single assistant summary message"; cookbook patterns recommend
  compressing "the earlier conversation into a precise, reusable snapshot"
  (≤200 words).
  https://openai.github.io/openai-agents-python/running_agents/ ·
  https://cookbook.openai.com/examples/agents_sdk/session_memory
- DeepMind/Gemini: ReadAgent stores compressed "gists," retrieving full
  text only on demand, extending effective context "3-20x" (arXiv:2402.09727,
  Feb 2024).
- DeepSeek-V3.2: fixed per-step KV budget (2048 tokens/query) "enabling
  extended reasoning chains within fixed token budgets" — the serving-layer
  analogue of capping what a single step carries forward.
  https://arxiv.org/html/2512.02556v1

This repo already implements the actionable version of this
(`.claude/rules/token-discipline.md`: "Cap subagent returns at 1–2k
tokens — a structured verdict or distilled summary, never the
transcript"). No change needed; this section is corroboration, not a gap.

### New: externalize large artifacts, return a reference not the content

**Confidence: high.** Anthropic's multi-agent research system post
describes an explicit artifact pattern distinct from summarization:
"Subagents call tools to store their work in external systems, then pass
lightweight references back to the coordinator" rather than routing full
output through the lead agent's context.
https://www.anthropic.com/engineering/multi-agent-research-system

This is a different lever from "summarize your findings" — it applies when
the artifact itself (a full diff, a search-result dump, a log) is the
useful output and summarizing it would be lossy. This repo already does
this by convention (evidence files under `specs/*/evidence/`, task files
as durable state) but has never stated it as a general dispatch principle
that applies to worker prompts beyond the drain/build evidence-file
pattern specifically.

**Gap:** not yet stated as a general Dispatch-authoring rule.

### New: thinking-token replay cost on current model tiers

**Confidence: high.** Anthropic's extended-thinking docs draw a
version-dependent line: on Opus 4.5+/Sonnet 4.6+, thinking blocks are kept
by default and billed as input tokens on replay in later turns; on earlier
Opus/Sonnet and all Haiku models, prior-turn thinking is stripped
automatically. "You're still charged for the full thinking tokens [once,
as output]. Omitting reduces latency, not cost" describes the older-model
behavior; the newer-model default keeps and re-bills them.
https://platform.claude.com/docs/en/build-with-claude/extended-thinking

Cross-lab corroboration for the general shape (reasoning state resets at a
task/turn boundary, not mid-task):

- OpenAI: "If you're using the Chat Completions API, reasoning items are
  never included in the context of the model" (stateless); the Responses
  API can pass them forward explicitly via `previous_response_id` but does
  not by default.
  https://developers.openai.com/api/docs/guides/reasoning-best-practices
- Gemini: raw thinking is hidden by default ("By default, only the final
  output is returned"); `includeThoughts: true` returns a *summary*, not
  the raw trace, and billing is "based on the full thought tokens the
  model needs to generate... despite only the summary being output."
  https://ai.google.dev/gemini-api/docs/thinking
- DeepSeek-V3.2: "Historical reasoning content is discarded only when a
  new user message is introduced... If only tool-related messages are
  appended, the reasoning content is retained" — reasoning persists within
  a task, resets at the next conversational boundary.
  https://arxiv.org/html/2512.02556v1

**Gap:** this repo's session-hygiene rule ("One task per session; `/clear`
between tasks") already prescribes the right behavior, but doesn't cite the
concrete, model-specific cost mechanism (thinking-block replay billing on
the models this toolkit actually pins) as the reason. Worth citing so the
rule reads as evidence-based rather than a stylistic preference.

## Not adoptable (model-internal or provider-specific, no orchestration-layer lever)

- DeepSeek-V3.2 sparse KV/attention selection (O(L²)→O(Lk)) — a model
  architecture change, not something a toolkit can apply from outside.
- DeepMind's MELODI recurrent memory compression (8x KV footprint
  reduction, arXiv:2410.03156) — same: model-internal.
- Gemini's "thought signature" resend requirement for stateless multi-turn
  continuity — a Gemini-API-specific mechanic; Claude Code's session model
  doesn't have an equivalent resend step for this toolkit to adopt.
- OpenAI/Gemini prompt-caching specifics (minimum token counts, TTL
  numbers, discount percentages) — provider-specific plumbing; the
  underlying principle ("stable content first, don't churn mid-session")
  is already in this repo's Cache economics section and is Claude's own
  mechanism, not these vendors'.
- DeepSeek-R1's forced `<think>\n` prefix — an R1-specific prompting
  workaround unrelated to context/token economy.

## Recommendation

Add two bullets to `.claude/rules/token-discipline.md`'s Dispatch
authoring section:

1. For a worker whose useful output is a large artifact (a full diff, a
   search-result dump, a log) rather than a verdict, write the artifact to
   disk and return a path — never paste it into the return message.
2. Prefer a fresh subagent dispatch over growing one thread's reasoning
   across many turns: on the model tiers this toolkit dispatches, thinking
   blocks are kept and re-billed as input on every subsequent turn, not
   just written once.

## Open questions

- Anthropic's extended-thinking docs describe the Opus 4.5+/Sonnet 4.6+
  keep-and-rebill behavior generally; no primary source was checked here
  for the exact current pin (Sonnet 5 / Opus 4.8) — assume it holds unless
  a future doc revision says otherwise.
- No source (from any lab) ties reasoning-token retention/discard policy
  specifically to *multi-agent delegation* (as opposed to single-thread
  multi-turn conversation) — the thinking-token finding above is inferred
  to apply to "one subagent's own multi-turn work," not verified against a
  worked multi-agent example.
