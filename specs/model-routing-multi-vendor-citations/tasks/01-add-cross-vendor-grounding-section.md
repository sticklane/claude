# Task 01: Add the Cross-vendor grounding section to model-routing.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R6, R7)
Touch: docs/guides/model-routing.md

## Goal

`docs/guides/model-routing.md` gains a new `## Cross-vendor grounding`
section, inserted immediately before the existing `## Rules and skills this
page explains` heading (currently line 71 — i.e. directly after the page's
Anthropic-sourced content). The section carries the OpenAI, Google DeepMind,
and DeepSeek primary-source citations listed verbatim in the spec's Solution
section, each with its exact quote and page URL, with DeepMind's missing
unified-framework caveat stated as a limitation and DeepSeek framed as a
contrast (not a supporting citation). No mechanism changes: `runtimes/` tier
mappings and the `.claude/runtime.md` override are untouched. This is a
docs-only citation addition to one existing file — no new file.

## Touch

- `docs/guides/model-routing.md` — insert one new `## Cross-vendor grounding`
  section before `## Rules and skills this page explains`. No other file.
- Do NOT touch `runtimes/claude-code.md` or any `runtimes/*.md` mapping, and
  do NOT create `.claude/runtime.md` (R4 — mechanism is out of scope).

## Steps

1. Read the spec's Solution section — it supplies every quote and every URL
   verbatim; this task transcribes them, it does not re-research. Read the
   current tail of `docs/guides/model-routing.md` to confirm the insertion
   point (before `## Rules and skills this page explains`).
2. Insert `## Cross-vendor grounding` immediately before that heading, with
   three labelled subsections:
   - **OpenAI** — the "accuracy first / then cheapest-fastest" pair
     (model-selection URL), the o-series-vs-GPT split quote
     (reasoning-best-practices URL), and the none/low/medium/high
     reasoning-effort ladder quotes (reasoning URL). All three OpenAI URLs
     present, quotes verbatim (R1).
   - **Google DeepMind** — the Flash-Lite, Pro, and Gemini 2.5 Flash
     use-case quotes (their two ai.google.dev URLs), the Language Model
     Cascades paper quote + URL, AND an explicit sentence stating no single
     unified DeepMind routing-framework doc was found — as a limitation, not
     glossed over (R2).
   - **DeepSeek** — framed as a contrast: the `deepseek-v4-flash`
     thinking/non-thinking-mode migration quote + pricing URL, and an
     explicit sentence stating DeepSeek publishes no complexity-based
     model-size routing guidance comparable to the other three (R3).
3. If `specs/idea-research-freshness`'s `Verified: YYYY-MM-DD` convention has
   already shipped, add a `Verified: <today>` stamp directly under the new
   heading; otherwise skip it — do not block on that sibling spec (R7).
4. Run `bash tests/test_doc_links.sh` — confirm it still passes (guards
   relative links + mermaid fences only; it does NOT verify the external
   URLs, per R5).
5. Mark the manual URL-resolution / verbatim-quote criterion manual-pending
   with a note — an unattended worker cannot fetch external pages to confirm
   each quote appears verbatim; a human re-verifies post-merge (R5).

## Acceptance

- [ ] `grep -Fq 'developers.openai.com/api/docs/guides/model-selection' docs/guides/model-routing.md && grep -Fq 'developers.openai.com/api/docs/guides/reasoning-best-practices' docs/guides/model-routing.md && grep -Fq 'developers.openai.com/api/docs/guides/reasoning' docs/guides/model-routing.md` → all three OpenAI URLs present (exit 0).
- [ ] `grep -Fq 'Optimize for accuracy until you hit your accuracy target' docs/guides/model-routing.md` → the accuracy-first quote is present verbatim (exit 0).
- [ ] `grep -Fq 'ai.google.dev/gemini-api/docs/gemini-3' docs/guides/model-routing.md && grep -Fq 'ai.google.dev/gemini-api/docs/models' docs/guides/model-routing.md && grep -Fq 'research.google/pubs/language-model-cascades-token-level-uncertainty-and-beyond' docs/guides/model-routing.md` → DeepMind + cascade-paper URLs present (exit 0).
- [ ] `grep -Fiq 'no single unified' docs/guides/model-routing.md || grep -Fiq 'no unified' docs/guides/model-routing.md` → the DeepMind unified-framework limitation sentence is present (exit 0).
- [ ] `grep -Fq 'api-docs.deepseek.com/quick_start/pricing' docs/guides/model-routing.md && grep -Fq 'deepseek-v4-flash' docs/guides/model-routing.md` → DeepSeek contrast citation present (exit 0).
- [ ] `grep -q '^## Cross-vendor grounding' docs/guides/model-routing.md` → the new section heading exists (exit 0).
- [ ] `git diff --quiet HEAD -- runtimes/claude-code.md` → exit 0 (runtimes mapping unchanged, R4).
- [ ] `bash tests/test_doc_links.sh` → exits 0 (relative links + mermaid fences intact after the edit).
- [ ] Manual-pending (human, post-merge, R5/AC5): each new URL resolves and each quoted string appears verbatim on its page — unattended workers cannot fetch external pages to self-verify.
