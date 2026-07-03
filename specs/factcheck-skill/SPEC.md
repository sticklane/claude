# `/factcheck` — close known-source factual gaps with cited primary sources

## Problem

When an answer lives in specific official docs — verify a claim, or "what do
the docs say about X" — the toolkit's only research tool is `deep-research`,
a ~100-agent fan-out → 3-vote adversarial verify → synthesize workflow. This
session showed it is the wrong tool for that job twice over: its adversarial
verifier over-refutes plain documentation facts (it returned zero surviving
claims on two legs whose answers sat in the first official doc), and its
Scope agent choked on long structured args (`StructuredOutput retry cap
exceeded` before any search ran). What actually worked was dispatching
targeted per-source `general-purpose` agents, each required to back every
claim with a verbatim quote + URL or mark it UNVERIFIED. That pattern is now
tribal knowledge (captured only as a heuristic in
`.claude/rules/token-discipline.md`, "Match the research tool to the
question"); nothing executable packages it, so the next session may reach for
`deep-research` and repeat the two failed runs.

## Solution

Add a git-tracked, model-invocable skill `.claude/skills/factcheck/SKILL.md`
that packages the targeted quote-or-UNVERIFIED pattern: it dispatches one
`general-purpose` agent per source cluster (parallel across independent
clusters), each constrained to primary sources and required to cite a
verbatim quote + exact URL per claim or return UNVERIFIED, then the skill
collects the cited findings. Its `description` routes the model here for
known-source factual questions and claim verification, while leaving
open-ended multi-source synthesis to `deep-research` — the tool-selection
split recorded in the "Match the research tool to the question" section of
`.claude/rules/token-discipline.md`. Follows the authoring conventions the
scouts confirmed: no `plugin.json` skills-manifest edit needed (directory
glob), but a `version` bump and a near-identical
`antigravity/.agents/skills/factcheck/` mirror are required, and
`bin/sync-skills` picks it up automatically. The worker prompt states the
worker's tier and an output cap explicitly (most existing skills dispatch
`general-purpose` without yet doing so — this skill sets the example the
token-discipline rules point toward; note a formal "Dispatch authoring"
section is only *proposed* in `specs/workflow-token-efficiency/`, not yet in
the repo, so this spec states the tier/cap requirement inline rather than
depending on it).

## Requirements

- R1: `.claude/skills/factcheck/SKILL.md` exists with YAML frontmatter keys
  `name: factcheck`, `description`, `argument-hint` (e.g.
  `"[claim or question, optionally with source hints]"`), and NO
  `disable-model-invocation` key (the skill is model-invocable). Body is
  under 500 lines.
