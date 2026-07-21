# ctx usage review — all sessions, 2026-07-17 → 2026-07-21

Cross-chat review of every Claude Code transcript (main sessions +
subagents, ~1,100 files) for actual `ctx` usage and for structure
questions answered without it. Four parallel analysis agents covered:
fooszone (the survey sessions), the other 7 indexed repos + the rollout
session, ~/claude (dev + dogfood), and a dedicated missed-opportunity
sweep. This file is the shared evidence base for specs
`ctx-dispatch-adoption`, `ctx-doc-drift-gate`, and
`ctx-output-shape-gaps`; findings already owned by the earlier ctx
specs (minified-skip, dead-code-zones, absence-check, query-ergonomics,
skill-token-doctrine, cujs, ctxignore-git-overlay) are not restated.

## What worked

- **refs/sig/tree/deps replaced file reads when actually used.** The
  fooszone survey (cfd7ce8f, 2026-07-20→21) located a three-way
  homography duplication (`src/video/homography.ts:37/74`,
  `Canvas.tsx:81`, `possessionAnalyzer.ts:191`) and 4 separate Go
  `writeJSON` defs entirely from `ctx refs`, spawning two dedup specs
  without reading any of the files. The only body read afterward was a
  22-line `sed` slice — correct ladder behavior.
- **Breakdown + ctx pairing.** budget_analysis session 35b223ab ran
  `ctx tree finmodel.py; ctx tree viz.py` and wrote three task files
  with zero source reads ("cheap, no file reads" → "Structure
  confirmed").
- **map as an index smoke test.** The rollout session's per-repo
  `ctx map --tokens 200` instantly exposed both signal and index
  defects (dist/ pollution → ctxignore spec; minified JS → minified-skip
  spec).
- **Resilience value.** When all 4 scouts died on the spend limit
  mid-survey, the main session finished the investigation inline with
  ctx — the index substituted for a subagent fleet.
- Init is cheap (hub, the largest repo: ~13 s cold; warm queries
  ~40 ms) and lazy staleness sweep worked — no manual sync anywhere.

## What didn't — adoption (the dominant failure)

- **~1 organic query use in ~14 post-rollout sessions** across the 7
  repos indexed at 2026-07-20 21:45. hub — the largest index — had
  three sessions and zero uses.
- **Zero subagent ctx invocations, in every repo, ever** (verified
  across all subagent transcripts). All 15 budget_analysis drain
  subagents (workers, critics, verifiers) used Read/Grep on
  finmodel.py — in the same repo where the main session's breakdown had
  just demonstrated the ctx pairing. One session's subagents ran a
  near-identical `grep -n "^func [A-Z]..."` package inventory 4 times
  (each = `ctx tree` of one package).
- **Ad-hoc one-line prompt hints had 0% compliance.** fooszone
  4ec3f264 and 5e9490ab dispatched 6 worker prompts containing "For
  structure questions prefer `ctx` (ctx tree/sig/refs) over reading
  whole files"; those workers ran 0 ctx commands and 99–124 greps. No
  drain/build/breakdown/critique template mentions ctx at all
  (verified: 0 hits in those skills' files).
- **No `Bash(ctx *)` permission entry exists** in any of the 8 indexed
  repos' `.claude/settings*.json` nor user-level settings. The critic
  agent's tool list (Read/Grep/Glob/git) cannot run ctx at all; the
  scout agent's grant gap is already owned by
  specs/ctx-skill-token-doctrine R5.
- **Worker worktrees are index-cold**: `.context/cache/` is gitignored,
  so each worktree inherits only `.context/.gitignore` (live-verified
  in an active ~/claude worktree) and pays the full cold index lazily.
- **Scale of the miss**: ~300 definition/reference/import-hunt greps
  post-availability map 1:1 onto tree/sig/refs/deps; widening-context
  chains (3 greps per symbol was the norm) and serial slice-reads
  (apiProvider.tsx read in 5 slices) were the recurring shapes. Worst
  session (~/claude 9edddd37): ~80–150 collapsible tool calls and 200+
  file reads across 76 subagents.
- **Even ctx work didn't dogfood ctx**: the sessions draining
  ctx-absence-check/ctx-cujs and writing grep-vs-ctx doctrine navigated
  ~/claude (indexed, 7 MB index on disk) by grep throughout.
- **notes never used anywhere** — the "persistent models of the
  codebases" goal from the rollout ask has no adoption at all.
- **Skill auto-triggered 0 times**; invoked via the Skill tool exactly
  twice, both times after explicit user instruction (owned by
  token-doctrine R1; recorded here for the baseline).

## What didn't — CLI/docs (residual, not owned by earlier specs)

- **Docs↔binary drift, both directions.** The rollout session's FIRST
  query failed: `ctx map --limit 5` → `error: unexpected argument
  '--limit'` (binary flag is `--tokens`; the one typo is owned by
  ctx-cujs/tasks/02). Reverse direction: the skill's scope caution
  says extractors cover "NOT rust", but `ctx tree context-tree/src`
  returns full Rust symbol outlines (live 2026-07-21); and
  `tree --depth/--limit/--doc`, `refs --limit`, `map --doc`,
  `--no-sync` all exist undocumented — the survey session hand-rolled
  `awk '/^tests/'` pipelines and parallel `find` runs to approximate
  output shaping the flags partly provide. No mechanical check exists.
- **Silent empty results.** `ctx refs possessionAnalyzer` (module
  symbol, 0 refs) and `ctx deps <file> --reverse` (0 importers) print
  nothing with exit 0 (live-reproduced 2026-07-21). Distinct from
  absence-check's no-match (resolution failure) and dead-code-zones'
  filter tails; unowned before spec ctx-output-shape-gaps.
- **No files-only listing mode**: `--depth 1` still interleaves
  symbols under each file header; "list the test files" needed awk +
  find cross-checks (tree line counts ≠ file counts).

## Ops notes (owned elsewhere, recorded for completeness)

- The rollout's ctx-init commits were transiently reverted twice by
  concurrent drain orchestrators riding stale git indexes
  (portfolio-tracker 17b0075, automation 510813e); postmortem in
  automation's docs/memory/drain-headless-runs.md. Root cause is
  drain's same-branch dual-checkout, not ctx.
- fooszone was initially excluded from the rollout but got
  `ctx init` + CLAUDE.md wiring mid-session on 2026-07-20 (5e9490ab);
  all 8 active repos are now indexed.
- Session/transcript ids for every claim above: fooszone
  {cfd7ce8f, 5e9490ab, 4ec3f264, 662df14f}, home {010cb127 (rollout),
  35b223ab, 9af5aab2, f9e7b72b}, budget-analysis 81640ded, hub
  {ce87362a, 8cd6b7e4}, portfolio-tracker {263ced16, eb538251},
  ~/claude {9edddd37, 5fdf5912, 2a4d6254}, under
  ~/.claude/projects/<project-dir>/.
