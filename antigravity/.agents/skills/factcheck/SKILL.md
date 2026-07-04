---
name: factcheck
description: Closes a known-source factual gap with cited primary sources — dispatches targeted web-capable conversations, each backing every claim with a verbatim quote + URL or marking it UNVERIFIED. Use to verify a claim ("fact-check this", "is it true that…", "cite the source for…", "verify X against the docs") or to look up a known source ("what do the official docs say about…", "get me the primary source for…", "close this factual gap"). NOT for open-ended, multi-source synthesis where the claims are contestable — that stays deep-research.
argument-hint: "[claim or question, optionally with source hints]"
---

Close a known-source factual gap: turn a claim or "what do the docs say about
X" question into a report where every fact carries a verbatim quote + URL, or
is marked UNVERIFIED. The execution contract (obey before anything else):

- **Primary sources only.** A claim may only be backed by a *primary* source:
  official vendor docs, formal specs/standards, or first-party
  source-of-truth artifacts. *Secondary* sources — blogs, wikis, forums,
  aggregators, any LLM output — may point you at the answer but can NEVER be
  the basis of a claim. Full rubric in `reference.md`.
- **Quote-or-UNVERIFIED.** Every reported claim carries a verbatim quote
  (≤30 words) plus the exact source URL, or it is marked `UNVERIFIED`.
- **Never guess, never substitute.** Do not answer from prior knowledge and
  never swap in a secondary source to avoid an `UNVERIFIED` — an honest
  UNVERIFIED beats a confident wrong or weakly-sourced answer.

## 1. Decompose the request into atomic claims

Break the input into atomic, independently-checkable claims/questions. For
each, note the likely primary source (which product's docs, which spec, which
repo) — these groupings become source clusters. If a part has no plausible
published primary source, expect it to land in the UNVERIFIED list; do not
drop it.

## 2. Dispatch one web-capable conversation per source cluster

Each worker must be able to search and fetch the web, so run these as separate
web-capable Agent Manager conversations (not the read-only scout skill). Open
one per **independent** source cluster, in parallel when the clusters don't
depend on each other.

Each worker prompt (exact template in `reference.md`, filled per cluster)
states, so nothing defaults silently:
- an explicit **tier** — session model at medium effort for a dense or
  contested cluster, scout-tier / low effort for a pure single-doc lookup;
- an explicit **output cap** — return **≤250 words**, only the structured
  items, never the fetched page text or search transcript;
- a structured per-item return: **verdict + URL + verbatim quote (≤30 words)
  + confidence**.

Raw fetched pages stay inside the worker conversation; only the cited findings
return to you. Do not fan out beyond the clusters the question spans — a
single-doc question is one worker (see `reference.md` "Clustering sources into
workers"). Tier and cap follow AGENTS.md "Dispatch authoring".

## 3. Assemble the cited report — two distinct sections

Collect the workers' items and emit:

1. **Findings** — the `VERIFIED` / `REFUTED` items, each with its verdict,
   verbatim quote, and exact URL.
2. **UNVERIFIED** — a separate, explicitly labelled list of every claim no
   worker could back with a primary source, each with a one-line reason (no
   primary source found / unreachable / doc silent). These are ALWAYS
   surfaced here, never merged into Findings, never dropped, and never
   quietly answered from a secondary source or the model's prior.

Report the two sections and stop; acting on the findings (editing a research
doc, updating a spec) is the caller's decision, not this skill's.

## Routing note

If the request is open-ended, multi-source synthesis where the claims are
contestable ("survey the landscape of X", "compare all the approaches to Y"),
this is the wrong tool — that is a broad `deep-research` pass. This skill is
for closing a *known-source* gap: the answer already lives in a specific
official doc or spec, and the job is to quote it.

`Next stage: none — the caller merges the cited findings into the relevant
doc (human-launched)`.
