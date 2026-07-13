Status: open
Priority: P2

## Problem

Three related gaps let stale environment/build/plugin state masquerade as a
real bug or a real failure, wasting check-cycles and burying genuine
failures under noise:

**1. Build/dist prerequisites live only in prose, never in a run command.**
In one monorepo, the same gotcha recurred in 6 of 7 sampled `/drain`
sessions: workers independently rediscover that the repo's check command
needs all package dists rebuilt first. The CLAUDE.md-documented dist-build
list was itself incomplete — two separate workers independently rediscovered
a missing package within a single session — and even the drain orchestrator
itself once merged a change without rebuilding its dist before gating,
producing a false pass that a later Stop-hook run caught as a real failure.
Root cause in this toolkit's own machinery: `bin/install-gates` detects and
renders only lint/typecheck/test stages into `scripts/check.sh`
(`CHECK_STAGES`/`STAGE_DESC`, `bin/install-gates:120-140`,
`templates/check.sh.tmpl`) — it has no concept of a build/install
prerequisite stage. That step, when a repo needs one, exists only as
CLAUDE.md prose a human or worker must remember to consult and keep
current — exactly the "doc list a human/worker must remember" pattern this
spec's requirements exist to eliminate. `/build`'s verify step (`.claude/
skills/build/SKILL.md`) and drain's merge step (`.claude/skills/drain/
SKILL.md`'s "run project gates" line, `.claude/skills/drain/reference.md:251`
"project gates green") both name gate-running only in the abstract, with no
explicit contract that dispatched workers and drain's own merge step must
run `scripts/check.sh` as the sole build+check entrypoint rather than
re-deriving steps from CLAUDE.md.

**2. Stale installed plugin cache silently enforces retired doctrine.** A
fix was verified against this toolkit's SOURCE repo, but the actually
INSTALLED plugin cache (`~/.claude/plugins/cache/agentic-toolkit/agentic/
<version>/`, per `bin/refresh-plugins`) still lacked it — a version-skew gap
between "fixed in source" and "what's actually running" that produced a
false failure report. Separately, an installed plugin was found 22 versions
behind dev HEAD, still enforcing a retired rule ("only humans promote
drafts") after that constraint had been relaxed upstream — directly forcing
a manual pipeline workaround in a sibling session that hit the same stale
rule. `bin/refresh-plugins` already exists as a manual remedy (run after
pushing, per its own header comment), but nothing detects staleness
proactively or warns before a session acts on doctrine that might already be
retired.

**3. The local Stop-hook gate re-runs the full check even for docs-only
edits, burying real failures under noise.** A 2-line docs-only edit (a
HUMAN.md update) triggered a full multi-workspace typecheck+lint+test run
via `templates/stop-gate.sh`, which unconditionally runs `scripts/check.sh`
with no path-based scoping; the real failure (disk at 100%, out of space)
was buried at the bottom under many pages of irrelevant per-package output
from unrelated packages. CLAUDE.md already states a `paths-ignore`
convention for **push-triggered CI** pipelines (`**.md`, `docs/**`,
`specs/**`, `.claude/**`) — that convention is unapplied to the LOCAL
Stop-hook gate, which has no equivalent.

## Solution

Three changes to this toolkit's own gate/dispatch machinery (general-purpose,
so every repo it's installed into benefits — not a one-off fix in the
monorepo where the evidence was gathered):

1. Add a build/dist prerequisite stage to `bin/install-gates`'s stack
   detection and `templates/check.sh.tmpl` rendering, so a repo that needs a
   pre-check build/install step gets it as a `run_stage` line in
   `scripts/check.sh` itself — a command that runs on every invocation,
   never a doc list. Make `/build`'s and drain's dispatch/merge procedures
   name `scripts/check.sh` as the sole required entrypoint (never a
   hand-derived CLAUDE.md step list) for both dispatched workers and drain's
   own merge-then-gate step.
2. Add a plugin-staleness check that compares the installed plugin's
   version against the source repo's `.claude-plugin/plugin.json` (or the
   marketplace's published version) and surfaces a warning — never a
   silent block — when they diverge, so a session doesn't unknowingly act
   on a stale cached doctrine.
3. Extend `templates/stop-gate.sh` (and `bin/install-gates`'s generation of
   it) to detect a docs-only diff since the last commit and skip or narrow
   `scripts/check.sh` accordingly, mirroring CLAUDE.md's CI `paths-ignore`
   convention for the local gate; and reorder `scripts/check.sh`'s failure
   reporting so a failing stage's output surfaces first/prominently rather
   than at the bottom of passing-stage noise.

## Research grounding

> the same gotcha recurred in 6 of 7 sampled drain sessions: workers
> independently rediscover that the repo's check command needs all package
> dists rebuilt first; the CLAUDE.md-documented dist-build list was itself
> incomplete — two separate workers rediscovered this omission within a
> single session — and even the drain orchestrator itself once merged a
> change without rebuilding its dist before gating, producing a false pass
> that a Stop hook later caught as a real failure.

> A fix was verified against this toolkit's SOURCE repo but the actually
> INSTALLED plugin cache still lacked it... a version-skew gap between
> "fixed in source" and "what's actually running"... an installed plugin was
> found to be 22 versions behind dev HEAD, still enforcing a retired rule
> ("only humans promote drafts")... directly forcing a manual pipeline
> workaround in a sibling session.

> A 2-line docs-only edit (a HUMAN.md update) triggered a full
> multi-workspace typecheck+lint+test run; the real failure (disk at 100%,
> out of space) was buried at the bottom under many pages of irrelevant
> per-package output.

`templates/check.sh.tmpl`'s header: "Runs the detected stack's stages in
order and exits non-zero on the first failure, printing that command's
output" — confirms today's generated check has no build/install stage and
no docs-only scoping.

CLAUDE.md's CI cost-discipline section: "`paths-ignore` for docs-only
pushes: `**.md`, `docs/**`, `specs/**`, `.claude/**` — baton-pass/spec
commits are the bulk of push traffic" (cited, not restated — this spec
extends the same convention to the local Stop-hook gate, which the cited
section does not cover).

## Requirements

R1. `bin/install-gates` gains detection for a repo-declared build/install
    prerequisite stage (e.g. a monorepo dist build), rendered into
    `templates/check.sh.tmpl` as a `run_stage` line that runs BEFORE the
    existing lint/typecheck/test stages whenever detected, so `scripts/
    check.sh` is self-sufficient and the CLAUDE.md doc list can drift
    without silently breaking gating. Detection heuristic and repo-opt-in
    mechanism (e.g. a marker file, a `package.json` script name, an
    explicit installer flag) are an implementation decision for whoever
    picks this up — record the choice in this SPEC.md or CLAUDE.md per this
    repo's Change Process convention, not left implicit in code.

R2. `.claude/skills/build/SKILL.md`'s verify step and `.claude/skills/drain/
    SKILL.md`'s merge-then-gate step (plus `.claude/skills/drain/
    reference.md`'s "project gates" language) are updated to state
    explicitly that `scripts/check.sh` is the sole required check
    entrypoint for both a dispatched worker's own verification and drain's
    own merge-time gate run — never a hand-derived list of steps read out
    of CLAUDE.md prose. `drain` and `build` are two of the four ultra-path
    skills (CLAUDE.md, "Testing changes") — any task implementing this
    requirement must run `bash evals/lint-ultra-gate.sh` before committing,
    and per CLAUDE.md's mirror-obligations paragraph, a SKILL.md-level
    wording change to either file must carry the matching `antigravity/`
    mirror update (and, since `drain`/`build` are two of the four codex
    real-content skills, the matching `codex/.agents/skills/{drain,build}/
    SKILL.md` update too) in the same task's `Touch:`.

R3. A plugin-staleness check compares the installed plugin's version
    (`.claude-plugin/plugin.json`'s `version` field as installed vs. the
    version at the source repo's current HEAD, or whatever mechanism this
    repo already uses via `bin/refresh-plugins`) at a natural checkpoint —
    session start, or before a session acts on doctrine that might have
    changed — and surfaces a warning (never a silent block, never an
    auto-refresh with side effects a user didn't request) when the
    installed version is behind source. Builds on the existing manual
    `bin/refresh-plugins` remedy; this requirement is the missing
    proactive-detection half.

R4. `templates/stop-gate.sh` (and `bin/install-gates`'s generation of it)
    detects a docs-only diff — every changed file since the last commit (or
    HEAD) matches CLAUDE.md's existing `paths-ignore` glob set (`**.md`,
    `docs/**`, `specs/**`, `.claude/**`) — and skips or narrows
    `scripts/check.sh` accordingly, applying the same convention CLAUDE.md
    already states for push-triggered CI to the LOCAL Stop-hook gate.

R5. `templates/check.sh.tmpl`'s `run_stage` failure reporting is reordered
    (or its aggregate runner is) so that when a stage fails, its output is
    surfaced first/prominently in the hook's stderr rather than appearing
    only after every prior passing stage's full output — `run_stage`
    already exits on first failure and prints only that stage's output
    (`templates/check.sh.tmpl`'s current behavior), so this requirement is
    about the CALLING context (e.g. a multi-workspace wrapper stage that
    itself runs several sub-checks and currently prints all of them before
    the failing one) not about `check.sh` itself if no such wrapper exists —
    confirm which shape applies during implementation and scope the fix to
    what's actually true of the target repo's check invocation.

## Out of scope

- No overlap found with any open `agentprof-*` or `codequality-*` spec —
  reviewed all six agentprof specs (antigravity-adapter, attribution-gaps,
  instrumentation, scrub-hex-tokens, cache-reprime-visibility is filed under
  the `cache-*` prefix) and both `codequality-*` specs' `## Problem`
  sections; they cover agentprof's parser/pricing/scrubbing, cache re-prime
  visibility in cost profiles, agent-console mutation test coverage, and
  antigravity content-parity/shared-header-parsing — none touch build/dist
  staging, plugin-version staleness, or Stop-hook path-scoping. No
  requirement in this spec is excluded on overlap grounds.
- Fixing the specific incomplete dist-build list in the monorepo where the
  evidence was gathered — that list lives in that repo's own CLAUDE.md, not
  this toolkit.
- A Gemini/Antigravity-native or Codex-native equivalent of the
  plugin-staleness check (R3) — Antigravity and Codex are live-file
  runtimes per CLAUDE.md's mirror-chain note (`bin/refresh-plugins`: "live-
  file runtimes... nothing to refresh there"), so R3's install/cache-version
  skew is a Claude-Code-plugin-cache-specific problem.
- Extending or modifying CLAUDE.md's push-triggered CI `paths-ignore`
  convention itself — R4 only extends the same idea to the local Stop-hook
  gate; the CI convention is unchanged.
- Redesigning `bin/install-gates`'s stack-detection architecture wholesale —
  R1 adds one new stage type to the existing detection/render pipeline, not
  a rewrite.

## Acceptance criteria

- `grep -c "build/dist prerequisite" bin/install-gates` → 0 today (verified
  this session); a task implementing R1 must raise it above 0.
- `grep -c "sole required check entrypoint" .claude/skills/build/SKILL.md
  .claude/skills/drain/SKILL.md` → 0/0 today (verified this session); a
  task implementing R2 must raise at least one of these above 0, and the
  corresponding `antigravity/.agents/skills/{build,drain}/SKILL.md` mirror
  must show the same phrase (codex is a symlink to antigravity for these
  two paths — confirmed via `codex/.agents/skills/{build,drain} ->
  ../../../antigravity/.agents/skills/{build,drain}` — so no separate codex
  edit is needed for R2 specifically, only the mirror check applies).
- `bash evals/lint-ultra-gate.sh` exits 0 after any commit touching
  `.claude/skills/{drain,build}/SKILL.md` under R2.
- `grep -c "plugin-staleness" bin/refresh-plugins .claude/skills/*/SKILL.md`
  → 0 today (verified this session); a task implementing R3 must raise it
  above 0 in whichever file ends up hosting the check.
- `grep -c "docs-only diff" templates/stop-gate.sh bin/install-gates` → 0
  today (verified this session); a task implementing R4 must raise it
  above 0.
- MANUAL: trigger the updated Stop hook on a repo with gates installed via
  a docs-only edit (e.g. a one-line HUMAN.md change) and confirm the full
  `scripts/check.sh` run is skipped or narrowed, not run in full.
- MANUAL: trigger the updated Stop hook on a repo with gates installed via
  a product-code edit and confirm `scripts/check.sh` still runs in full
  (R4 must not become a blanket skip).
- MANUAL: on a repo with a deliberately stale plugin cache (mismatched
  `.claude-plugin/plugin.json` version vs. installed), confirm the R3 check
  surfaces a warning rather than silently proceeding or hard-blocking.

## Open questions

- R1's detection heuristic for "this repo needs a build/dist prerequisite
  stage" is left as an implementation decision (see R1) — should
  `bin/install-gates` auto-detect it (e.g. a monorepo layout signal) or
  require explicit opt-in (a marker file or install-gates flag)? Auto-
  detection risks false positives across the wide variety of repos this
  toolkit is installed into; explicit opt-in requires a human or worker to
  discover and set it once. Whoever breaks this spec down should decide and
  record the choice rather than leaving it implicit in code.
- R5's premise (a multi-sub-check wrapper stage exists in some target
  repo's check invocation) was not directly verified against a live
  wrapper — the evidence describes symptoms consistent with one but this
  research pass did not locate the specific repo/script. The requirement is
  written to self-scope during implementation; flag DEFERRED if no such
  wrapper shape is found anywhere in scope.
