# Token-efficiency conventions for agent-dispatching skills

## Problem

The toolkit's execution skills (`/drain`, `/parallel`, `/autopilot`,
`/design`, `/evals`) all spawn subagents, and none of them state a model or
effort tier for any dispatch — every spawned agent silently inherits the
session model at default effort, including purely mechanical stages
(`.claude/skills/drain/SKILL.md:51`, `parallel/SKILL.md:37-40`,
`autopilot/SKILL.md:40-42`). Meanwhile the repo's own research has already
adopted concrete practices — stage-type tiering, 1–2k-token subagent
returns, bounded evaluator loops, single-call rubric judging — that live
only in `docs/*-research-2026-07.md` and specs, not in any authoring
convention, so each new skill repeats the omissions. The `deep-research`
workflow is a harness built-in with no repo-owned definition at all, so its
search/fetch stages also run at session-model rates.

## Solution

Codify a token-efficiency authoring checklist as a new section of
`.claude/rules/token-discipline.md` (citing the research docs, not
restating them), retrofit the five execution skills to comply, add a
repo-owned `deep-research` workflow script with per-stage tiering, and
enforce it all with a `bin/check-token-discipline` conformance script
modeled on `bin/sync-skills` (tests in `tests/`, TDD).

Tiering policy (decided 2026-07-03, interview): **tier by stage type** —
mechanical stages (search, fetch, extract, grep-like scouting, conformance
checks) run on Haiku or `effort: low`; judgment stages (implementation,
verification, judging, synthesis) keep the session model, raising effort
only for the hardest verify/judge stages.

## Requirements

- R1: `.claude/rules/token-discipline.md` gains a "Dispatch authoring"
  section stating, each in one or two lines with a citation into
  `docs/orchestration-research-2026-07.md` /
  `docs/context-management-research-2026-07.md` /
  `docs/anthropic-playbook.md`: (a) tier-by-stage-type rule above; (b)
  subagent returns capped at 1–2k tokens (structured verdict/summary, never
  transcripts); (c) evaluator-optimizer loops bounded to 2–4 cycles,
  skipped when a deterministic check exists; (d) single-call rubric judge
  as the default over multi-judge voting; (e) the deterministic-vs-model-
  driven placement axis (script owns loops/fan-out/gates, model owns
  decomposition/routing); (f) effort-scaling language for dispatch prompts
  (1 agent / 3–10 calls for lookups; 2–4 agents / 10–15 calls for
  comparisons; 10+ only breadth-first).
- R2: `CLAUDE.md` (repo) Authoring conventions gain exactly one new bullet
  pointing at that section — no restated content.
- R3: Every agent-spawning instruction in
  `.claude/skills/{drain,parallel,autopilot,design,evals}/SKILL.md` (and
  their `reference.md` where dispatch details live) states an explicit tier
  — either the model (`haiku` / session model) or `effort` — plus an output
  budget for what returns to the orchestrator. Workers that implement code
  (drain/parallel/autopilot) stay session-model and are instructed to
  delegate their own mechanical scouting to Haiku scouts; skill text says
  so explicitly.
- R4: Any loop a skill authorizes (retry-on-BLOCKED, evaluate-and-revise)
  carries an explicit cycle bound of at most 4.
- R5: A repo-owned `.claude/workflows/deep-research.js` exists, equivalent
  in phases to the built-in (scope → search → fetch → verify → synthesize)
  but with per-stage tiering: search/fetch/claim-extraction at
  `effort: 'low'`, verify and synthesize at session model; all fan-out
  stages schema-constrained. Its first statement is
  `log('[repo-deep-research]')` so resolution is observable. First step of
  implementing R5 is a resolution probe: invoke
  `Workflow({name: "deep-research"})` with the script symlinked into
  `~/.claude/workflows/` and confirm the marker appears in the progress
  log. If the harness built-in wins name resolution, name the repo script
  `research.js` (invoked as `research`) instead and say so in the R1 rule
  section. `bin/sync-skills` is extended to also symlink
  `.claude/workflows/*` into `~/.claude/workflows/`, honoring the same
  `SYNC_SKILLS_SRC`-style env overrides it already uses so tests never
  touch the real home directory.
