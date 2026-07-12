# Ground model-routing guidance in OpenAI/DeepMind/DeepSeek research (configurability already exists)

Breakdown-ready: true

## Problem

Per-task-type model configurability already exists in this toolkit —
`runtimes/README.md` + `runtimes/claude-code.md` (and `antigravity.md`,
`gemini-cli.md`) define a four-tier ladder (scout/session/deep/frontier)
mapped to concrete models, and a user overrides it per-repo by writing
`.claude/runtime.md`. `docs/guides/model-routing.md` already documents this
ladder and cites Anthropic's own published guidance. What's missing,
confirmed by three targeted research passes: the guide cites Anthropic
only — it has no grounding from OpenAI, Google DeepMind, or DeepSeek, all
of which the user wants represented. This is a documentation-grounding
gap, not a missing mechanism.

## Solution

Add a new `## Cross-vendor grounding` section to
`docs/guides/model-routing.md`, inserted immediately before its existing
`## Rules and skills this page explains` section (i.e., directly after the
page's current Anthropic-sourced content, which ends at line 69) — this is
the exact, unambiguous insertion point, not "somewhere after Anthropic."
Its content is these verbatim quotes, each with the real page URL it came
from (not a domain stem):

- **OpenAI:**
  - "Optimize for accuracy until you hit your accuracy target." —
    https://developers.openai.com/api/docs/guides/model-selection
  - "Then aim to maintain accuracy with the cheapest, fastest model
    possible." —
    https://developers.openai.com/api/docs/guides/model-selection
  - "Most AI workflows will use a combination of both models—o-series for
    agentic planning and decision-making, GPT series for task execution." —
    https://developers.openai.com/api/docs/guides/reasoning-best-practices
  - "`low` - Efficient reasoning with a modest latency increase. Ideal
    for use cases requiring tool-use, planning, search, or multi-step
    decision making" / "`high` - Hard reasoning, complex debugging, deep
    planning, and high-value tasks" (the four-level none/low/medium/high
    reasoning-effort ladder) —
    https://developers.openai.com/api/docs/guides/reasoning
- **Google DeepMind:**
  - "The workhorse model built for cost-efficiency and high-volume
    tasks." (Flash-Lite) —
    https://ai.google.dev/gemini-api/docs/gemini-3
  - "Designed for complex tasks that require broad world knowledge and
    advanced reasoning across modalities." (Pro) —
    https://ai.google.dev/gemini-api/docs/gemini-3
  - "Our best price-performance model for low-latency, high-volume tasks
    requiring reasoning." (Gemini 2.5 Flash) —
    https://ai.google.dev/gemini-api/docs/models
  - "a small model is invoked for most 'easy' instances, while a large
    model is invoked for a few 'hard' instances" (Language Model Cascades
    paper) —
    https://research.google/pubs/language-model-cascades-token-level-uncertainty-and-beyond/
  - Explicitly note: no single unified DeepMind routing-decision-framework
    doc was found across ai.google.dev/blog.google/research.google — the
    per-model blurbs and the cascade paper are the closest primary
    sources; state this as a limitation, not glossed over.
- **DeepSeek** (framed as a **contrast**, not a supporting citation):
  - "The model names `deepseek-chat` and `deepseek-reasoner` will be
    deprecated on 2026/07/24 15:59 UTC. For compatibility, they
    correspond to the non-thinking mode and thinking mode of
    `deepseek-v4-flash`, respectively." —
    https://api-docs.deepseek.com/quick_start/pricing
  - State plainly: DeepSeek does not publish complexity-based
    model-*size* routing guidance comparable to the other three vendors —
    it is collapsing "which model" into a "thinking mode" toggle on one
    model, a different axis (reasoning depth as a runtime toggle) than
    this toolkit's per-task-type model *selection*.

## Requirements

- **R1**: `docs/guides/model-routing.md` gains a new section (placed after
  its existing Anthropic-sourced content) citing OpenAI's model-selection
  and reasoning-effort guidance, each claim with its verbatim quote and
  URL (the three OpenAI URLs in Solution).
