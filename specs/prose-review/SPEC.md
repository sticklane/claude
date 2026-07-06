# /prose-review: check writing style for AI-writing antipatterns

## Problem

No skill in this toolkit reviews prose quality. `/code-review` and
`/simplify` are code-only; `/critique` is adversarial review of a spec's
*content* (gaps, ambiguity, missing requirements), not its *style* — a
scout confirmed no sibling exists and grep for "writing style"/"prose"/
"antipattern" across `.claude/` turns up nothing on-topic. Six vendors'
own published guidance, verified this session, converges on a checkable
rubric of AI-writing antipatterns:
- **Anthropic**: avoid list/bullet overuse ("DO NOT use ordered lists...
  unless... discrete items" — write "flowing prose using complete
  paragraphs"), avoid over-formatting ("avoids over-formatting with bold
  emphasis, headers, lists"), avoid self-celebratory language ("fact-based
  progress reports rather than self-celebratory updates"), sycophancy is
  a named, measured problem. (platform.claude.com/docs)
- **OpenAI** (Model Spec, model-spec.openai.com): avoid "purple prose,
  hyperbole, self-aggrandizing, and clichéd phrases"; avoid "excessive
  hedging... disclaimers... reminders that it's an AI"; avoid sycophancy
  ("not... flatter them or agree with them all the time"); prefer "plain
  paragraphs as the default format"; avoid "stock acknowledgments like
  'Got it'".
- **DeepSeek**: repetition and language-mixing are named, documented
  failure modes of raw model output (DeepSeek-R1 README/paper), addressed
  via explicit reward-shaping for readability.
- **Amazon**: narrative, non-bulleted writing is core culture ("we don't
  do PowerPoint... narratively structured six-page memos"); "verbosity
  hacking" (length exploding without quality) is a named failure mode in
  their own RFT best-practices post.
- **Mistral**: avoid vague/blurry language ("avoid blurry words like
  'things', 'stuff'... state exactly what you mean"); `frequency_penalty`/
  `presence_penalty` exist specifically to reduce repetition.
- **DeepMind**: no primary source names specific antipatterns (only
  Workspace style-*matching* features and generic prompt-clarity advice)
  — contributes no rubric items, noted honestly rather than padded.

## Solution

A new skill, `/prose-review`, reviewing a target (a file path, a diff, or
pasted text) against a **fixed, cited rubric** written directly into the
skill's own doctrine (`.claude/skills/prose-review/reference.md`) — no
research is dispatched at invocation time; the rubric is stable content,
verified once, not re-derived per run (unlike `/domain-knowledge`'s
live-research design, this is closer to `/simplify`'s fixed-checklist
shape). It reports findings ranked by severity, each citing which rubric
item it violates, with a suggested rewrite — matching `/code-review`'s
reporting shape (`ReportFindings`-style) but for prose instead of code.

## Requirements

- **R1**: `.claude/skills/prose-review/reference.md` documents exactly
  these nine rubric items, each with its source vendor(s) and the
  verified quote backing it (from Problem): (1) list/bullet overuse where
  prose reads better, (2) excessive hedging/disclaimers/AI-reminders,
  (3) sycophancy, (4) over-formatting (bold/headers beyond what aids
  scanning), (5) purple prose/clichéd filler, (6) stock acknowledgments,
  (7) repetitive phrasing/redundant information, (8) vague/blurry language
  lacking concrete specifics, (9) self-celebratory language. DeepMind is
  noted as contributing no rubric item, not silently omitted. **Rubric
  item 1 explicitly excludes structured technical documents** — a spec's
  `## Requirements`/`## Acceptance criteria` sections, API references, or
  any list whose items are genuinely discrete/enumerable (this repo's own
  `specs/*/SPEC.md` files are the concrete example) are not "list
  overuse"; item 1 targets narrative/explanatory prose being fragmented
  into bullets where flowing paragraphs would read better, per the exact
  carve-out Anthropic's own guidance already states ("unless... you're
  presenting truly discrete items").
- **R2**: `.claude/skills/prose-review/SKILL.md` takes a target (file
  path / diff / pasted text) and checks it against all nine items,
  reporting findings ranked by severity — file:line (or quoted excerpt for
  pasted text), which rubric item, a one-line reason, and a suggested
  rewrite. Zero findings is a valid, explicitly reported outcome ("no
  antipatterns found"), not silence.
- **R3**: `/prose-review` is read-only by default (report only) — this is
  its only model-invocable behavior. An optional `--fix` flag applies the
  suggested rewrites to the target file directly; `--fix` requires a file
  path target specifically — given a diff or pasted-text target, `--fix`
  errors rather than guessing where to write output. (Note: earlier
  drafts of this spec claimed `--fix` "matches `/code-review`'s existing
  `--fix` convention" — that claim doesn't hold up: `/code-review` is a
  harness/plugin built-in with no on-disk SKILL.md, invoked with a tier
  arg like `low`, not option flags, per `build/SKILL.md:86`; `--fix`'s
  design here stands on its own, not on an unverifiable parity claim.)
- **R4**: The **default, read-only report mode** is model-invocable (no
  `disable-model-invocation`) — same risk class as `/critique`/
  `/simplify`. **`--fix` is human-invoked only** (the flag must be typed
  explicitly by a human in the same message that invokes the skill,
  never inferred/added automatically by the model from a vague request)
  — this is a `SKILL.md` behavioral instruction, not a runtime guard (a
  flag can't distinguish human-typed from model-typed arguments at
  invocation time); enforcement is the same "the model doesn't self-grant
  the mutating path" discipline `disable-model-invocation` skills rely
  on elsewhere in this repo, applied here as an instruction rather than a
  frontmatter flag since the read-only mode must stay model-invocable.
  Auto-rewriting a file based on a 9-item subjective rubric is real
  mutation risk (a false positive on item 1 could damage exactly the kind
  of structured spec content R1 carves out, if that carve-out is ever
  misjudged), and this repo's own convention reserves autonomous mutation
  for stages with much stronger gates than a style rubric provides.
- **R5**: Per CLAUDE.md's mirroring convention,
  `antigravity/.agents/skills/prose-review/` is created in the same
  commit with equivalent content (a plain review skill, no
  Claude-Code-specific mechanism, ports cleanly).
- **R6**: `.claude-plugin/plugin.json`'s `version` is bumped (new skill).

## Out of scope

- Auto-triggering `/prose-review` from within `/build`'s or `/idea`'s own
  flow — this spec adds a standalone, explicitly-invoked skill only; wiring
  it into another skill's completion step is separate follow-up work.
- Re-researching the rubric at invocation time, or keeping it "fresh" via
  `idea-research-freshness`'s `Verified:` convention — the rubric is
  vendor style-doctrine, not a fast-moving fact set; revisiting it is a
  human call, not an automated staleness check.
- Reviewing code comments or docstrings as a distinct target type — this
  spec scopes to prose documents/specs/PR-description-shaped text; code
  itself stays `/code-review`'s job.
- Adding a tenth rubric item from a source not verified this session
  (e.g. third-party "AI writing tells" listicles) — R1's nine items are
  exactly what verified primary-source quotes support.

## Acceptance criteria

Fixtures live under a new
`.claude/skills/prose-review/test-fixtures/` directory, created as part
of this spec's implementation with exactly this pinned content (not left
for the verifying agent to invent):

- `bullet-overuse.md`: a narrative explanation of a product feature (not
  a spec/Requirements-shaped document) broken into 5+ single-sentence
  bullets where the same content reads naturally as 2-3 prose sentences,
  and containing no hedging/sycophancy/repetition/vague language.
- `hedging.md`: three sentences using "there's no one-size-fits-all
  solution," "I should note that," and "as an AI, I don't have personal
  opinions, but," with no bullets and no other antipatterns.
- `clean.md`: direct, concrete, plain-paragraph prose (e.g. a factual
  changelog entry) with none of the nine items present.
- `structured-spec.md`: a copy of this repo's own `## Requirements`
  section style (numbered `- **R1**:` bullets) — used to prove R1's
  carve-out.

- [ ] `.claude/skills/prose-review/reference.md` documents all nine
      rubric items with their source vendor(s) and verified quote.
- [ ] `/prose-review test-fixtures/bullet-overuse.md` reports a finding
      tagged rubric item 1, and no finding tagged items 2-9.
- [ ] `/prose-review test-fixtures/hedging.md` reports a finding tagged
      rubric item 2, and no finding tagged item 1.
- [ ] `/prose-review test-fixtures/clean.md` reports "no antipatterns
      found" explicitly — zero findings, not a silent empty response.
- [ ] `/prose-review test-fixtures/structured-spec.md` reports **no**
      finding tagged rubric item 1 (proves R1's structured-document
      carve-out holds).
- [ ] `/prose-review --fix test-fixtures/bullet-overuse.md` (typed
      explicitly, per R4) rewrites that file in place to flowing prose;
      `/prose-review test-fixtures/bullet-overuse.md` (no `--fix`) leaves
      it unchanged, printing findings only.
- [ ] `/prose-review --fix` given a diff or pasted-text target (not a
      file path) errors per R3, rather than silently no-op'ing or
      guessing a write target.
- [ ] `antigravity/.agents/skills/prose-review/` exists with equivalent
      content (R5).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change (R6).

## Open questions

(none)
