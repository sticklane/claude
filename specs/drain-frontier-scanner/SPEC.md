# Drain frontier scanner: deterministic dispatch frontier from task headers

Status: open
Breakdown-ready: true

## Problem

Drain's dispatch decision — which tasks are unblocked, in what order,
co-admissible under window W — is re-derived by the model in context on
every cycle (`.claude/skills/drain/SKILL.md`: read headers, compute
Priority → unblocking-power → lexicographic order, judge Touch-disjoint
admission), even though the inputs are all machine-parseable text:
`Status`/`Priority`/`Depends on` already parse via
`.claude/skills/_shared/headers.py` today, while `Touch:` disjointness
and `- Group:` co-admissibility are new deterministic parsing this
scanner adds. This costs real money — the
2026-07 profile (`specs/archive/drain-wake-cost/EVIDENCE.md`) measured
57% of total spend on the orchestrator main line and ≈$3.50 per verdict
at the median rewrite context — and real defects:
`docs/memory/drain-dispatch-lessons.md` logs a recurring queue-state
incident class (per-spec vs global Touch-disjointness, group
co-admissibility, flip-commit grep shape). The same evidence file shows
text-only discipline fixes underperform structural enforcement (the
baton prose fix did not reduce reprime pileup). The Beads DAG-backend
evaluation (`docs/external-playbooks.md`) was declined, but named
"recurring queue-state defects" as an explicit revisit trigger — that
trigger is now met. The adopted orchestration axis
(`docs/decisions/orchestration.md`: the script owns the loop and gates,
the model owns decisions on intermediate results) already prescribes
where this logic belongs; the frontier computation is the one gate still
living model-side.

## Solution

