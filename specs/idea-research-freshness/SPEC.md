# /idea: auto-trigger research grounding, skip it when a recent citation already exists

## Problem

This session hit the same pattern twice: an idea framed around "best
practices" / "how do frontier labs do X" needed external research before a
spec could be written responsibly (codebase-indexing best practices;
multi-vendor model-routing citations). Neither time did `/idea`'s own
SKILL.md direct that — it happened because the executing session
recognized the need and manually reached for `/deep-research` or
`factcheck`-style agents. There's also no policy against redoing that work
pointlessly: `docs/guides/model-routing.md` already had Anthropic citations
before this session added OpenAI/DeepMind/DeepSeek to it — with no
"already covered, don't re-research" signal, a future idea touching the
same topic has no way to know the existing citations are recent and
trustworthy versus stale and due for a refresh.

## Solution

- **A dated citation-freshness convention.** Any doc section that cites
  external research (currently `docs/external-playbooks.md` and
  `docs/guides/*.md`) carries a `Verified: YYYY-MM-DD` line immediately
  under its heading. This is the one signal both a human and a future
  `/idea` run check before deciding whether a topic needs fresh research.
- **`/idea` gains a grounding-check step**, inserted between step 1
  (scout) and step 2 (interview) in `.claude/skills/idea/SKILL.md`: when
  the idea's own framing asks for external grounding (phrases like "best
  practices," "how do [vendor/tool] do this," "research X," "backed by
  research/blogs from ..."), grep `docs/` for a `Verified:` stamp on a
  topically-matching section within the staleness window (default **90
  days**) before dispatching anything:
  - **Fresh match found** → reuse it: cite the existing `docs/<path>:<line>`
    directly in the spec's Solution/Problem, dispatch no research agents.
  - **Stale or no match** → dispatch research the same way this session
    did — `factcheck`-style targeted agents for a known-source question
    (which vendor said what), `/deep-research` for a genuinely open-ended
    one (per `.claude/rules/token-discipline.md`'s existing "Match the
    research tool to the question" routing — cite it, don't restate) —
    then write or refresh the `Verified: <today>` stamp on the doc section
    the findings land in.

## Requirements

- **R1**: The `Verified: YYYY-MM-DD` line means "the date this heading's
  citations were last actually checked against their live sources" — never
  a fabricated/copied date for content nobody re-verified this session.
  This spec dogfoods the convention **only** where the content was
  actually (re-)verified: `docs/guides/model-routing.md`'s
  `## Dispatch authoring: making the choice explicit` heading (whose body
  cites the Anthropic URLs — verified this session, no heading is
  literally named "Anthropic") gets a real current-dated stamp. If
  `specs/model-routing-multi-vendor-citations` has already shipped its
  `## Cross-vendor grounding` section by the time this spec is
  implemented, that heading gets one too (its citations were verified
  when that spec's research ran); if it hasn't yet, this spec doesn't
  block on it — whichever spec lands second adds that stamp. Every OTHER
  externally-cited heading across `docs/external-playbooks.md` and
  `docs/guides/*.md` (the ~46 URLs the repo-navigability/playbook scouts
  found, none re-verified this session) is explicitly **left unstamped**
  by this spec — an absent stamp already reads as "stale" per R3's own
  rule, which is the honest state for content nobody has re-checked. A
  human or a future `/idea` run backfills real stamps for those,
  heading by heading, only as each is actually re-verified.
- **R2**: `.claude/skills/idea/SKILL.md` gains a grounding-check step,
  positioned between today's step 1 and step 2, worded per Solution.
  Detection of "needs external grounding" is judgment-based (the
  executing session reads the idea's own phrasing and intent), not a
  fixed keyword list — the step names the phrase patterns from Solution
  as illustrative triggers, explicitly stating they are illustrative, not
  exhaustive, so a paraphrased idea with the same intent but none of the
  listed words still qualifies. This is inherently harder to pin with a
  fixture than a deterministic check — the acceptance criteria below test
  the mechanical fresh/stale branching precisely (R3/R4/R5), and add one
  paraphrase-only case as the best available proxy for the judgment
  claim, rather than asserting judgment behavior is fully fixture-tested.
- **R3**: The staleness window is **90 days**: a `Verified:` date older
  than that is treated the same as no stamp at all (stale, re-research).
- **R4**: On a stale/absent match, after research completes, `/idea`
  writes/updates the `Verified: <today>` line on whichever doc section the
  new findings were recorded into (or creates one, if the findings don't
  belong in an existing doc — e.g. a new `docs/guides/` page).
- **R5**: On a fresh match, the spec being written cites the existing
  `docs/<path>:<line>` location directly (so a reader can trace the claim)
  instead of re-summarizing findings from scratch — no research agents are
  dispatched for that topic in that `/idea` run.
- **R6**: This convention and step apply to `/idea` only in this spec.
  Extending it to `/design`'s "Frame it" step (which can also need
  external grounding for a technology choice) is explicitly deferred.
- **R7**: Per CLAUDE.md's mirroring convention, the new grounding-check
  step is mirrored into `antigravity/.agents/skills/idea` (and
  `antigravity/.agents/workflows/idea.md` if that file also documents
  idea's step sequence), in the same commit — not left un-mirrored.
- **R8**: `.claude-plugin/plugin.json`'s `version` is bumped (skill
  behavior changed in `/idea`).
- **R9**: Since `/idea` is one of the four ultra-path skills (critique,
  drain, build, idea) with a standalone gate check, `bash
  evals/lint-ultra-gate.sh` is run and passes after this edit — the new
  step is inserted before `.claude/skills/idea/SKILL.md`'s `## Ultra
  path` section, so this confirms no "ultra" mention drifted outside its
  required ±3-line window around the "active runtime profile" marker.

## Out of scope

- Extending the `Verified:` convention or the grounding-check step to
  `/design`, `/critique`, or any other skill — `/idea` only, for now.
- A fully automated staleness checker/CI gate that flags docs past the
  90-day window — this spec only makes `/idea` consult the stamp; it
  doesn't build a background job to police it.
- Retrofitting `Verified:` stamps onto every existing `docs/` file — only
  `docs/external-playbooks.md` and `docs/guides/*.md` (R1), since those
  are the files that currently cite external research.
- Changing the 90-day number based on per-topic volatility — one fixed
  default for now.

## Acceptance criteria

Fixtures for the four checks below live under a new
`.claude/skills/idea/test-fixtures/research-freshness/` directory (one
small `docs/`-shaped tree per scenario: `fresh/`, `stale/`, `no-stamp/`),
created as part of this spec's implementation — not left for the
verifying agent to invent.

- [ ] `docs/guides/model-routing.md`'s `## Dispatch authoring: making the
      choice explicit` heading has a real, current-dated `Verified:` line
      (and `## Cross-vendor grounding` too, if that sibling spec has
      already landed — see R1). No other heading in
      `docs/external-playbooks.md` or `docs/guides/*.md` gets a stamp
      from this spec (per R1's narrowed dogfood scope) — confirm none
      were added elsewhere.
- [ ] `.claude/skills/idea/SKILL.md` contains the new grounding-check step
      between today's steps 1 and 2, naming the 90-day window, the
      fresh-vs-stale branching from Solution, and the "illustrative, not
      exhaustive" phrase-pattern caveat from R2.
- [ ] Using the `fresh/` fixture (a `Verified:` stamp dated within 90
      days on a section topically matching a test idea phrased "research
      best practices for X, backed by Y"): a fresh agent running `/idea`
      against it produces a spec citing that existing doc location; the
      transcript shows no research-agent (`factcheck`/general-purpose
      web-research/`deep-research`) dispatch.
- [ ] Using the `stale/` fixture (identical, but the stamp is dated 100+
      days ago): research agents ARE dispatched, and the resulting spec's
      citations include a refreshed `Verified: <today>` stamp written back
      to that doc section.
- [ ] Using the `no-stamp/` fixture (matching section, no `Verified:` line
      at all): treated identically to `stale/` (research dispatched,
      stamp written).
- [ ] Using the `fresh/` fixture again, but with the test idea reworded to
      carry the same grounding intent without any of R2's listed trigger
      phrases (e.g. "let's make sure our approach here matches what other
      labs have published"): the fresh match is still found and cited,
      demonstrating the check isn't a literal keyword match on the
      illustrative phrase list.
- [ ] `bash tests/test_doc_links.sh` (existing link-checker gate) still
      passes after the `Verified:` lines are added.
- [ ] `bash evals/lint-ultra-gate.sh` passes after the SKILL.md edit (R9).
- [ ] `antigravity/.agents/skills/idea` (and `workflows/idea.md` if
      applicable) reflect the same grounding-check step as
      `.claude/skills/idea/SKILL.md` (R7).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change (R8).

## Open questions

(none)