- R6: `bin/check-token-discipline [skills-root]` (default: repo root)
  exits 0 iff every file in its in-scope list (the five SKILL.md files,
  their reference.md where dispatch details live, and the deep-research
  workflow script) passes three checks, and exits 1 with a per-file,
  per-check report otherwise. Normative definitions: a *dispatch line*
  matches `/Task\(|agent\(|spawn|dispatch|launch/i`; each dispatch line
  must have a *tier token* (`haiku`, `session model`, `opts.model`, or
  `effort`) within ±5 lines. An *output-budget statement* is a line
  containing a numeric cap or budget word (`≤`, `under N words`, `tokens`,
  `verdict + evidence`) — at least one per file. A *loop line* matches
  `/retry|re-dispatch|revise|iterate|cycle/i` and must have a numeric
  bound within ±3 lines. Exact regexes live in the script; its tests
  encode these definitions with fixture files. Tests first (`tests/`),
  following the `bin/sync-skills` precedent (commits `05df3ef`/`0629fa7`,
  entrypoint `tests/test_sync_skills.sh` — there is no aggregate runner;
  add `tests/test_check_token_discipline.sh` alongside).
- R7: Each retrofitted skill's existing antigravity counterpart (mirrored
  under `antigravity/` — as a workflow file for the human-only skills, a
  skill file otherwise; follow whatever path each skill already mirrors
  to) carries the same text changes in the same commit.
  `deep-research.js` is Claude-Code-specific and gets no antigravity
  counterpart. `.claude-plugin/plugin.json` `version` is bumped once
  (skill behavior changes).

## Out of scope

- Other user-level skills (`morning-brief`, `workboard`, `redacted`, …) and
  the `.claude/agents/*` definitions (scout's Haiku default and ≤300-word
  budget already comply).
- Token-usage evals comparing spend before/after (decided against —
  cost/noise; conformance check only).
- Any functional change to what a skill does: dispatch shape, worktree
  isolation, verdict schemas, and human-gate placement all stay as-is.
- Amending `specs/ultra-mode/` or `specs/orchestrator-context/` — the
  pending research follow-up run owns those docs; if its findings change
  the adopt-lists, the rule section cites the docs and inherits the change
  without editing this spec.

## Acceptance criteria

- [ ] `bash tests/test_sync_skills.sh && bash
      tests/test_check_token_discipline.sh` both pass (R5 sync extension,
      R6; tests use the env-override src/dest so they never touch `~`)
- [ ] `bin/check-token-discipline` exits 0 on the retrofitted tree, and
      `git worktree add /tmp/pre-retrofit <pre-retrofit-sha> &&
      bin/check-token-discipline /tmp/pre-retrofit` exits 1 (R3, R4, R6)
- [ ] Resolution probe recorded: invoking the named workflow shows
      `[repo-deep-research]` in the progress log, OR the spec's fallback
      (`research`) was taken and the R1 section documents it (R5)
- [ ] After commit + push + `git -C ~/agentic-toolkit pull &&
      ~/agentic-toolkit/bin/sync-skills`:
      `test -L ~/.claude/workflows/deep-research.js` (or `research.js`)
      succeeds (R5 — sync-skills reads `~/agentic-toolkit`, so this check
      is only valid after the pull; use env overrides to test earlier)
- [ ] `git show --stat HEAD` includes `.claude/skills/` and `antigravity/`
      paths, and `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a
      version bump (R7)
- [ ] End-to-end: after the pull+sync above, a fresh session invoking
      `/parallel` on a two-task toy list produces dispatch prompts
      containing the tier and output-budget language (observed in the
      dispatch text before workers run)

## Open questions

(none)