Keep task files as the sole source of truth (files-as-state is
load-bearing for resume, diffability, and the port chain — this spec
adds no database and no new state). Add a read-only, stdlib-only scanner
`.claude/skills/drain/drain_frontier.py` that loads
`.claude/skills/_shared/headers.py` via the same importlib bootstrap as
`list_specs.py`, reads one or more spec dirs' task headers plus
`## Parallelization` `- Group:` lines, and emits a JSON frontier report.
Drain's inventory step invokes it and treats its output as authoritative
for the dispatchable set and ordering; the model keeps every judgment
call it has today (verdict handling, deferral, BLOCKED routing,
lease/baton, merges). This is the same class of helper as
`list_specs.py` — a read-only script an already-authorized run invokes —
so it adds no new launch surface and needs no gating
(docs/human-gates.md governs launches, not a launched run's tools).

## Requirements

- R1: `drain_frontier.py` emits JSON to stdout with: `dispatchable`
  (ordered task entries — path, priority, and the tie-break rationale),
  `admissible`, `blocked` (task + unmet deps or typed `Unblock:` line),
  and `diagnostics`. Read-only; stdlib-only; deterministic output
  ordering; takes spec-dir paths, `--window N`, and `--claimed
<task-path>...` (the in-flight tasks whose `Touch:` lists form the
  current claim set) as arguments.
  - Field semantics, pinned: `dispatchable` is the FULL ordered set of
    tasks with `Status: pending` and every dependency `done`,
    regardless of Touch collisions; `admissible` is its windowed
    subset (`dispatchable ⊇ admissible`), and `--window N` truncates
    `admissible` only — `dispatchable` is never truncated. A
    dispatchable task kept out of `admissible` by a Touch collision
    with `--claimed` stays in `dispatchable` (it is not `blocked`,
    which remains deps/`Unblock:`-based). The scanner does NO
    live-slot arithmetic: `--claimed` filters Touch collisions only,
    never subtracts window slots, and `--window N` caps the returned
    candidate-list length for reporting — drain alone owns the final
    admit count against live slots, because only drain's window
    membership distinguishes a live worker (occupies a slot) from a
    suspected zombie (claim retained, slot released, per
    reference.md's zombie rule). An R2 test pins this: with a
    non-empty `--claimed`, `admissible` still has length
    `min(N, candidates)` — never `N - len(claimed)`. Likewise for
    structure, not just count: the scanner computes the
    ungrouped-runs-alone / co-admissibility shape from an EMPTY-WINDOW
    assumption; drain applies the actual live-window gate — emptiness
    and co-admissibility with live in-flight workers — exactly as it
    owns the admit count, since only drain knows which claims are live.
  - `admissible` implements drain's existing admission contract with
    the authority's own structure (`.claude/skills/drain/reference.md`,
    Rolling-window admission — the authority; restated here only to
    bind the JSON field): co-admissibility is the `- Group:` predicate
    alone — two tasks are co-admissible iff a single `- Group:` line
    names both, and a task on no `- Group:` line runs alone, admitted
    only when the window is empty; SEPARATELY, every admitted task's
    `Touch:` must be disjoint from the in-flight claim set
    (`--claimed` plus tasks already admitted this pass). Windows are
    per-spec, never interleaved across specs (today's behavior;
    interleaving is a future spec).
  - Invocation scope: drain invokes the scanner once per spec dir,
    matching its sequential walk — so a malformed header's non-zero
    exit disables the frontier for that spec only, and the multi-dir
    argument form exists for reporting callers, not drain.
  - Touch-disjointness predicate for glob entries: normalize each
    entry to its literal prefix up to the first glob metacharacter;
    two entries conflict when either prefix is a prefix of the other;
    ambiguity resolves to "not disjoint" (conservative, per the
    per-spec lesson in docs/memory/drain-dispatch-lessons.md).
  - `Depends on:` grammar: within-spec task numbers and cross-spec
    task-file paths (the two forms breakdown and specs/QUEUE.md
    define). A dependency pointing outside the scanned spec set is
    unresolved: the task goes to `blocked` with reason
    `unresolved-external-dep` in `diagnostics` — never guessed done.
  - Parse semantics: a missing `Status:` defaults to `pending` and a
    missing `Priority:` to P2 (the existing scanner conventions),
    each recorded in `diagnostics` with exit 0; a _present but
    malformed_ mandatory header (unrecognized `Status:` value,
    unparseable `Depends on:` reference) exits non-zero with the
    defect named on stderr, since a wrong frontier is worse than no
    frontier.
- R2: `test_drain_frontier.py` beside it (same `python3 <file>` unittest
  convention as `test_list_specs.py`: unit-test fixtures are built in
  temp dirs; the ONE committed golden fixture lives at
  `.claude/skills/drain/fixtures/` — NEVER under real `specs/`, where
  drain's no-arg queue walk and list-specs would treat its pending
  tasks as live work), with fixture-driven cases
  encoding the pinned ordering triple and the logged incident classes:
  dependency gating on non-`done` deps; Priority then unblocking-power
  then lexicographic tie-break; Touch-disjointness enforced per-spec,
  not globally (docs/memory/drain-dispatch-lessons.md); `- Group:`
  co-admissibility including the ungrouped-runs-alone rule; collision
  with a `--claimed` in-flight set; the glob prefix-overlap predicate
  (overlapping, non-overlapping, and ambiguous-conservative cases); an
  unresolved cross-spec dependency landing in `blocked`; defaulted
  missing headers exiting 0 with diagnostics vs a malformed `Status:`
  exiting non-zero; window truncation at W; `blocked`/`deferred`/
  `needs-verification` exclusion from `dispatchable`.
- R3: drain consumes the scanner at every point the frontier is
  currently model-derived — not only SKILL.md's inventory step but also
  step 2's tie-break prose and `reference.md`'s Rolling-window
  admission section, each rewritten to defer to the scanner's output
  (the existing "drain computes the order; the model never reorders"
  contract, now structurally enforced rather than asserted in three
  places). Explicit fallback: script missing or exiting non-zero → the
  current header-reading procedure verbatim, with the scanner's stderr
  diagnostics quoted in the drain log line that records the fallback —
  so gate-closed or partial installs keep today's behavior and a parse
  failure is surfaced, not swallowed.
- R4: one trajectory assertion in the drain evalset: an `assert.sh`
  greps `$EVAL_TRANSCRIPT` for a `drain_frontier.py` invocation
  (mechanism per `specs/trajectory-evals`), added to
  `evals/drain/01-rolling-window/` or a new scenario. The paid run is
  manual-pending (human-launched); the committed assertion is the
  drain-completable half.
- R5: mirrors and distribution: the antigravity drain workflow port
  receives the change with the divergence explicitly classified per
  `.claude/rules/mirror-procedure-discipline.md` (load-bearing if that
  runtime cannot invoke the script from its workflow — then it keeps
  the model-derived procedure with the fallback wording; incidental
  otherwise). The codex drain wrapper
  (`codex/.agents/skills/drain/SKILL.md`) is real content per CLAUDE.md
  and must carry the matching update in the same `Touch:`.
  `.claude-plugin/plugin.json` `version` is bumped;
  `tests/mirror-procedure-manifest.txt` gains a seeded phrase for the
  new procedure step targeting the CODEX mirror line only
  (`.claude/skills/drain/SKILL.md` |
  `codex/.agents/skills/drain/SKILL.md` | phrase), with the phrase
  pinned to the runtime-neutral bare token `drain_frontier` — never a
  path-bearing phrase, since codex legitimately re-roots paths and a
  path phrase would fail the gate on correct divergence. The codex
  wrapper carries the same invoke-with-fallback procedure text; whether
  the codex runtime actually resolves and runs the source-tree script
  is classified load-bearing-vs-incidental by the implementing task
  exactly as for antigravity, via `.claude/rules/mirror-verification.md`'s
  live cross-reference check (fallback-to-header-reading keeps a
  non-invoking codex correct either way). The seed never targets the
  antigravity workflow, whose divergence may be load-bearing per the
  classification above; seeding a source-present phrase against a
  legitimately divergent mirror would fail the coverage gate on
  correct behavior.

## Out of scope

- Any write path: the scanner never flips `Status:`, never claims
  leases, never commits. Drain remains the sole queue-state writer.
- Baton/relaunch bookkeeping, lease liveness, and verdict counting —
  model-side judgment, unchanged.
- Compiling the frontier into an ultra-path Workflow script — drain's
  existing gated ultra path may later consume the same JSON; not here.
- A DAG backend (Beads-style) — declined with rationale in
  docs/external-playbooks.md; this spec is the smaller remedy its
  revisit trigger points at.

## Acceptance criteria

- [ ] `python3 .claude/skills/drain/test_drain_frontier.py` exits 0,
      with at least one test per R2 incident class (R1, R2 — L2:
      exercises the scanner's behavior on fixtures).
- [ ] `python3 .claude/skills/drain/drain_frontier.py
.claude/skills/drain/fixtures/basic-window --window 2` emits JSON
      whose `admissible` set matches the fixture's documented
      expectation (R1 — golden-output check). The committed fixture
      lives under `.claude/skills/drain/fixtures/` ONLY — never under
      real `specs/`, whose queue walks would treat fixture tasks as
      live work; unit tests otherwise build fixtures in temp dirs per
      the `test_list_specs.py` convention.
- [ ] `grep -c 'drain_frontier' .claude/skills/drain/SKILL.md` ≥ 2 —
      the invocation and the fallback — and `grep -c 'tie-break is
computed by drain_frontier' .claude/skills/drain/SKILL.md` ≥ 1 —
      the mandated verbatim sentence in step 2's tie-break paragraph,
      so the count cannot be satisfied while step 2 still instructs
      model-side ordering — and `grep -c 'drain_frontier'
.claude/skills/drain/reference.md` ≥ 1 — the Rolling-window
      admission section deferring to the scanner (R3; all anchors 0
      today, verified 2026-07-19). Depth
      ceiling on these greps: procedure prose — the behavioral
      complement is R4's trajectory assertion (the scanner actually
      runs during a drain eval) plus R2's unit tests.
- [ ] `grep -rl 'drain_frontier' evals/drain/ | grep -q assert.sh`
      (R4 — committed half; the passing paid run is manual-pending,
      human-launched, per docs/memory/unattended-worker-tool-limits.md).
- [ ] `grep -c 'drain_frontier' codex/.agents/skills/drain/SKILL.md` ≥ 1
      and `grep -c 'codex/.agents/skills/drain/SKILL.md.*drain_frontier'
tests/mirror-procedure-manifest.txt` ≥ 1 and `bash
tests/test_mirror_procedure_coverage.sh` exits 0 — the seeded
      codex manifest line is present and the coverage gate stays green
      (R5); the antigravity port's divergence classification recorded
      in the task's evidence; closing commit modifies the plugin
      version line: `git show <closing-commit> --
.claude-plugin/plugin.json | grep -q '^+.*"version"'` (R5).

## Open questions

(none — the scanner is frontier-only (the `## Progress`/`## Deferred`
rollup stays model-written; it is cheap and rarely wrong), and windows
stay per-spec, both folded into R1 and Out of scope.)

## Parallelization

Task 01 (scanner + tests + fixture, TDD) is the foundation. Tasks 02
(drain SKILL/reference consumption) and 03 (eval trajectory assertion)
are disjoint in Touch and share no undecided design — the script name,
JSON fields, and assertion token are all pinned above — so they run
concurrently. Task 04 (mirrors + manifest + version bump) closes.
Group grammar per specs/drain-rolling-window/SPEC.md's Parallelization
section.

- Group: 02, 03
