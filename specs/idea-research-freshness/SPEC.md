# /idea: auto-trigger research grounding, skip it when a recent citation already exists

Status: open
Breakdown-ready: true

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
  `docs/guides/*.md`) carries a `Verified: YYYY-MM-DD` line as the next
  non-blank line after its `##` heading, matching `^Verified:
\d{4}-\d{2}-\d{2}$` exactly (no other text on that line). This is the
  one signal both a human and a future `/idea` run check before deciding
  whether a topic needs fresh research. **File-level stamps also count**:
  a `Verified:` line positioned as the next non-blank line after a file's
  H1 title (before its first `##` heading) — the shape
  `docs/guides/large-codebase-context.md` already carries today — applies
  to every `##` heading in that file that has no more specific stamp of
  its own, rather than being unrecognized by the checker and reading as
  permanently stale. A heading with its own `##`-level stamp always wins
  over the file-level one where both exist.
- **A deterministic freshness checker.**
  `.claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh
  <dir> [--today YYYY-MM-DD]` scans a `docs/`-shaped directory tree for
  headings, checks each for the pinned `Verified:` line immediately below
  it (falling back to the file-level H1 stamp above when a heading has
  none of its own), and prints one of `fresh` / `stale` / `absent` per
  matching heading: a stamp within 90 days of `--today` (default: the
  real current date) is `fresh`; older than 90 days is `stale`; no stamp
  at all (heading-level OR file-level) is `absent`. The `--today` flag
  makes the fixtures below date-relative instead of hardcoded, so they
  don't rot as the calendar advances. This script is the one mechanical
  decision point both `/idea`'s new step and this spec's tests rely on —
  no other freshness logic is duplicated elsewhere.
- **`/idea` gains a grounding-check step**, inserted as the new step 2
  between today's step 1 (scout) and step 2 (interview) in
  `.claude/skills/idea/SKILL.md` — today's steps 2-6 renumber to 3-7, and
  every internal `step N` cross-reference elsewhere in SKILL.md is
  updated to match the new numbering: when the idea's own framing asks
  for external grounding (phrases like "best practices," "how do
  [vendor/tool] do this," "research X," "backed by research/blogs from
  ..."), run `check-freshness.sh` against `docs/` to check for a
  `Verified:` stamp on a topically-matching section within the staleness
  window (default **90 days**) before dispatching anything:
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
  inserted as the new step 2 (positioned between today's step 1 and
  step 2), worded per Solution. Inserting it renumbers today's steps 2-6
  to 3-7, and every internal `step N` cross-reference elsewhere in
  SKILL.md (the ~12 the critic found at authoring time) is updated in the
  same edit to match — no reference is left pointing at the old numbers.
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
  step is mirrored into `antigravity/.agents/skills/idea/SKILL.md`
  (`antigravity/.agents/workflows/idea.md` is a thin launcher stub with no
  step text of its own — confirmed via grep, nothing to mirror there) in
  the same commit — not left un-mirrored. Antigravity's SKILL.md has its
  own, independent 5-step numbering (1. Scout, 2. Interview, 3. Write the
  spec, 4. Adversarial pass, 5. Hand off) — do not apply `.claude`'s
  6-step renumbering instruction to it literally. The grounding-check step
  inserts the same way — between today's antigravity step 1 and step 2 —
  which renumbers antigravity's own steps 2-5 to 3-6. Antigravity step 4
  ("Adversarial pass") contains one internal cross-reference, "step 5's
  hand-off", which must become "step 6's hand-off" in the same edit.
  Mirroring the CONTENT, not the file: `check-freshness.sh` and its
  `test-fixtures/` directory are `.claude`-only tooling — porting the
  script and fixtures into antigravity is out of scope (this spec's
  `.claude` leg already carries the deterministic check; duplicating it
  isn't a mirroring requirement). Antigravity's grounding-check step
  therefore describes the fresh/stale/absent decision logic **inline**,
  in its own words (the 90-day `Verified:` window and the
  fresh/stale/absent branching from Solution/R2/R3) — it does not cite
  `check-freshness.sh`'s path, which would be a non-resolving
  cross-reference under `.claude/rules/mirror-verification.md` (a file an
  antigravity reader has no reason to open, since antigravity has no
  runtime shape from which to invoke a `.claude`-rooted script).
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

Fixtures for the checks below live under a new
`.claude/skills/idea/test-fixtures/research-freshness/` directory (one
small `docs/`-shaped tree per scenario: `fresh/`, `stale/`, `no-stamp/`,
`file-level-stamp/`), created as part of this spec's implementation — not
left for the verifying agent to invent. Each fixture's `Verified:` date
(where present) is computed relative to the check's `--today` argument
rather than hardcoded, so the fixtures stay valid as the calendar
advances.

- [ ] `docs/guides/model-routing.md`'s `## Dispatch authoring: making the
choice explicit` heading has a real, current-dated `Verified:` line
      (and `## Cross-vendor grounding` too, if that sibling spec has
      already landed — see R1). No other heading in
      `docs/external-playbooks.md` or `docs/guides/*.md` gets a stamp
      from this spec (per R1's narrowed dogfood scope) — confirm none
      were added elsewhere.
- [ ] `bash check-freshness.sh <fixtures-dir>/fresh --today <fixed-date>`
      prints `fresh` for the fixture's stamped heading (a `Verified:`
      date within 90 days of `--today`), where `<fixtures-dir>` is
      `.claude/skills/idea/test-fixtures/research-freshness`.
- [ ] `bash check-freshness.sh <fixtures-dir>/stale --today <fixed-date>`
      prints `stale` for the fixture's stamped heading (a `Verified:`
      date 100+ days before `--today`).
