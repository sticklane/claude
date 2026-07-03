---
name: design
description: Chooses technology and architecture through parallel investigation - concurrent agents explore candidate approaches, judged on agent-buildability, and the decision is recorded in the spec and CLAUDE.md. Use when a spec leaves a tech or design choice open, or the user asks "which library/framework/approach should I use" or "how should we architect this".
argument-hint: "[path/to/SPEC.md or the decision to make]"
---

Resolve the open design/technology decision in $ARGUMENTS. Three principles
govern everything here (see "How they choose tech" in the toolkit repo's
docs/anthropic-playbook.md — not shipped with installs):

- **Stay on distribution.** Prefer technology the model already knows deeply
  — popular, well-documented, boringly mainstream. Anthropic chose Claude
  Code's own stack this way, explicitly so the agent could build the product
  itself. An exotic choice means every future session pays a teaching tax.
- **Do the simple thing first.** Default to the smallest design that meets
  the requirements; add machinery only when a requirement forces it.
- **A decision unrecorded will be re-litigated** by every future agent.
  The output of this skill is a written decision, not a discussion.

## 1. Frame it

State the decision as a question with explicit criteria drawn from the
spec's requirements. Send one `scout` to establish the status quo: what the
codebase already uses, existing patterns this must fit. The default answer
to "what library should we add?" is **nothing new** — build on what's
already in the codebase unless a requirement can't be met that way.

## 2. Investigate candidates in parallel

For a real contest (2–4 viable options), launch one agent per candidate in
parallel (general-purpose, or `Explore` for pure research). Each reports:

- Fit: which spec requirements it satisfies, which it strains.
- On-distribution score: maturity, docs quality, how much prior art exists.
- Integration cost with the current codebase (from the scout's status quo).
- **Verification story: could an agent test this well?** Fast deterministic
  checks, low-noise output, typed APIs score high. This is the tiebreaker
  that matters most for agentic development.
- The simplest version of this option that could work.

For choices where reading isn't enough, prototype instead: one background
agent per candidate with `isolation: worktree`, timeboxed to a small fixed
scope ("make the spec's riskiest requirement work end to end"), each
returning a short report — what worked, what fought back, verification
story. The prototypes are throwaway: keep the winner's lessons, not its
code. Note the cost before launching: each investigator or prototype agent
pays its own full context, so 3 candidates ≈ 3× the tokens of deciding from
a survey — worth it only when the decision is expensive to reverse.

## 3. Decide and record

Pick using: requirements fit first, then verification story, then
on-distribution, then simplicity. Present the decision with the runner-up
and the one scenario that would flip it. Then record:

- SPEC.md Solution section: the choice, in one paragraph.
- SPEC.md Open questions: delete the entry this decision resolves —
  /breakdown refuses any spec with unresolved entries there.
- SPEC.md appendix: rejected options and the reason, one line each.
- CLAUDE.md: a single line constraining future agents ("Use X for Y; do not
  introduce Z") — only if the decision is repo-wide, and it passes the
  "would removing this cause mistakes?" test.

Next step: `/breakdown specs/<slug>/SPEC.md` (or `/build specs/<slug>/SPEC.md`
for small specs).
