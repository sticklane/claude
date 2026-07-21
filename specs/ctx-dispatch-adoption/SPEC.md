# ctx dispatch adoption: make the pipeline's agents index-first in indexed repos

Serves CUJ: all of docs/guides/ctx-cujs.md — this spec is about WHO runs
the queries, not what they return.

Breakdown-ready: true

## Problem

The 2026-07-21 cross-chat review (evidence/ctx-usage-review-2026-07-21.md)
measured post-rollout adoption: ~1 organic query use in ~14 main sessions
across the 7 repos indexed on 2026-07-20, and **zero subagent ctx
invocations anywhere, ever** — while ~300 definition/reference/import-hunt
greps that map 1:1 onto `ctx tree|sig|refs|deps` ran in the same window,
including 4 subagents in one session independently re-running the same
`^func [A-Z]` package inventory that one `ctx tree` answers.

The failure is structural, not doctrinal ignorance:

1. **Prompt hints don't survive dispatch.** Six ad-hoc worker prompts
   carried "For structure questions prefer `ctx` (ctx tree/sig/refs) over
   reading whole files"; compliance was 0% (0 ctx commands, 99–124 greps).
   No drain/build/breakdown/critique template mentions ctx at all.
2. **Agents can't run it.** No `Bash(ctx *)` permission entry exists in
   any indexed repo's `.claude/settings*.json`; the critic agent's tool
   list (Read, Grep, Glob, git-only Bash) physically cannot execute ctx.
   (The scout agent's identical gap is owned by
   specs/ctx-skill-token-doctrine R5 — NOT this spec.)
3. **Worktrees are index-cold.** `.context/cache/` is gitignored, so
   every worker worktree inherits only `.context/.gitignore`
   (live-verified) and pays the repo's full cold index lazily (hub:
   ~13 s) — or, in practice, just greps.
4. **Nothing measures adoption**, so doctrine changes (this spec,
   token-doctrine R1/R5/R6) can't be evaluated; today's baseline is 0.

Positive control: the one session that paired breakdown with ctx
(budget_analysis 35b223ab) wrote three task files from two `ctx tree`
calls with zero source reads — 45 minutes before 15 subagents in the same
repo Read/Grepped finmodel.py without a single ctx call.

## Seam with sibling specs

specs/ctx-skill-token-doctrine owns the ctx SKILL.md (trigger surface,
reading ladder), the scout agent (grant + prompt, R5), the /onboard
CLAUDE.md doctrine section (R6a), and the token-discipline rule (R6b).
This spec owns the surfaces those don't reach: dispatch templates,
non-scout agent grants, repo permission allowlists, worktree cache
warmth, and measurement. This spec does NOT edit the ctx SKILL.md and
therefore needs no slot in token-doctrine's SKILL.md editor registry.
Its one same-file seam: R3b edits /onboard's SKILL.md, which
token-doctrine R6a also edits (different sections) — the two tasks land
serialized, whichever is second rebasing on the first.

