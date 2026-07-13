# prose-review: adopt verified NN/g and Google style-guide doctrine

Status: open
Priority: P2
Breakdown-ready: true

## Problem

A deep-research pass (2026-07-12) adversarially verified technical-writing
best practices against primary, reputable sources — the Google developer
documentation style guide, Nielsen Norman Group's UX-writing research, and
WCAG 2.2 — specifically to find doctrine `/prose-review` could adopt or cite.
25 claims were 3-vote verified; 18 confirmed, 7 refuted. A scout pass against
the skill's current `reference.md` found six of those confirmed findings are
genuinely new (not already covered): an explicit "guidelines not rules"
framing, inverted-pyramid/subheading scoring in the reader test, a named
"Learn More"-style bad example with accessibility framing for vague link
text, an acronym/jargon tension note, and correlational DORA framing. Two
items (the AI-antipattern rubric's promotional-language flags, and the
reader test's existence) are already mostly covered and need only a citation
add, not new rubric behavior.

## Solution

Edit `.claude/skills/prose-review/reference.md` (source line numbers below
are from the pre-edit file; re-locate by heading if drift has occurred):

- **Guidelines-not-rules framing** (new, insert immediately after the
  `## Google-style essentials Vale can't check` heading, before the existing
  `Vale's Google package...` paragraph at `reference.md:119-121`): add a
  short paragraph beginning with the literal sentence "Priority when guides
  conflict: project-specific conventions first, this toolkit's adopted
  Google-style layer second, third-party authorities (Merriam-Webster,
  Chicago Manual, Microsoft Writing Style Guide) third." and stating this
  guidance is departable when it improves content (guidelines, not rules).
  Cite https://developers.google.com/tech-writing/resources (the
  single-house-style-regardless-of-which-conventions principle) — the
  existing `developers.google.com/style` citation at reference.md:121/125
  already covers the guide's own stated hierarchy, so do not re-cite it here.
- **Reader-test extension** (`reference.md:142-167`, currently comprehension
  probes only — what/first-action/stumbles/gaps): add scoring for
  inverted-pyramid structure (does the doc front-load its conclusion?) and
  subheading quality, alongside the existing probes. Cite
  https://www.nngroup.com/articles/how-users-read-on-the-web/ (79% scan vs
  16% read word-by-word).
- **Antipattern rubric citation** (items 5/7/9, `reference.md:56-84`, already
  flagging hyperbole/verbosity/self-celebratory language): add a citation to
  the Morkes & Nielsen finding (concise +58%, objective +27%, combined +124%
  usability) as the evidentiary basis, and make conciseness an explicitly
  *rewarded* property in the item text, not just an anti-flagged one. Cite
  https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/.
  Do not cite the separately-refuted 47%-scannability figure from the same
  source family.
- **Link-text example + accessibility framing** (`reference.md:135-136`,
  currently "descriptive link text — never 'click here' or 'this page'"):
  add "Learn More" as a named bad example, and state that vague link text is
  *also* an accessibility defect (screen readers announce identical repeated
  text with no way to distinguish links). Cite
  https://www.nngroup.com/articles/ux-writing-faqs/.
- **Acronym/jargon checklist item** (new: add as a sixth bullet to the
  `## Google-style essentials Vale can't check` list, `reference.md:127-136`,
  after the existing "Descriptive link text" bullet): introduce a
  first-use-only acronym/jargon-definition convention — prose-review has no
  existing rule on this today, so this bullet establishes it, not merely
  restates it — immediately followed by an explicit "known tension" callout
  citing NN/g's 2026 finding that non-linear scanning means readers often
  miss a first-use definition, so long documents should consider a glossary
  or repeated inline gloss rather than relying on the rubric to catch this.
  Cite https://www.nngroup.com/articles/ux-writing-faqs/.
- **DORA correlational framing** (new: insert a new `## Why this matters`
  section immediately after the existing intro paragraph that ends
  `reference.md:12` ("...never re-fetched at invocation."), before the
  `## The nine-item rubric` heading at `reference.md:14`): one sentence
  noting documentation quality is associated with (not proven to cause)
  ~25% higher team performance per Google/DORA's State of DevOps research,
  explicitly labeled correlational and self-reported. This is the only
  content of the new section — not a rubric item or scoring rule. Cite
  https://dora.dev/capabilities/documentation-quality/.

None of these are new Vale/regex-checkable rules — Vale is already installed
and configured (`vale` binary present, `vale/styles` + `vale/.vale.ini.template`
in repo) and untouched by this spec. All six items stay in the
model-judgment rubric/reference layer, matching prose-review's existing
architecture (Vale pass → rubric pass → reader test, per `SKILL.md`).
Findings from these additions remain advisory, matching the skill's existing
"zero findings is a valid, explicit outcome" behavior (`SKILL.md:64`) — this
spec does not change prose-review from a report to a gate.

## Requirements