- R2: The `description` is third person, states what the skill does, and
  lists concrete trigger phrases for BOTH framings — claim verification
  ("verify X against the docs", "fact-check this", "is it true that…",
  "cite the source for…") and known-source lookup ("what do the official
  docs say about…", "get me the primary source for…", "close this factual
  gap"). It must also state, in one clause, when NOT to use it: open-ended,
  multi-source synthesis where claims are contestable → that stays
  `deep-research`. (This is the routing contract the skill exists to fix.)
- R3: The first ≤30 lines of the body encode the execution contract, in
  this order: (a) primary-sources-only, with a one-line rubric for
  primary (official vendor docs / specs / first-party engineering posts)
  vs secondary (blogs, wikis, aggregators — disallowed as the basis of a
  claim); (b) every reported claim MUST carry a verbatim quote (≤30 words)
  plus the exact source URL, or be marked `UNVERIFIED`; (c) never guess and
  never substitute a secondary source to avoid an UNVERIFIED.
- R4: The skill dispatches `general-purpose` agents (they have WebSearch/
  WebFetch; the toolkit's scout/verifier/critic do not) — one per
  independent source cluster, launched in parallel when clusters are
  independent. Each worker prompt states an explicit tier (name the model
  or effort) AND an output budget — a per-worker word cap and a structured
  per-item return of verdict + URL + verbatim quote + confidence. Raw
  fetched pages stay in the worker; only the cited findings return to the
  caller.
- R5: UNVERIFIED handling: items the workers could not back with a primary
  source are reported explicitly and the run continues; they are NEVER
  dropped silently and NEVER answered from a secondary source or the
  model's prior. The skill's final output surfaces the UNVERIFIED list
  distinctly from the verified findings.
- R6: The skill produces a cited findings report as its output and states
  where it goes and what comes next: it ends with a `Next stage:` line
  (naming the downstream action, e.g. the caller merges findings into the
  relevant doc — "(human-launched)" or "none — <user action>", per
  conventions; it does not self-chain into a doc edit).
- R7: Cross-file obligations, all in the same commit: a near-identical
  ported mirror at `antigravity/.agents/skills/factcheck/SKILL.md` (plus
  the reference.md) — "near-identical" per CLAUDE.md, adapting agent→skill
  references and runtime/tier wording for Antigravity, NOT byte-identical
  (existing mirrors legitimately differ by dozens of lines); and a
  `version` bump in `.claude-plugin/plugin.json`. No `plugin.json`
  skills-manifest edit (directory glob) and no `bin/sync-skills` edit
  (auto-discovers).
- R8: The exact worker-prompt template and the full primary-vs-secondary
  source rubric live in `.claude/skills/factcheck/reference.md` (required),
  loaded on demand — NOT in the SKILL.md body, which stays a checklist per
  the conventions. If reference.md exceeds 100 lines it opens with a table
  of contents. References stay one level deep (SKILL.md → reference.md,
  never reference → reference).

## Out of scope

- Editing or "fixing" `deep-research` itself — it is a harness built-in
  with no editable SKILL.md in this repo. This skill is the complementary
  narrow-lookup tool, not a replacement; `deep-research` remains for
  open-ended synthesis.
- A new web-enabled agent definition. The worker is the built-in
  `general-purpose` agent, so no `.claude/agents/*` addition and no
  agent-enumeration edit to `plugin.json`.
- Automatic doc-merging or committing of findings — the skill returns a
  cited report; acting on it (editing a research doc, etc.) is the
  caller's decision.
- Restating the deep-research args-length gotcha or the tool-selection
  heuristic in the skill body beyond the one-line "when NOT to use"
  clause; the full heuristic already lives in `token-discipline.md`.

## Acceptance criteria

- [ ] `test -f .claude/skills/factcheck/SKILL.md` and it has no
      `disable-model-invocation` line
      (`! grep -q disable-model-invocation .claude/skills/factcheck/SKILL.md`) (R1)
- [ ] Frontmatter has `name: factcheck` and a `description:`; body is
      < 500 lines (`awk 'END{exit NR>=500}'`) (R1)
- [ ] `description` contains both a claim-verification trigger and a
      known-source-lookup trigger AND a "not for open-ended synthesis /
      deep-research" clause (grep for the three) (R2)
- [ ] First 30 lines contain the quote-or-UNVERIFIED contract and the
      primary-vs-secondary rubric
      (`head -30 SKILL.md | grep -qi "UNVERIFIED"` and `... grep -qi "primary"`) (R3)
- [ ] Body names `general-purpose` as the worker and states a tier + an
      output cap for it (grep `general-purpose`, and a tier token +
      a word/`token` cap) (R4)
- [ ] Body contains a `Next stage:` line (R6)
- [ ] `diff .claude/skills/factcheck/SKILL.md
      antigravity/.agents/skills/factcheck/SKILL.md` is empty, and
      `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a version bump (R7)
- [ ] End-to-end in a FRESH session: invoke `/factcheck` on a known-source
      factual question with an obviously-checkable answer AND one part with
      no published answer; observe it (a) dispatches ≥1 `general-purpose`
      web worker, (b) returns findings each carrying a verbatim quote + URL,
      and (c) lists the unbackable part as UNVERIFIED rather than answering
      it. Then confirm an open-ended "survey the landscape of X" prompt does
      NOT trigger `/factcheck` (routing/anti-trigger check per R2).

## Open questions

(none)
