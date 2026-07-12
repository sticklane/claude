# /prose-review reference

Contents: The nine-item rubric (with vendor quotes · item-1 carve-out ·
DeepMind note) · Diátaxis — structure by what the reader needs RIGHT NOW
(quadrant table bound to house doc locations) · Google-style essentials Vale
can't check · The reader test (distilled).

Loaded on demand — the SKILL.md body names the passes; this file carries the
doctrine each pass applies. The rubric and style bindings are stable,
verified content (like /simplify's fixed checklist), not live research: the
vendor sources below were verified 2026-07-11 and are revisited only on a
human call, never re-fetched at invocation.

## The nine-item rubric

Each item names the vendor(s) whose own published guidance backs it and the
verified quote. A finding cites its item number, the offending excerpt, a
one-line reason, and a suggested rewrite (SKILL.md's report shape).

1. **List/bullet overuse where prose reads better.** Narrative or
   explanatory content fragmented into bullets where flowing paragraphs
   would read better.
   - Anthropic: "DO NOT use ordered lists ... unless ... discrete items" —
     write "flowing prose using complete paragraphs". (platform.claude.com/docs)
   - OpenAI: prefer "plain paragraphs as the default format".
     (model-spec.openai.com)
   - Amazon: narrative, non-bulleted writing is core culture — "we don't do
     PowerPoint ... narratively structured six-page memos".
   - **Carve-out (does NOT fire on structured technical documents).** A
     spec's `## Requirements` / `## Acceptance criteria` sections, API
     references, config-key tables, or any list whose items are genuinely
     discrete and enumerable are NOT "list overuse". Item 1 targets
     narrative/explanatory prose broken into bullets where paragraphs would
     read better — per Anthropic's own carve-out, "unless ... you're
     presenting truly discrete items". When unsure whether a list is
     narrative-fragmented or genuinely enumerable, do not flag it: a
     misjudged carve-out that rewrites structured spec content into prose is
     the real damage this exclusion prevents.

2. **Excessive hedging / disclaimers / AI-reminders.** Qualifier pileups,
   defensive caveats, and reminders that the author is an AI.
   - OpenAI: avoid "excessive hedging ... disclaimers ... reminders that
     it's an AI". (model-spec.openai.com)

3. **Sycophancy.** Flattery, reflexive agreement, praising the reader or the
   subject instead of informing.
   - Anthropic: sycophancy is a named, measured problem. (platform.claude.com/docs)
   - OpenAI: "not ... flatter them or agree with them all the time".
     (model-spec.openai.com)

4. **Over-formatting.** Bold, headers, and lists beyond what genuinely aids
   scanning — decoration that fragments reading rather than guiding it.
   - Anthropic: "avoids over-formatting with bold emphasis, headers, lists".
     (platform.claude.com/docs)

5. **Purple prose / clichéd filler.** Hyperbole, self-aggrandizing phrasing,
   and stock clichés in place of plain statement.
   - OpenAI: avoid "purple prose, hyperbole, self-aggrandizing, and clichéd
     phrases". (model-spec.openai.com)

6. **Stock acknowledgments.** Conversational filler openers that carry no
   information.
   - OpenAI: avoid "stock acknowledgments like 'Got it'".
     (model-spec.openai.com)

7. **Repetitive phrasing / redundant information.** The same idea or wording
   restated; length growing without added content.
   - DeepSeek: repetition and language-mixing are named, documented failure
     modes of raw model output (DeepSeek-R1 README/paper), addressed via
     explicit reward-shaping for readability.
   - Mistral: `frequency_penalty` / `presence_penalty` exist specifically to
     reduce repetition.
   - Amazon: "verbosity hacking" (length exploding without quality) is a
     named failure mode in their RFT best-practices guidance.

8. **Vague / blurry language.** Placeholder words where a concrete specific
   belongs.
   - Mistral: "avoid blurry words like 'things', 'stuff' ... state exactly
     what you mean".

9. **Self-celebratory language.** Progress narrated as achievement rather
   than reported as fact.
   - Anthropic: "fact-based progress reports rather than self-celebratory
     updates". (platform.claude.com/docs)

**DeepMind contributes no rubric item.** Its published material names no
specific prose antipattern — only Workspace style-*matching* features and
generic prompt-clarity advice. It is recorded here as contributing nothing
rather than silently omitted or padded with an invented item, so a later
reader knows the vendor was checked, not skipped.

## Diátaxis — structure by what the reader needs RIGHT NOW

Diátaxis (diataxis.fr) splits documentation into four modes; mixing them —
explanation folded into reference, a tutorial that detours into design
rationale — makes each worse. That failure mode is exactly the house one, so
the structural question a review or an authoring pass asks first is:

**What does the reader need RIGHT NOW?** The answer picks the quadrant:

| Reader needs right now | Quadrant | House doc location |
| --- | --- | --- |
| To learn by doing, guided step by step | Tutorial | rare here; a getting-started walkthrough in README.md or docs/ |
| To accomplish a specific goal they already have | How-to | README.md (human tasks), SKILL.md bodies (agent tasks) |
| To look up facts — a map, an API, an option list | Reference | AGENTS.md (orientation map), docs/ reference pages, SKILL.md bodies |
| To understand why — context, rationale, trade-offs | Explanation | README.md (for humans), docs/*.md |

So: README.md = explanation + how-to for humans; AGENTS.md =
reference/orientation map; docs/ = explanation and reference; SKILL.md bodies
= how-to/reference for agents. When a section serves two of these at once,
that is the split the review flags — separate the reference table from the
explanation prose rather than interleaving them.

The Diátaxis grid (diataxis.fr) crosses two axes — acquisition vs.
application, study vs. work — but the RIGHT-NOW question above is the fast
selector for the common case; consult the grid only when a doc genuinely
straddles two modes.

## Google-style essentials Vale can't check

Vale's Google package (developers.google.com/style, run first when
installed) catches sentence-level mechanics — passive voice, second person,
tense, wordy phrases, heading case. It cannot judge structure or fit, so the
rubric pass owns these, all sourced to the Google Developer Documentation
Style Guide (developers.google.com/style):

- **Audience-first ordering.** Lead with what the reader needs first, not
  with background or history. The most important thing goes at the top.
- **One idea per paragraph.** A paragraph carrying two ideas is two
  paragraphs; a paragraph carrying none is filler.
- **Conditions before instructions.** "To do X, click Y" and "If X, do Y" —
  the reader learns whether a step applies before reading how to do it.
- **Concrete over abstract.** Prefer a real example to a general
  description; show the command, the path, the value.
- **Descriptive link text.** Link the thing being referred to, never "click
  here" or "this page".

Vale absent does not stop these — they are judgment checks the rubric pass
runs regardless; the review notes only that the deterministic Vale pass was
skipped.

## The reader test (distilled)

Distilled from Anthropic's `doc-coauthoring` skill (github.com/anthropics/skills)
— the procedure, not the plugin, so no per-session token load. It probes
comprehension, which neither Vale nor the rubric can: a document can pass
every sentence-level and antipattern check and still leave a fresh reader
lost.

Procedure: open ONE fresh Agent Manager conversation (session tier, no prior
context — it must read cold, exactly as a first-time reader would; per
AGENTS.md Dispatch authoring — awaited, capped return). Give it only the
target document. It reads once and answers, in a capped report:

- **What is this?** — can it say, in one sentence, what the doc is for?
- **What would I do first?** — is the first action obvious?
- **Where did I stumble?** — every point it had to re-read, guess, or look
  elsewhere to follow.
- **What question is left unanswered?** — the gap it noticed but the doc
  never closes.

The stumble report merges into the review findings (each stumble ranked with
the rubric/Vale findings by how badly it blocks the reader). Review mode runs
the reader test for orientation docs (README.md, AGENTS.md) by default and
skips it for diffs and pasted text — a fragment has no cold-read context to
test.
