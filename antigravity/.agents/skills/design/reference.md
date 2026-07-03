# Code-vs-LLM ladder

Loaded on demand by /design's step-1 classification gate: when a decision
embeds generative AI in the product, classify each part of the feature on
this ladder before framing candidates. Scope: the ladder governs product
architecture only — the toolkit's own agent-usage scaling lives in
AGENTS.md (token discipline), and right-sizing process work stays behind
/idea's "a script, not a spec" gate. Research record and sources: the
toolkit repo's docs/external-playbooks.md ("Code-vs-LLM ladder") — not
shipped with installs.

## The ladder

Default to the lowest rung that meets the requirements; climb one rung at
a time, only when that rung's escalation trigger fires.

- **Rung 0 — pure code.** Deterministic logic: parsing, validation,
  routing on explicit fields, math, CRUD. Escalate when the rules cannot
  be written down, or the ruleset has grown unmaintainable.
- **Rung 1 — single LLM call**, with retrieval/examples in the prompt and
  structured output. Escalate when one prompt must do several distinct
  jobs and evals show it failing at their intersection.
- **Rung 2 — workflow patterns.** Multiple LLM calls composed by
  deterministic code, each pattern with its own trigger:
  prompt-chaining (fixed sequential steps, each checkable in code),
  routing (distinct input categories served better by separate prompts),
  parallelization (independent subtasks, or voting on one),
  orchestrator-workers (subtasks unpredictable upfront, but code still
  owns the loop), evaluator-optimizer (clear eval criteria and iteration
  measurably improves output). Escalate when the path through the work
  cannot be predetermined at all.
- **Rung 3 — single agent.** The model drives an open-ended tool loop —
  step count unknowable in advance. OpenAI's three criteria, all worth
  checking: complex decision-making beyond rules, a brittle or
  unmaintainable ruleset, heavy reliance on unstructured data; otherwise
  a deterministic solution may suffice. Escalate when the task is
  breadth-first and genuinely parallelizable.
- **Rung 4 — multi-agent.** Breadth-first parallelizable work only —
  independent subtasks that don't share state. Costs ~15× the tokens of
  chat (single agents ~4×); never the default.

## Per-part tests

Apply to each part of the feature separately — most features split
across rungs. A part belongs on a higher rung only when:

- **Rule-expressible?** If you can write the rules, write them (rung 0).
- **Nuanced judgment?** Tone, intent, relevance — genuine model work.
- **Ruleset maintainability:** rules that sprawl with every edge case
  argue for a model; three stable rules don't.
- **Unstructured input?** Free text, images, audio favor a model call.
- **Failure tolerance:** wrong-answer cost is high → stay low, add
  human review, or keep it in code.
- **Latency/cost budget:** every rung multiplies both.
- **Eval-ability:** escalate only when evals show the lower rung
  actually failing — never on anticipated inadequacy.

## Seam rules

- Structured output at every code/LLM boundary — schema-constrained
  generation, AND validated in application code before use. (OpenAI
  treats schema enforcement as sufficient; Gemini guidance says validate
  in application code anyway. The toolkit sides with validation: the
  schema can't check semantics, and seam bugs are the expensive kind.)
- Side effects and loop exits live in code. The model emits arguments
  only; deterministic code decides whether to execute, retry, or stop.
