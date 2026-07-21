# Agentic-register writing tells: cross-runtime prose doctrine

Status: open
Priority: P2
Breakdown-ready: true

## Problem

An empirical pass over this operator's own Claude Code output — 519 local
sessions, 717,369 words of assistant prose (visible output only; stored
thinking is redacted to signatures) — surfaced writing tics that the
`/prose-review` nine-item rubric does not name, that live in a register the
rubric's charter does not reach, and that are documented as **general
RLHF-trained-assistant behaviors** — not Claude-specific — so they must be
governed equally across every runtime this toolkit ports to
(`.claude/` → `antigravity/` → `codex/`). The measured tics (operator's
Claude corpus; illustrative of the general pattern, not a per-runtime figure):

- **Meta-discourse (announce-then-do process narration).** `let me` opens
  more sentences than any other phrase — as `let me check`, `let me read`,
  `let me verify` — with `now`-fronted sequencing (`now let me`, `now
  running`) close behind. This is the measured instance of a broader
  antipattern: spending a clause on what the answer is *about to* do, or its
  own structure, instead of the substance. The reader already watches the
  action fire.
- **False precision on knowable quantities.** `~<digit>` is the dominant
  hedge, far above `roughly`, plus the empty-comparator family `well
  under`/`well over`/`well past`. The number is usually in hand (a diff line
  count, a runner's test count, two measured timings), so the tilde
  manufactures fuzz over a fact.
- **Evaluative varnish substituting for the checkable fact.** `clean(ly)?` is
  the most frequent evaluative adjective by a wide margin; discounting the
  literal cleanup verb and the verifiable `whitelist clean` token leaves a
  large residual of quality-assertions ("landed clean", "clean merge") that
  name no fact. Siblings: `solid`, `robust`, `holistic`; `genuinely` and
  salience labels (`notably`, `clearly`) inflate the same way.

The rubric's items 2/5/8/9 name adjacent behaviors, not these three (the
boundaries are drawn in R1). More important, `/prose-review`'s charter is
human-facing docs (README/AGENTS/docs), while these tics dominate
**agent-authored user-facing status and reports** (drain/build progress) — a
register no doctrine in this repo currently governs, on any runtime.

**Cross-runtime gap (the reason this spec exists as written).** The prose
doctrine surfaces are not uniformly ported. `prose-review` reaches all three
runtimes — Antigravity holds the real `reference.md`, Codex symlinks to it —
so a rubric addition mirrored once covers all three. But CLAUDE.md's
`## Authoring conventions` and `.claude/rules/` are **Claude-only**;
`antigravity/AGENTS.md` re-expresses their spirit under its own headings (no
authoring-conventions section), and `codex/AGENTS.md` defers to Antigravity
**only for "shared pipeline orientation," which an author-side prose
convention is not**. So an author-side principle added only to CLAUDE.md
would bind Claude agents and silently skip Antigravity/Gemini and Codex/GPT
agents — the exact non-uniformity this spec must close, and the reason each
runtime's home is named explicitly in R3/R4.

## Solution

Land the doctrine in every runtime, in two forms:

1. **Reviewer + on-demand-authoring doctrine (all runtimes via the mirror).**
   A new "Agentic-register tells" `##` subsection in
   `.claude/skills/prose-review/reference.md`, after the nine-item rubric —
   three **runtime-neutral** tells (no operator-specific counts in the
   shipped doctrine) in the rubric's own citation+rewrite shape, each with an
   explicit boundary against the existing rubric items it neighbors, plus a
   **status-telegraphy carve-out** parallel to the existing item-1 carve-out.
   Mirrored verbatim-equivalent into
   `antigravity/.agents/skills/prose-review/reference.md` (Codex inherits via
   its symlink), with a parity-manifest data line so the gate enforces it.
