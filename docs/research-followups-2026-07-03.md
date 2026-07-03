# Research follow-ups (2026-07-03) — the unverified legs

Two deep-research runs on 2026-07-03 produced verified reports, but several
threads failed verification (a transient credit-check blip killed 24 verifier
agents mid-burst — credits were actually fine) or never got covered. This file
is the self-contained brief for a fresh session to close them.

## What to do

Run the `deep-research` workflow (ultracode is implied by invoking it) ONCE,
with the combined question below, then merge results:

1. Append a dated "Follow-up findings" section to BOTH
   `docs/context-management-research-2026-07.md` and
   `docs/orchestration-research-2026-07.md` with whatever survives 3-vote
   verification, and rewrite each doc's Caveats to reflect the now-covered
   legs.
2. If findings materially change the designs, amend
   `specs/orchestrator-context/SPEC.md` (context) or
   `specs/ultra-mode/SPEC.md` (orchestration) with a dated amendment note —
   do not restructure them.
3. Commit and push in this repo (conventional message, co-author trailer per
   repo conventions). Mirror nothing — docs only.

## The combined research question (pass as the workflow question/args)

"Close the unverified legs of two prior surveys, as of mid-2026, using primary
sources only:

(A) CONTEXT MANAGEMENT, non-Anthropic vendors: OpenAI (Agents SDK sessions,
trimming/summarization guidance, operator-style long-run checkpointing),
Google/DeepMind (ADK/Gemini context caching, session state, any
clear-vs-compact guidance), Meta/xAI if they publish agent guidance — when to
compact vs clear-and-respawn, external-memory/handoff patterns, orchestrator
checkpointing, cache economics.

(B) CONTEXT MANAGEMENT, Anthropic claims that failed verification last time
(re-verify each against primary sources): server-side compaction positioning
vs the API context-editing feature; the 'Managed Agents' architecture and what
a failed orchestrator does; the warning against irreversible clearing;
combining context editing with the memory tool; Claude Code auto-compact
trigger threshold and /clear guidance; any concrete clear-vs-continue rule of
thumb.

(C) ORCHESTRATION, the DeepMind leg that never verified: Google ADK workflow
agents (SequentialAgent/ParallelAgent/LoopAgent) — where deterministic vs
model-driven control flow sits, verification/judging, budgets, resumability;
whether A2A adds anything for a solo single-machine toolkit.

Deliverable: cited findings per leg + a short 'changes anything?' verdict
against the adopt-lists already recorded in
docs/context-management-research-2026-07.md and
docs/orchestration-research-2026-07.md."
