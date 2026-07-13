---
name: design
description: Chooses technology and architecture through structured investigation of candidate approaches, judged on agent-buildability, with the decision recorded in the spec and AGENTS.md. Use when a spec leaves a tech or design choice open, or the user asks "which library/framework/approach should I use" or "how should we architect this".
---

Resolve the open design/technology decision. Three principles govern
everything here (see "How they choose tech" in the toolkit repo's
docs/anthropic-playbook.md — not shipped with installs):

- **Stay on distribution.** Prefer technology the model already knows
  deeply — popular, well-documented, boringly mainstream. An exotic choice
  means every future session pays a teaching tax.
- **Do the simple thing first.** Default to the smallest design that meets
  the requirements; add machinery only when a requirement forces it.
- **A decision unrecorded will be re-litigated** by every future agent.
  The output of this skill is a written decision, not a discussion.

## 1. Frame it

State the decision as a question with explicit criteria drawn from the
spec's requirements. Scout the status quo (scout skill): what the codebase
already uses, existing patterns this must fit. The default answer to "what
library should we add?" is **nothing new** — build on what's already there
unless a requirement can't be met that way.

When the decision embeds generative AI in the product, classify each part
of the feature with the code-vs-LLM ladder in [reference.md](reference.md)
BEFORE framing candidates: the lowest rung that meets the requirements is
the default candidate, and any higher-rung candidate must name the failing
per-part test that justifies the escalation.

## 2. Investigate candidates

For a real contest (2–4 viable options), investigate each candidate on the
session model (they weigh trade-offs), scout-tier for pure research — in
parallel Agent Manager conversations if the user wants speed, otherwise
sequentially with the scout discipline. Per candidate report, capped at
~200 words:

- Fit: which spec requirements it satisfies, which it strains.
- On-distribution score: maturity, docs quality, how much prior art exists.
- Integration cost with the current codebase.
- **Verification story: could an agent test this well?** Fast deterministic
  checks, low-noise output, typed APIs score high. This is the tiebreaker
  that matters most for agentic development.
- The simplest version of this option that could work.

Where reading isn't enough, prototype: one git worktree or branch per
candidate on the session model, timeboxed to the spec's riskiest
requirement, throwaway — keep the winner's lessons, not its code. Worth it
only when the decision is expensive to reverse, since each candidate pays
its own full context.

## 3. Decide and record

Pick using: requirements fit first, then verification story, then
on-distribution, then simplicity — for LLM-embedding decisions,
"simplicity" means the lowest rung on the ladder. Present the decision
with the runner-up and the one scenario that would flip it. Then record:

- SPEC.md Solution section: the choice, in one paragraph.
- SPEC.md Open questions: delete the entry this decision resolves —
  /breakdown refuses any spec with unresolved entries there.
- SPEC.md appendix: rejected options and the reason, one line each — and,
  when the ladder applied, the chosen rung per component.
- AGENTS.md: a single line constraining future agents ("Use X for Y; do
  not introduce Z") — only if the decision is repo-wide, and it passes the
  "would removing this cause mistakes?" test.

Next step: `/breakdown specs/<slug>/SPEC.md` (or `/build specs/<slug>/SPEC.md`
for small specs).