2. **Always-loaded author-side principle (each runtime's conventions doc).**
   The short principle — *lead with the result, not narrated intent; replace
   a quality adjective with the checkable fact; state a known number rather
   than a `~` approximation; but never suppress a terse factual status line* —
   added to `CLAUDE.md`'s `## Authoring conventions`, to `antigravity/AGENTS.md`
   (in its own register), and made explicitly in-scope for `codex/AGENTS.md`
   (which currently defers to Antigravity only for pipeline orientation, so
   its deferral clause is widened to name output/authoring conventions, or the
   principle is stated inline). Each cites reference.md's subsection for
   detail. The canonical literal is `lead with the result, not narrated
   intent` — used verbatim everywhere it is required or checked.

No new always-on `.claude/rules/*.md` file (standing cached-prefix cost; folds
into existing conventions docs). `.claude-plugin/plugin.json` `version` bumps
0.9.29 → 0.9.30 since skill behavior changes.

## Research grounding

Sources verified 2026-07-21 (revisit only on human call, per reference.md's
stability convention). The tells are empirically measured on RLHF assistants
generally — much of the evidence is on GPT — so they apply at least as
strongly to Antigravity/Gemini and Codex/GPT as to Claude.

- **Excess-vocabulary / varnish adjectives (measured on GPT).** Liang et al.,
  "Monitoring AI-Modified Content at Scale" (ICML 2024, arXiv:2403.07183):
  adjectives are the most discriminative POS; `meticulous` shows a 34.7x
  fold-increase, and the Top-100 AI-overused adjective table includes
  `robust`, `seamless`, `comprehensive`, `holistic`. Kobak et al., "Delving
  into LLM-assisted writing…" (arXiv:2406.07016): style words dominate excess
  vocabulary; `crucial`/`notably` are among the largest absolute gaps.
  Grounds tell T3 and the intensifier note — and is why the non-Claude ports
  need it.
- **False precision / confident guessing.** Kalai et al. (OpenAI), "Why
  Language Models Hallucinate" (arXiv:2509.04664): eval incentives reward
  confident specificity over calibrated abstention. "Revisiting Epistemic
  Markers…" (arXiv:2505.24778): a model's `likely`/`~` is a learned surface
  phrase that does not track its actual confidence. Grounds tell T2.
- **Process narration / verbosity.** Singhal et al., "A Long Way to Go:
  Investigating Length Correlations in RLHF" (arXiv:2310.03716): reward models
  conflate length with quality — a purely length-based reward reproduces most
  RLHF gains, so an unearned preamble is exactly the kind of length RLHF
  rewards. Grounds tell T1. (The CoT-faithfulness literature is NOT cited for
  T1: it concerns hidden-reasoning fidelity, not user-facing action
  preambles.)
- **Sycophancy (rubric item 3, reinforced).** Sharma et al. (arXiv:2310.13548).
- **Scoping caution (informs Out of scope).** Wikipedia "Signs of AI writing"
  and the 2025 em-dash discourse (Washington Post, Apr 2025): tells are
  model-specific with dialect false-positives (the "delve" backlash). Claude
  is measured as the *lightest* em-dash user among major models — so the
  operator's dense em-dash use is settled house style. This carve-out is
  Claude-scoped and must NOT be ported: other models over-produce em-dashes,
  but banning punctuation is still rejected everywhere per the false-positive
  caution.

## Requirements

- **R1**: `.claude/skills/prose-review/reference.md` gains a `##`
  "Agentic-register tells" subsection (after the nine-item rubric)
  documenting exactly three runtime-neutral tells, each with: a name, a
  one-line description, at least one cited research source from Research
  grounding, a before→after suggested rewrite in the rubric's report shape,
  and a one-line boundary against the rubric item it is closest to. The three:
  - **T1 meta-discourse (announce-then-do process narration)** — talking
    about the response or the work instead of delivering it: narrating intent
    before a visible action ("let me…", "now I'll…"), or commenting on the
    answer's own structure. Distinct from item 6 (stock acknowledgments) in
    that it previews *work*, not pleasantries. Its code-comment analogue —
    inline comments that narrate what the code does — is a separate code-doctrine
    follow-up, not in this prose spec's scope.
  - **T2 false precision on knowable quantities** — `~`/`well under` on a
    value that is in hand; distinct from item 2 (hedging/disclaimers) in that
    it reads *more* precise than warranted, not less committal.
  - **T3 evaluative varnish substituting for the checkable fact** — a quality
    adjective used *in place of* the fact it summarizes ("landed clean" with
    no stated conflict/gate status); explicitly bounded against item 5 (purple
    prose = hyperbole/cliché) and item 9 (progress narrated as achievement) —
    T3 is specifically the *cash-out failure*, an adjective where a checkable
    fact belonged.
  The subsection states the tells apply to any RLHF-trained assistant, carries
  no operator-specific raw counts, and (if any count is cited) labels it as
  measured on one operator's Claude corpus, illustrative of the general
  pattern.
- **R2**: The same subsection carries a status-telegraphy carve-out, modeled
  on the item-1 carve-out and naming it as the model, drawing the boundary
  precisely: a terse line that **states verifiable state** ("gates green",
  "merged and pushed", "waiting on task 09") is exempt; a line where an
  **adjective substitutes for that state** ("landed clean" alone) is a T3 hit,
  not exempt — the two are complementary, not overlapping. It includes one
  concrete exempt example and one concrete T3-hit example on that boundary,
  and carries the same "when unsure, do not flag" guard.
- **R3**: The author-side principle is added to CLAUDE.md's
  `## Authoring conventions` as one bullet — the canonical literal `lead with
  the result, not narrated intent` plus "replace a quality adjective with the
  checkable fact; state a known number rather than a `~` approximation" —
  extending the writing charter to agent-authored user-facing status/reports,
  carrying the status-telegraphy carve-out as a trailing clause (so an agent
  with only conventions loaded does not over-suppress telegraphy), and citing
  reference.md's subsection for detail rather than restating it.
- **R4 (non-Claude parity — the equal-application requirement)**: The same
  principle, with the same canonical literal and trailing carve-out clause, is
  added to `antigravity/AGENTS.md` in its own register (agent output in
  Antigravity's workflow / Agent-Manager conversations), under the most
  fitting existing heading, citing the reference.md subsection via an
  antigravity-valid or runtime-neutral path (never a `.claude/` path). Because
  `codex/AGENTS.md`'s deferral to Antigravity is scoped to pipeline
  orientation and does NOT cover authoring conventions, `codex/AGENTS.md` is
  edited too: either its deferral clause is widened to explicitly name
  output/authoring conventions as also inherited from `antigravity/AGENTS.md`,
  or the principle is stated inline. No runtime is left unbound.
- **R5 (mirror + gate)**: The reference.md subsection is mirrored
  verbatim-equivalent into
  `antigravity/.agents/skills/prose-review/reference.md` (all three tell names
  and the carve-out present there, not just the heading); a real
  (non-comment) `<source>|<mirror>|<phrase>` data line seeding the phrase
  `Agentic-register tells` is added to `tests/mirror-procedure-manifest.txt`;
  and `bash tests/test_mirror_procedure_coverage.sh` passes. The Codex symlink
  `codex/.agents/skills/prose-review/reference.md` is confirmed to resolve to
  the updated content (no Codex skill edit — it is a symlink). A closure
  cross-reference check (mirror-verification rule) confirms the mirrored
  subsection's citation path resolves under Antigravity.
  `.claude-plugin/plugin.json` `version` is bumped to exactly `0.9.30`.
- **R6 (size + Touch discipline)**: reference.md's table-of-contents block
  (file >100 lines) names the new subsection; SKILL.md is untouched and stays
  <500 lines. The implementing task's `Touch:` header carries every mutated
  path: `.claude/skills/prose-review/reference.md`,
  `antigravity/.agents/skills/prose-review/reference.md`,
  `tests/mirror-procedure-manifest.txt`, `CLAUDE.md`, `antigravity/AGENTS.md`,
  `codex/AGENTS.md`, `.claude-plugin/plugin.json`.

## Out of scope

- **A full parity migration of `.claude/rules/` and CLAUDE.md conventions to
  the non-Claude runtimes.** The scout found the rules are Claude-only and
  `antigravity/AGENTS.md` only absorbs their spirit selectively — a genuine
  systemic gap, but a much larger effort than this writing doctrine. This spec
  makes ITS doctrine cross-runtime (R4); the broader rules-parity question is
  surfaced to the human as a possible follow-up spec, not folded in here.
- **Reducing or banning the em-dash.** Claude-scoped house style; not ported;
  no rule/Vale/rubric item targets it on any runtime.
- **Banning generic "AI vocabulary" (delve/meticulous/moreover).** Documented
  dialect false-positives; Vale's Google package already flags wordiness. The
  three tells target *constructions and cash-out failures*, not a word
  blocklist.
- **Custom Vale styles.** Vale runs file-only; these tics live in the
  response/status register, not in docs, so a Vale rule would not reach them.
- **Reworking the existing nine-item rubric or its vendor sourcing.** The new
  tells are additive and separately sourced; items 1–9 are untouched.

## Acceptance criteria

Extraction helper used below: `SUB` = the subsection body,
`awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' <reference.md>`.

- [ ] `grep -q '^## Agentic-register tells' .claude/skills/prose-review/reference.md` (R1)
- [ ] `test $(awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -Eio 'meta-discourse|false precision on knowable|evaluative varnish' | sort -u | wc -l) -eq 3` — three distinct tell names (R1)
- [ ] `SUB=$(awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md); test $(printf '%s' "$SUB" | grep -Eic 'arxiv|liang|kobak|singhal|kalai') -ge 3 && test $(printf '%s' "$SUB" | grep -c 'Before' ) -ge 3` — each tell cited and each has a before→after (R1)
- [ ] `awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -qi 'RLHF-trained assistant'` and `! awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -Eq '717,369|519 (local )?sessions'` — runtime-neutral, no operator counts as doctrine (R1)
- [ ] `awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -qi 'status-telegraphy carve-out'` and the same block matches `item-1` and both `gates green` (exempt example) and a T3-hit example (R2)
- [ ] `grep -c 'lead with the result, not narrated intent' CLAUDE.md` = 1, and the surrounding bullet matches both `reference.md` and a status-carve-out clause (R3)
- [ ] `grep -c 'lead with the result, not narrated intent' antigravity/AGENTS.md` = 1, citing the reference.md subsection with no `.claude/` path (R4)
- [ ] `grep -Eqi 'authoring convention|output convention|lead with the result, not narrated intent' codex/AGENTS.md` — Codex is bound, not silently skipped (R4)
- [ ] `grep -Eq '^[^#].*\|Agentic-register tells' tests/mirror-procedure-manifest.txt` — real (non-comment) manifest data line (R5)
- [ ] `bash tests/test_mirror_procedure_coverage.sh` exits 0 (R5)
- [ ] `test $(awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' antigravity/.agents/skills/prose-review/reference.md | grep -Eio 'meta-discourse|false precision on knowable|evaluative varnish' | sort -u | wc -l) -eq 3` — mirror carries the full subsection, not just the heading (R5)
- [ ] `grep -q '^## Agentic-register tells' codex/.agents/skills/prose-review/reference.md` — Codex symlink resolves to updated content (R5)
- [ ] `grep -q '"version": "0.9.30"' .claude-plugin/plugin.json` (R5)
- [ ] `awk '/## Table of contents/{f=1;next} f&&/^Loaded on demand/{f=0} f' .claude/skills/prose-review/reference.md | grep -qi 'agentic-register'` — TOC block names the subsection (R6)
- [ ] `test $(wc -l < .claude/skills/prose-review/SKILL.md) -lt 500` (R6)

## Parallelization

Task 02 (author-side conventions) cites the finalized subsection wording from
task 01 (reference doctrine) — a shared undecided-design coupling — so they
serialize. No concurrent-safe groups; both tasks run solo in order 01 → 02.