- **R2**: Same section (or an adjacent one) cites DeepMind's per-model
  use-case guidance and the cascade-research parallel, with the four
  verbatim quotes and URLs given in Solution (Flash-Lite, Pro, Gemini 2.5
  Flash, and the Language Model Cascades paper), and explicitly notes that
  no single unified DeepMind routing framework doc was found — this is
  stated as a limitation of the citation, not glossed over.
- **R3**: Same section cites DeepSeek, but frames it as a **contrast**:
  quote the `deepseek-v4-flash` thinking/non-thinking-mode migration
  language and state plainly that DeepSeek does not publish
  complexity-based model-size routing guidance comparable to the other
  three vendors.
- **R4**: No change to `runtimes/claude-code.md`'s actual tier→model
  mappings or to the `.claude/runtime.md` override mechanism — this spec
  is documentation-only. If a future session wants to revisit the actual
  tier defaults in light of this research, that is separate follow-up
  work, not this spec's scope.
- **R5**: `docs/guides/model-routing.md` still satisfies the existing
  link-checker gate (`tests/test_doc_links.sh`) — but note explicitly:
  that gate only checks relative in-repo links and mermaid fences; it
  `continue`s past every `http://`/`https://` URL, so it verifies *none*
  of the external citations this spec adds. Passing it confirms this edit
  didn't break unrelated relative links — it is not evidence the new
  URLs resolve or the quotes are verbatim. That verification is manual:
  whoever implements this spec confirms each URL in Solution resolves and
  each quoted string appears on its page (the quotes were already
  verified once, this session, via direct fetch — re-verify at
  implementation time in case a vendor page changed).
- **R6**: The new section is added to `docs/guides/model-routing.md` only
  — no new file, since the guide already exists and already houses this
  exact kind of citation (its current Anthropic-sourced content).
- **R7**: If `specs/idea-research-freshness`'s `Verified: YYYY-MM-DD`
  citation-freshness convention has already shipped by the time this spec
  is implemented (independent sibling spec, no enforced order), the new
  `## Cross-vendor grounding` heading gets a `Verified: <today>` stamp
  directly under it, following that convention. If it hasn't shipped yet,
  skip this — don't block on it.

## Out of scope

- Building any new configurability mechanism — `runtimes/` +
  `.claude/runtime.md` already provide it; this spec only adds citations
  to the existing guide.
- Re-litigating or changing the current default tier→model pins.
- Citing third-party comparison sites (BentoML, DataCamp, etc.) for the
  DeepSeek framing some of them offer ("use R1 for math, V3 for everyday
  tasks") — the research pass flagged that framing as not
  DeepSeek-sourced; this spec only cites primary sources.

## Acceptance criteria

- [ ] `docs/guides/model-routing.md` contains the OpenAI URLs from R1 and
      at least the "accuracy first, then cheapest/fastest" and the
      reasoning-effort-ladder quotes verbatim.
- [ ] It contains the DeepMind URLs from R2, the Flash-Lite/Pro use-case
      quotes, the cascade-paper quote, and an explicit sentence noting no
      unified DeepMind routing-framework doc exists.
- [ ] It contains the DeepSeek `deepseek-v4-flash` thinking-mode quote and
      an explicit sentence stating DeepSeek does not publish
      complexity-based model-size routing guidance.
- [ ] `bash tests/test_doc_links.sh` still passes after the edit (guards
      only against accidentally broken relative links/mermaid fences —
      per R5, this is not the check that verifies the new citations).
- [ ] Manual: each URL in the new section resolves, and each quoted
      string appears on its page (re-verify at implementation time).
- [ ] `runtimes/claude-code.md` and `.claude/runtime.md`'s documented
      override mechanism are byte-for-byte unchanged (confirms R4 — this
      is a docs-only citation addition, not a mechanism change).
- [ ] End-to-end: a human reading `docs/guides/model-routing.md` top to
      bottom now sees Anthropic, OpenAI, DeepMind, and DeepSeek each
      represented, with DeepSeek clearly marked as a contrast rather than
      a supporting citation.

## Open questions

(none)
