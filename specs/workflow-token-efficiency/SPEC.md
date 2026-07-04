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
modeled on the `bin/sync-skills` pattern (tests in `tests/`, TDD; note
sync-skills itself was retired 2026-07-03 — skills are plugin-served now —
but its env-override + test structure remains the precedent).

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
  section. **Amendment 2026-07-03:** `bin/sync-skills` is retired (skills
  are plugin-served; user-dir copies shadow the plugin), so do NOT extend
  it. Ship a narrow `bin/sync-workflows` instead that symlinks ONLY
  `.claude/workflows/*` into `~/.claude/workflows/` (plugins do not ship
  workflows, so this one sync remains legitimate), with the same
  env-override pattern (`SYNC_WORKFLOWS_SRC`/`_DEST`) so tests never
  touch the real home directory.
- R6: `bin/check-token-discipline [skills-root]` (default: repo root)
  exits 0 iff every file in its in-scope list passes three checks, and
  exits 1 with a per-file, per-check report otherwise. The in-scope
  list, exactly: `.claude/skills/drain/SKILL.md`,
  `.claude/skills/drain/reference.md`,
  `.claude/skills/parallel/SKILL.md`,
  `.claude/skills/autopilot/SKILL.md`,
  `.claude/skills/autopilot/reference.md`,
  `.claude/skills/design/SKILL.md`, `.claude/skills/evals/SKILL.md`,
  `.claude/skills/evals/reference.md`, and
  `.claude/workflows/deep-research.js`. The check operates on
  **blank-line-separated paragraphs** (not single lines), skipping YAML
  frontmatter and table rows (lines starting with `|`), so verb/noun
  pairs split across wrapped lines are seen together. Three checks:

  - *Dispatch → tier.* A paragraph is a dispatch instruction if it
    contains `Task(`/`agent(` OR an imperative dispatch verb
    (`spawn`/`dispatch`/`launch`) *adjacent to* (same clause/line, not
    merely the same paragraph) an agent noun (`agent`/`worker`/
    `session`) — so incidental co-occurrence like "dispatch order" and
    "worker's lock" in one prose paragraph does not count — excluding
    the adjectival forms (`dispatchable`) and pure prohibitions. Each
    dispatch paragraph must carry a tier token (`haiku`, `session
    model`, `opts.model`, or `effort`) in itself or an adjacent
    paragraph.
  - *Output budget.* Each file has ≥1 statement matching
    `(≤|under|at most|no more than|cap(ped)?)\s.{0,20}(words|tokens|lines)`
    OR the literal `verdict + evidence`. Bare cost commentary like
    "3× the tokens" must NOT satisfy this.
  - *Bounded loops.* A paragraph naming an iterative re-dispatch
    (`retry`, `re-dispatch`, `revise`, `iterate`, `cycle`, or `relaunch`
    used as a repeating action) must state a bound in itself or an
    adjacent paragraph: a numeral 1–4 or a spelled-out cap (`once`,
    `twice`, `at most one/two/three/four`). NOT a trigger: the term
    preceded by `no`/`never`; hyphenated forms (`relaunch-with-evidence`);
    and a one-shot reading where the term is immediately followed by a
    non-bound benign modifier describing the state, not a repeat count
    (e.g. `relaunch clean`) rather than by a count. `tournament` is not a
    loop trigger (its bound is covered by drain's "at most one
    tournament" prose and its dispatch by the dispatch check).
    *Flag-when-unsure (wte-08,
    tasks/08-loop-bound-residuals.md):* the loop-bound and dispatch
    checks err toward flagging on a curated in-scope list — an ambiguous
    or oddly-phrased bound flags, and the fix is to state the bound
    adjacently (e.g. drain's baton "max-generations cap of 10"), never to
    widen the regex; precision is bought only via enumerated,
    fixture-locked carve-outs.

  These prose definitions state intent; the **tests are the contract**.
  Ship `tests/test_check_token_discipline.sh` with fixtures encoding at
  minimum: drain's actual retry paragraph (must PASS the loop check
  unmodified), the prose lines the check must NOT flag
  (`drain/SKILL.md:32` tournament-cleanup, `drain/reference.md:154` "no
  relaunch", `autopilot/reference.md:108` "relaunch clean",
  `design/SKILL.md:47` "3× the tokens"), and the wrapped dispatches at
  `drain/SKILL.md:68-69` and `design/SKILL.md:41-42` (must be SEEN as
  dispatches). The implementer tunes the regexes until every fixture
  passes; the spec does not freeze regex syntax. Tests first, following
  the `bin/sync-skills` precedent (commits `05df3ef`/`0629fa7`, entrypoint
  was `tests/test_sync_skills.sh`; both retired 2026-07-03 but the commits
  remain the structural reference — there is no aggregate runner).
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
- The `/build` execution stage: although CLAUDE.md lists it among the
  execution stages, it dispatches the `scout` and `verifier` agents,
  which carry their own tier defaults — it is not in the retrofit set and
  not in R6's file list.
- Token-usage evals comparing spend before/after (decided against —
  cost/noise; conformance check only).
- Any functional change to what a skill does: dispatch shape, worktree
  isolation, verdict schemas, and human-gate placement all stay as-is.
- Amending `specs/ultra-mode/` or `specs/orchestrator-context/` — the
  2026-07-03 research follow-up (commit `7cb3b69`) already updated those
  docs and amended `orchestrator-context`; this spec's rule section cites
  the research docs and inherits any adopt-list change without editing
  those specs.

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
- [ ] After commit + `~/claude/bin/sync-workflows` (amended 2026-07-03:
      sync-skills retired; the dev checkout is `~/claude`):
      `test -L ~/.claude/workflows/deep-research.js` (or `research.js`)
      succeeds (R5 — use the env overrides to test without touching the
      real home directory first)
- [ ] `git show --stat HEAD` includes `.claude/skills/` and `antigravity/`
      paths, and `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a
      version bump (R7)
- [ ] End-to-end: after the pull+sync above, a fresh session invoking
      `/parallel` on a two-task toy list produces dispatch prompts
      containing the tier and output-budget language (observed in the
      dispatch text before workers run)

## Open questions

(none)

## Parallelization

See specs/QUEUE.md (canonical, single copy) — this spec's tasks are
wired into the combined wave plan there; the Depends-on headers in
tasks/ are the machine-readable source.

## Amendments

- **2026-07-03 (breakdown critic):** R4/R6 loop-bound scope — a named
  generation cap (e.g. drain's baton max-generations 10, from
  specs/orchestrator-context) is a relaunch ceiling, not an
  evaluator-optimizer loop; the R6 checker treats "max-generations" /
  "generations cap" phrasing as a stated bound (non-failing) even though
  the numeral exceeds 4. Encode this as a must-PASS fixture in
  tests/test_check_token_discipline.sh (drain's post-baton paragraph).