Intra-spec file sharing: R1, R4, and R6 all edit the drain/build skill
files (R1 + R4 both touch `.claude/skills/drain/` and
`.claude/skills/build/`; R6 touches build's SKILL.md). Breakdown must
emit these as ONE task or as explicitly serialized tasks — never
parallel work on the same files (concurrent-sessions collision rule).

## Requirements

- R1 — Worker dispatch stanza (drain + build). The worker dispatch
  prompt templates in `.claude/skills/drain/` and `.claude/skills/build/`
  gain a "Structure lookups (ctx)" stanza, emitted when the target
  checkout has `.context/` at its root: it names `tree`, `sig`, `refs`,
  `deps` (and `show` once specs/ctx-query-ergonomics lands — do not
  reference `show` before it exists) with one concrete example each, and
  states the rule as a procedure step, not a preference: "for a
  definition, caller, signature, or outline question, run the ctx query
  BEFORE any Grep/Read; fall back to Grep for content/text questions
  (bodies, literals, patterns) and Read a file only when about to edit
  it." The stanza is self-contained — dispatched workers do not have
  the ctx SKILL.md loaded, so it must not reference the reading ladder
  by name. Rationale for stanza-over-hint: the 0%-compliance evidence
  above. Acceptance: `grep -rl 'Structure lookups (ctx)'
  .claude/skills/drain/` returns ≥1 file AND `grep -rl 'Structure
  lookups (ctx)' .claude/skills/build/` returns ≥1 file (phrase
  confirmed absent from the repo today, grep -c = 0) — both directories
  independently, so the criterion cannot green on drain alone; the same
  literal greps succeed against the antigravity mirrors
  (`antigravity/.agents/workflows/drain.md` and `build.md` — verified
  to exist) and the codex legs (`codex/.agents/skills/drain/SKILL.md`
  and `codex/.agents/skills/build/SKILL.md` — real content, not
  symlinks), all confirmed absent today; and a
  `<source>|<mirror>|Structure lookups (ctx)` line is added to
  `tests/mirror-procedure-manifest.txt` (the manifest file itself —
  `tests/test_mirror_procedure_coverage.sh` is its reader, and it
  silently skips unlisted pairs, so the manifest line is the entire
  anti-re-drop protection) for each source→mirror pair, with the
  source field naming the specific file the stanza landed in;
  runnable check: `grep -c 'Structure lookups (ctx)'
  tests/mirror-procedure-manifest.txt` ≥4 (CLAUDE.md's "unlisted
  mirror silently ships un-mirrored" failure mode); the
  stanza is inside the dispatch-prompt
  template text, not a surrounding narrative section; mirror legs
  (antigravity + codex for drain/build) and plugin.json bump per
  CLAUDE.md's authoring conventions (cited, not restated).

- R2 — Breakdown structure gathering. `.claude/skills/breakdown/SKILL.md`'s
  structure-scouting step instructs: in an indexed repo, gather the
  symbol-level structure for task-file authoring via `ctx tree` (per
  module/file) and `ctx sig`/`ctx refs` (per touched symbol) before any
  scout dispatch or file read — citing the 35b223ab pairing as the model
  (task files written from outlines, zero reads). Acceptance:
  `grep -q 'ctx tree' .claude/skills/breakdown/SKILL.md` succeeds
  (confirmed 0 ctx mentions today) and the instruction is conditional on
  index presence; antigravity mirror + plugin.json per conventions.

- R3 — Grants and allowlists. (a) The critic agent
  (`.claude/agents/critic.md`) gains `Bash(ctx *)` in its tools
  frontmatter plus one prompt line containing the exact phrase
  "index-first: prefer ctx" directing it to run ctx queries for
  structure questions when the repo is indexed — a critic verifying a
  spec's symbol claims is exactly a refs/sig consumer, and the prompt
  line is the behavioral half (the grant alone changes nothing). The
  antigravity critic mirror (`antigravity/.agents/skills/critic/SKILL.md`)
  carries ONLY the prompt line in the same commit — antigravity skill
  mirrors have no `tools:` mechanism, so the grant is a load-bearing
  divergence per `.claude/rules/mirror-procedure-discipline.md`, never
  faked as prose — with the plugin.json bump per conventions. (b) The /onboard skill's permission-allowlist step —
  `.claude/skills/onboard/SKILL.md` §4 "Permissions" specifically, NOT
  the gate skill (gate owns hooks/deny rules, not the allowlist) — adds
  `Bash(ctx *)` to the recommended allowlist when the repo is indexed.
  (c) A rollout checklist task (may be executed by an attended session;
  the repos are outside this repo's Touch scope) adds `Bash(ctx *)` to
  the 8 indexed repos' `.claude/settings.json` allowlists, with the
  exact per-repo command written in the task. Acceptance: (a)
  `grep -q 'Bash(ctx' .claude/agents/critic.md` AND
  `grep -q 'index-first: prefer ctx' .claude/agents/critic.md` AND
  `grep -q 'index-first: prefer ctx'
  antigravity/.agents/skills/critic/SKILL.md` all succeed (all three
  literals confirmed absent from their targets today; the antigravity
  check is the prompt phrase, never `Bash(ctx` — see the requirement);
  (b) `grep -q 'Bash(ctx' .claude/skills/onboard/SKILL.md`
  succeeds (confirmed absent today — the file has zero ctx mentions);
  (c) checklist task exists with runnable commands and its Status
  reflects the attended-rollout path
  (docs/memory/unattended-worker-tool-limits.md pattern).

- R4 — Worktree cache warmth. The worktree-creation step in drain's (and
  build's, where it isolates) procedure copies the main checkout's
  `.context/cache/` into the new worktree when present — copy, never
  symlink: two writers on one SQLite file is a corruption risk — so
  workers start warm; absent a cache, behavior is unchanged (lazy
  build). Acceptance: the copy step appears in the drain worktree
  procedure text (`grep -q '.context/cache' .claude/skills/drain/` files;
  confirmed absent today); a live check — create a scratch worktree per
  the procedure in an indexed repo and assert
  `.context/cache/index.sqlite` exists in it — is scripted in the task;
  antigravity + codex mirror legs for the drain/build edits and the
  plugin.json bump per CLAUDE.md conventions (same obligation as R1 —
  a task landing R4 without R1 carries them itself).

- R5 — Adoption telemetry. agentprof reports per-session ctx usage:
  count of Bash tool calls whose command invokes `ctx
  <tree|sig|refs|deps|at|map|notes|show>` plus Skill-tool invocations of
  `agentic:ctx`, for sessions whose cwd resolves to an indexed repo.
  Baseline (this review): 0 outside the fooszone survey + rollout
  sessions. Acceptance: a Go test over fixture transcripts asserts (i)
  the counts for both invocation shapes in an indexed-repo session AND
  (ii) that a session whose cwd is NOT an indexed repo contributes zero
  to the metric even when its transcript contains ctx-shaped commands —
  the cwd→indexed filter is load-bearing, not decorative; the report
  surfaces the metric alongside existing skill attribution.

- R6 — Notes adoption nudge. /build's attended completion step gains:
  in an indexed repo, if this task surfaced a symbol-anchored fact
  meeting the code-comment bar (gotcha, invariant, rationale), offer
  `ctx notes add <symbol> ... --kind <kind>` before finishing. Evidence:
  notes — the mechanism for the rollout's stated "persistent models"
  goal — have zero uses to date. Acceptance: `grep -q 'ctx notes add'
  .claude/skills/build/SKILL.md` (confirmed absent today); mirrors +
  plugin.json per conventions.

## Non-goals

- The scout agent's grant/prompt and the ctx SKILL.md trigger surface
  (specs/ctx-skill-token-doctrine R5/R1).
- Any `ctx` binary change (sibling ctx-* specs own the CLI).
- Forcing ctx usage in unindexed repos or on content/text questions —
  the reading ladder's escalation rules stand.
- Fixing drain's same-branch stale-index commit clobber (recorded in
  the evidence file; owned by the drain hardening line of specs).

## Evidence

evidence/ctx-usage-review-2026-07-21.md (session ids for every claim).

Next stage: /critique (this SPEC.md), then /breakdown.
