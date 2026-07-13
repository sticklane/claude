Archived: 2026-07-13 (Steven, attended triage) — thin value (the automated workflow is ~"run /deep-research once and save it dated"), heavy revision (Workflow/ultracode contract + ~8-criterion restructure), hard-blocked behind idea-research-freshness. Re-/idea after the sibling ships and the pattern proves itself.

# /domain-knowledge: build and consult a per-project cache of domain best practices

## Problem

When a codebase is building a specific *kind* of application — an RTS
game engine, a Vertex AI app on GCP, a video-player/media pipeline — best
practices for that domain live scattered across docs/blogs/repos, and
this toolkit has nothing that proactively researches and caches them.
Checked against what frontier labs' own tools do: Anthropic explicitly
recommends keeping domain knowledge *out* of always-on memory —
"For domain knowledge or workflows that are only relevant sometimes, use
skills instead" (code.claude.com/docs/en/best-practices) — validating a
skill-consultable doc over a CLAUDE.md injection. Cursor's `.cursor/rules`
is "for domain-specific knowledge about your codebase"
(cursor.com/docs/context/rules), Amazon Kiro's "steering" files give
"persistent knowledge about your workspace" (kiro.dev/docs/steering), and
Amazon Q Developer has an equivalent "project rules" library
(docs.aws.amazon.com/amazonq)... but every one of these is **reactive and
human-authored** (Cursor: "Add rules only when you notice Agent making the
same mistake repeatedly"; none proactively researches an external domain).
OpenAI/DeepMind/DeepSeek publish nothing on-topic. So the storage pattern
(a persistent, skill-consulted knowledge file) has strong precedent — the
proactive-research-and-cache behavior this idea asks for does not, and is
exactly where the user's own caution ("be mindful of how aggressively we
do deep research") matters most.

## Solution

A new skill, `/domain-knowledge`, human-invoked (not auto-triggered from
within other flows — the cost-discipline concern means this stays an
explicit choice, unlike `/idea`'s grounding-check auto-trigger). It:

1. Determines the application's domain — first via a `scout` pass over
   `package.json`/`README`/existing code/dependencies; if genuinely
   ambiguous, asks the user directly (`AskUserQuestion`) rather than
   guessing.
2. Checks for an existing `docs/domain-knowledge/<domain-slug>.md` with a
   `Verified: YYYY-MM-DD` stamp (same convention `specs/
   idea-research-freshness` introduces) within the staleness window — if
   fresh, reports it exists and stops; no research dispatched.
3. If stale/absent, dispatches **one** `deep-research` run (this is
   exactly the open-ended, multi-source, contestable-claims question
   `deep-research` is for, per `.claude/rules/token-discipline.md`'s
   existing routing rule) scoped to "[domain] best practices for
   [detected tech stack]" — capped, not a fleet of unbounded research
   passes, honoring the cost-discipline ask.
4. Writes findings to `docs/domain-knowledge/<domain-slug>.md` with
   citations and a `Verified: <today>` stamp.
5. Other skills may optionally consult this file by name (e.g. `/idea`'s
   interview step, `/design`'s "Frame it" step) — this spec adds no
   forced integration into them; it only makes the artifact discoverable
   by a predictable path.

## Requirements

- **R1**: `/domain-knowledge`'s domain-detection step tries repo signals
  first (dependency manifests, README, existing code patterns via one
  `scout` dispatch); if the result is ambiguous or the scout can't tell,
  it asks the user directly rather than guessing a domain and researching
  the wrong thing.
- **R1b (slug canonicalization)**: The domain-slug is the sole cache key
  R2 checks freshness against, so it must be stable across phrasing
  variants — "RTS game" from a scout's dependency-based detection and
  "real-time strategy game" from a user's direct answer must resolve to
  the same file, or the freshness check silently misses and re-runs the
  full R3 research every time (defeating the whole cost-discipline point
  of this spec). Before creating a new slug, list existing files under
  `docs/domain-knowledge/` and ask (via a cheap comparison, not another
  research dispatch) whether any existing slug already names the same
  domain in different words; only mint a new slug when none matches.
  Canonicalize new slugs to short, kebab-case, common-name form (prefer
  "rts-game" over "real-time-strategy-game" when both describe the same
  detected domain).
- **R2**: Before dispatching any research, check
  `docs/domain-knowledge/<domain-slug>.md` (resolved per R1b) for a
  `Verified:` stamp within 90 days (same window `idea-research-freshness`
  establishes, for consistency — not re-derived here). Fresh → report the
  existing file path, stop. Stale/absent → proceed to R3.
- **R3**: Dispatch exactly one `deep-research` run per invocation, scoped
  to the detected domain + stack — invoked via the `Workflow` tool
  (`Workflow({name: "deep-research", args: "..."})`), the only mechanism
  that runs it. **Verify at implementation time** whether the harness's
  actual `Workflow` tool contract accepts "a skill's own instructions
  call for it" as sufficient sanction on its own, or whether it also
  requires the runtime's "ultracode" opt-in for the invoking session
  (this repo's own docs — `human-gates.md` reason 5,
  `workflow-author/SKILL.md`'s framing — emphasize the ultracode opt-in
  as the standing sanction elsewhere, so don't assume the skill-
  instructions path alone suffices without confirming it against the
  live tool contract). If ultracode turns out to be required too, add a
  precondition check/note to this skill rather than silently failing at
  dispatch time. This is genuinely a ~100-agent fan-out (5 search agents +
  up to 15 source fetches + up to 75 adversarial-verification agents +
  synthesis, per `.claude/rules/token-discipline.md`'s own "~100-agent
  cost" framing of this exact workflow) — not a "bounded single call."
  *If* the tool contract does accept "a skill's own instructions call for
  it" as sufficient sanction (one of the `Workflow` tool's documented
  invocation paths), then R5's `disable-model-invocation` — a human
  explicitly typing `/domain-knowledge` — is what satisfies it. *If* the
  live contract instead also requires the runtime's ultracode opt-in,
  this skill needs that precondition added per the paragraph above before
  it can dispatch — this is not yet a settled fact either way, only a
  design intent to confirm at implementation time. No fan-out beyond
  `deep-research`'s own standard phases regardless of which path applies
  — this requirement exists to prevent scope creep into repeated/
  redundant research passes.
- **R4**: Write `docs/domain-knowledge/<domain-slug>.md` with the
  research findings (claims + citations, in `deep-research`'s normal
  output shape) and a `Verified: <today>` stamp under its top heading.
- **R5**: `/domain-knowledge` carries `disable-model-invocation: true` —
  a human types it explicitly, every time; it is never auto-triggered by
  `/idea`, `/design`, or any other skill's own flow (contrast with
  `idea-research-freshness`'s grounding-check, which stays model-invocable
  because it's scoped to a cheap doc-freshness lookup, not a full research
  dispatch). This is a direct application of `docs/human-gates.md`'s
  reason 1 (spend discontinuity): a ~100-agent fan-out is exactly the
  scale of spend decision that document reserves for explicit human
  authorization, same as `/build`/`/drain`/`/evals`. (An earlier draft of
  this spec argued the opposite — that no gate was needed because this
  was "a bounded single research call" — that characterization was wrong
  and is corrected here.)
- **R6**: Per CLAUDE.md's mirroring convention, `/domain-knowledge` is
  created in both `.claude/skills/domain-knowledge/` and its
  `antigravity/.agents/skills/domain-knowledge/` counterpart in the same
  commit — but the antigravity port's R3 step degrades: Antigravity has
  no scripted `Workflow`-tool fan-out (per its own README: "Ultracode
  workflow scripts... Human-dispatched launch-list workflows — no
  scripted fan-out in Antigravity"), so the ported skill's research step
  is a human-dispatched launch-list (the human manually runs however many
  research passes they choose in the Agent Manager) rather than one
  automated `Workflow` call — the detect/freshness-check/write/report
  steps (R1, R2, R4) port unchanged.
- **R7**: `.claude-plugin/plugin.json`'s `version` is bumped (new skill
  added) and its skills manifest is unaffected beyond the version bump
  (per CLAUDE.md: skills are manifest-free, only agents require a
  manifest edit).

## Out of scope

- Auto-detecting domain changes over time and re-triggering research
  unprompted — this is always a human-invoked action (R5).
- Forcing `/idea`, `/design`, `/build`, etc. to read
  `docs/domain-knowledge/*.md` automatically — optional consultation only
  (Solution point 5), no required integration in this spec.
- Any staleness-window number other than 90 days, or a mechanical CI gate
  policing it — matches `idea-research-freshness`'s own scope limits.
- Researching multiple domains in one invocation, or maintaining a
  cross-project domain-knowledge library shared between repos — scoped
  to one domain, one repo, per invocation.

## Acceptance criteria

- [ ] `.claude/skills/domain-knowledge/SKILL.md` exists, describing the
      five-step flow (detect, check freshness, research once if needed,
      write, report).
- [ ] Fixture repo with clear domain signals (e.g. a `package.json`
      depending on a game-engine library): domain detection succeeds via
      scout alone, no `AskUserQuestion` needed.
- [ ] Fixture repo with ambiguous/no domain signals: the skill asks the
      user directly rather than guessing.
- [ ] Fixture with an existing `docs/domain-knowledge/<slug>.md` stamped
      within 90 days: the skill reports the existing path and dispatches
      no `deep-research` run.
- [ ] Fixture proving R1b: an existing `docs/domain-knowledge/rts-game.md`
      stamped within 90 days, and a repo whose signals would naturally be
      described as "real-time strategy game" — the skill resolves to the
      existing `rts-game.md` (reports its path, dispatches no research)
      instead of minting a new `real-time-strategy-game.md`.
- [ ] Fixture with a stamp 100+ days old (or none): exactly one
      `deep-research` dispatch occurs, and the resulting file has a
      current-dated `Verified:` stamp and cited findings.
- [ ] `antigravity/.agents/skills/domain-knowledge/` exists with
      equivalent content (R6).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change (R7).
- [ ] End-to-end: running `/domain-knowledge` in a fixture repo clearly
      building, say, an RTS game produces
      `docs/domain-knowledge/rts-game.md` with real cited best-practice
      claims a developer could act on.

## Open questions

(none)
