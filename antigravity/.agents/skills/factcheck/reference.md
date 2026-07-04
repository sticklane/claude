# /factcheck reference

Contents: Primary-vs-secondary source rubric · The web-worker prompt
template · Clustering sources into workers · Assembling the cited report

Loaded on demand. The SKILL.md body is the checklist; this file holds the
exact worker-prompt template and the full source rubric so they stay out of
the always-loaded body.

## Primary-vs-secondary source rubric

A claim may only be *backed* by a **primary** source. Secondary sources may
orient a worker toward where the answer lives, but can never be the citation
of record — if the primary source can't be found, the claim is `UNVERIFIED`,
never downgraded to a secondary citation.

**Primary (may back a claim):**
- Official vendor / project documentation (e.g. `docs.<product>.com`, the
  product's own reference or API pages).
- Formal specifications and standards (RFCs, W3C/WHATWG specs, language or
  protocol standards, IETF/ISO documents).
- First-party source-of-truth artifacts: the project's own source repo,
  release notes, changelog, or `CHANGELOG`, pricing/limits pages the vendor
  publishes, official first-party engineering blog posts that state the fact
  authoritatively.
- Primary data: the actual dataset, filing, or original document being cited.

**Secondary (orient only — NEVER the basis of a claim):**
- Third-party blogs, tutorials, Medium/dev.to posts, personal sites.
- Community wikis, Stack Overflow answers, Reddit/forum threads.
- Aggregators, listicles, "top 10" roundups, news rewrites of a primary
  source (cite the primary source they quote, not the rewrite).
- Another model's output or the model's own prior knowledge.

Tie-breakers:
- Prefer the most authoritative and most current primary source; if the
  vendor doc and the spec disagree, report both with their URLs rather than
  silently picking one.
- A quote must be **verbatim** and **≤30 words**; if the fact needs more than
  30 words of quotation to support, quote the load-bearing clause and cite the
  section URL for the rest.
- If a primary source exists but is paywalled/unreachable by the worker, mark
  the item `UNVERIFIED` with a note ("primary source at <URL> not reachable"),
  not backed by a secondary substitute.

## The web-worker prompt template

Dispatch one web-capable Agent Manager conversation per independent source
cluster. Fill the bracketed slots; keep every constraint. The tier and the
word cap are stated in the prompt so the worker does not default them silently
(per AGENTS.md "Dispatch authoring").

> **Tier:** run at [session model / medium effort — raise to the session
> model's higher effort only for a cluster whose primary source is dense or
> contested; a pure "read one doc page" cluster can run scout-tier / low
> effort]. **Output budget:** return **≤ [250] words total** — only the
> structured findings below, never the fetched page text or your search
> transcript.
>
> You are a factcheck source-cluster worker. Verify each claim below against
> **primary sources only** — official vendor docs, formal specs/standards, or
> first-party source-of-truth artifacts. Blogs, wikis, forums, aggregators,
> and any model output are **secondary**: you may use them to *find* the
> primary source, but they can NEVER back a claim. Start from these source
> hints: [URLs / doc sites / repos to hit]. Fetch the primary source and read
> the relevant section; do not answer from memory.
>
> Claims to check:
> [numbered list of the atomic claims / questions for this cluster]
>
> For EACH claim return exactly one item:
> - **Claim:** <restated claim>
> - **Verdict:** `VERIFIED` | `REFUTED` | `UNVERIFIED`
> - **URL:** <exact primary-source URL, incl. anchor/section> (omit only if
>   `UNVERIFIED`)
> - **Quote:** "<verbatim excerpt, ≤30 words, copied exactly from that URL>"
>   (omit only if `UNVERIFIED`)
> - **Confidence:** high | medium | low
>
> Rules: Never guess. Never substitute a secondary source to avoid an
> `UNVERIFIED`. If you cannot find a primary source that states the fact, the
> verdict is `UNVERIFIED` and you say briefly why (no primary source found /
> source unreachable / doc is silent). A `REFUTED` verdict still needs a
> verbatim quote + URL from the primary source that contradicts the claim.
> Keep raw pages and search results inside this conversation — return only the
> items above.

## Clustering sources into workers

- One worker per **independent** source cluster (one product's docs, one
  spec, one repo). Open independent clusters in parallel; keep dependent
  claims (claim B only matters if A is true) in the same worker.
- Do not fan out beyond the clusters the question actually spans — a
  single-doc question is one worker, not many. Scale per AGENTS.md "Dispatch
  authoring": 1 worker / 3–10 calls for a lookup, 2–4 workers for a small
  comparison.

## Assembling the cited report

Collect the workers' structured items and emit two distinct sections:

1. **Findings** — the `VERIFIED` / `REFUTED` items, each with its verdict,
   verbatim quote, and URL.
2. **UNVERIFIED** — a separate, explicitly labelled list of every item no
   worker could back with a primary source, each with the one-line reason.
   These are surfaced, never dropped and never quietly answered from a
   secondary source or the model's prior.

Do not edit any downstream doc; return the report and stop (see the SKILL.md
`Next stage:` line).