- R1: `reference.md` states the guidelines-not-rules framing, including the
  literal sentence "Priority when guides conflict: project-specific
  conventions first, this toolkit's adopted Google-style layer second,
  third-party authorities (Merriam-Webster, Chicago Manual, Microsoft
  Writing Style Guide) third." (verbatim, so it is independently greppable),
  citing developers.google.com/tech-writing/resources.
- R2: The reader-test procedure scores inverted-pyramid structure (conclusion
  front-loaded) and subheading quality, in addition to its existing
  comprehension probes, citing nngroup.com/articles/how-users-read-on-the-web.
- R3: Antipattern rubric items covering hyperbole/verbosity/self-celebratory
  language cite the Morkes & Nielsen concise/objective/combined figures
  (58%/27%/124%) and explicitly reward conciseness, not just flag its absence.
  The refuted 47%-scannability figure is not cited anywhere in the file.
- R4: The "descriptive link text" checklist item names "Learn More" as a bad
  example and states the accessibility rationale (screen readers announce
  duplicate link text), citing nngroup.com/articles/ux-writing-faqs.
- R5: A new sixth bullet in the "Google-style essentials Vale can't check"
  list introduces a first-use-only acronym/jargon-definition convention
  (new doctrine, not a restatement of an existing rule) and records NN/g's
  every-occurrence finding as a caveat for long documents, citing the same
  ux-writing-faqs source.
- R6: A new `## Why this matters` section, placed immediately after
  `reference.md:12` and before the `## The nine-item rubric` heading,
  contains a one-sentence DORA citation, explicitly labeled
  correlational/self-reported, citing dora.dev/capabilities/documentation-quality.
- R7: `SKILL.md`'s gating behavior is unchanged — the read-only report mode
  stays model-invocable, `--fix` stays human-typed only, and zero findings
  stays a valid outcome (no lines in `SKILL.md:20-27` or `SKILL.md:64`
  change in meaning).

## Out of scope

- Retrofitting existing repo docs (README.md, AGENTS.md, docs/*.md) against
  the updated rubric — that is per-doc task work under
  `specs/prose-review/tasks/`, not this doctrine-update spec.
- Any change to Vale configuration, rules, or alert levels.
- Idiomatic-code/TDD doctrine for code-review/simplify/gate — the research
  pass returned zero confirmed claims in that area (Kent Beck, Martin
  Fowler, and engineering-blog sources did not survive verification); this is
  tracked as an open follow-up question, not addressed by this spec.
- Making any new rubric item blocking or gating — all additions stay
  advisory, consistent with prose-review's existing behavior.

## Acceptance criteria

- [ ] `grep -c "developers.google.com/tech-writing" .claude/skills/prose-review/reference.md` → ≥1 (confirmed 0 pre-edit — a new citation, not the already-present style-guide URL); `grep -c "project-specific conventions first" .claude/skills/prose-review/reference.md` → ≥1 (exercises the actual ordering substance, not just the sentence label, confirmed 0 pre-edit) (R1)
- [ ] `grep -c "how-users-read-on-the-web" .claude/skills/prose-review/reference.md` → ≥1, and the reader-test section text includes both "inverted pyramid" (or equivalent front-loaded-conclusion language) and a subheading-quality check (R2)
- [ ] `grep -c "concise-scannable-and-objective" .claude/skills/prose-review/reference.md` → ≥1; `grep -c "47%" .claude/skills/prose-review/reference.md` → 0 (R3)
- [ ] `grep -c "Learn More" .claude/skills/prose-review/reference.md` → ≥1, and the surrounding text states the screen-reader/accessibility rationale (R4)
- [ ] `grep -ci "acronym\|jargon" .claude/skills/prose-review/reference.md` → ≥1, referencing the every-occurrence-vs-first-use tension (R5)
- [ ] `grep -c "dora.dev" .claude/skills/prose-review/reference.md` → ≥1; `grep -c "Why this matters" .claude/skills/prose-review/reference.md` → ≥1 (confirmed 0 pre-edit), and the DORA sentence sits under that new heading and uses "associated with" (or equivalent correlational language), not "causes" (R6)
- [ ] `git diff .claude/skills/prose-review/SKILL.md` shows no changes, or only changes that preserve the existing meaning of lines 20-27 and line 64 (R7)
- [ ] End-to-end: create a scratch file named `README.md` (the reader test
      runs only for orientation docs — README.md/AGENTS.md — by default per
      `reference.md:165`; any other filename skips the reader-test pass and
      this check would not exercise R2) containing a "Learn More" link, a
      promotional/hyperbolic sentence, and a paragraph structure that buries
      its conclusion below unrelated background. Run `/prose-review` (read-only
      report mode) against it — the report flags all three under the updated
      rubric, and the report format is otherwise unchanged.

## Open questions

(none)

## Parallelization

Single task (01) — all six requirements land in one file (`reference.md`)
as one cohesive commit. No concurrent-safe groups; nothing to parallelize.