- [ ] `bash check-freshness.sh <fixtures-dir>/no-stamp --today
<fixed-date>` prints `absent` for the fixture's heading (no
      `Verified:` line at all).
- [ ] `bash check-freshness.sh <fixtures-dir>/file-level-stamp --today
<fixed-date>` prints `fresh` for a `##` heading that itself has no
      `Verified:` line but whose file carries a fresh file-level stamp
      (the next non-blank line after the H1 title) — confirming the
      fallback the Solution/checker description above pins, exercised on
      a fixture rather than only on the pre-existing
      `docs/guides/large-codebase-context.md` case.
- [ ] `.claude/skills/idea/SKILL.md` contains the new grounding-check step
      as step 2 (between today's steps 1 and 2), naming the 90-day
      window, directing that `check-freshness.sh` (or the equivalent
      logic) decides the fresh/stale/absent branching from Solution, and
      the "illustrative, not exhaustive" phrase-pattern caveat from R2 —
      checked by grep over SKILL.md's text, not by running `/idea`.
- [ ] Every internal `step N` cross-reference in
      `.claude/skills/idea/SKILL.md` is consistent with the renumbering
      from R2: no reference still points at a step's pre-insertion
      number (old steps 2-6 are cited as 3-7 everywhere they're
      referenced, not only where they're defined) — checked by grepping
      every `step[ -][0-9]` occurrence (the space form, e.g. "step 3",
      AND the hyphenated form, e.g. "post-step-3", both count — a
      space-only pattern misses the hyphenated references at SKILL.md's
      current lines 127, 130, 137, which must become `post-step-4` once
      "Write the spec" moves 3→4) against the heading it's meant to
      reference.
- [ ] MANUAL-PENDING (unattended drain workers cannot interactively run
      `/idea` — CLAUDE.md's execution-stage launch-authorization contract
      requires a live user request naming the stage, and
      background-dispatched agents can't interview per
      `.claude/rules/token-discipline.md`'s "Background-dispatched agents
      can't interactively interview a human"): a human or attended
      session runs `/idea` against the `fresh/`, `stale/`, and
      `no-stamp/` fixtures (plus one paraphrase-only rewording of the
      `fresh/` idea per R2, carrying the same grounding intent without
      any listed trigger phrase) and confirms behavior matches the
      deterministic checks above end to end: `fresh/` (trigger-phrase or
      paraphrase) dispatches no research agent and cites the existing
      `docs/<path>:<line>`; `stale/` and `no-stamp/` dispatch research
      and write back a refreshed `Verified: <today>` stamp. This is the
      only criterion requiring a live `/idea` run — the mechanical
      fresh/stale/absent decision itself is fully covered by
      `check-freshness.sh` above.
- [ ] `bash tests/test_doc_links.sh` (existing link-checker gate) still
      passes after the `Verified:` lines are added.
- [ ] `bash evals/lint-ultra-gate.sh` passes after the SKILL.md edit (R9).
- [ ] `antigravity/.agents/skills/idea/SKILL.md` contains the new
      grounding-check step as its own step 2 (between antigravity's
      current steps 1 and 2), and its steps 2-5 are renumbered to 3-6
      (R7) — checked by grep over the SKILL.md's `## N.` headings.
- [ ] `grep -c "90.day\|90 day" antigravity/.agents/skills/idea/SKILL.md`
      → 1 or more (confirmed absent today; the antigravity step describes
      the fresh/stale/absent decision inline, per R7) AND
      `grep -c "check-freshness.sh" antigravity/.agents/skills/idea/SKILL.md`
      → 0 (confirmed absent today; must stay 0 — the antigravity step
      never cites a `.claude`-rooted script path).
- [ ] `grep -c "step 6's hand-off" antigravity/.agents/skills/idea/SKILL.md`
      → 1 or more (confirmed absent today; the mirror's own cross-reference
      consistency check, parallel to the `.claude` one above — the old
      "step 5's hand-off" reference in antigravity step 4 must become
      "step 6's hand-off" after the renumbering).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change (R8).

## Open questions

(none)

## Parallelization

Tasks 01 (checker/fixtures/stamps), 02 (`.claude` SKILL.md step +
renumbering), and 03 (antigravity mirror) are disjoint in `Touch` and
share no undecided design — the `Verified:` format, the 90-day window,
and each SKILL.md's own step-numbering scheme are all fully pinned by the
spec text, so none of the three make an open choice the others depend
on. Task 02 only _references_ task 01's script path (already fully
specified), it doesn't need task 01's actual implementation to land
first. Task 04 (version bump + closing evidence) depends on all three.

- Group: 01, 02, 03
