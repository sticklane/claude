# Task 04: admission.py — lease-claim CAS + two-level cross-spec cap module

Status: in-progress
Depends on: specs/drain-frontier-scanner/tasks/01-scanner-and-tests.md
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (requirements R1, R2, R4, R5, R6, R12, R13, R14, R17)
Touch: .claude/skills/drain/admission.py, .claude/skills/_shared/touch_disjoint.py

## Goal

Round-10 revision: this task no longer writes a bash simulation. Instead it
extracts the greedy footprint-disjointness spec-claim check (R1), the
task-level two-level admission cap (R2), and the `DRAIN-OWNER.md` git-CAS
lease-claim protocol (reference.md's existing claim algorithm, mechanically
unchanged) into a real, authoritative Python module —
`.claude/skills/drain/admission.py` — following the same live-invocation
pattern this repo already proves works (`.claude/skills/prioritize/SKILL.md:35`'s
`prioritize_scan.py` invocation).

**R14 composition (round-10 critique fix — the original wording was
infeasible and is corrected here):** `admission.py` consumes
`specs/drain-frontier-scanner`'s `drain_frontier.py` JSON output for what
that scanner actually emits — per-spec `dispatchable`/`admissible`/`blocked`
task lists and their Priority/unblocking-power/lexicographic ordering — so
it never re-derives dependency resolution or per-spec window arithmetic.
It does **NOT** source R1's cross-spec Touch-footprint data from that JSON
(`drain_frontier.py`'s schema carries only path/priority/tie-break
rationale, no per-task `Touch:` sets). Instead, `admission.py` reads each
candidate spec's dispatchable-task `Touch:` headers directly — the same
on-disk source `drain_frontier.py` itself reads — and computes per-spec
footprint unions and pairwise cross-spec disjointness via a new shared
helper, `.claude/skills/_shared/touch_disjoint.py` (this repo's existing
`_shared/` convention alongside `headers.py`/`viz.py`/`spec_readiness.py`),
so this task does not ship a second, independently-maintained copy of
glob-prefix Touch-disjointness logic that could silently diverge from
`drain_frontier.py`'s own internal comparison. `drain_frontier.py` itself is
NOT required to adopt this helper by this task (out of this task's Touch);
it exists so a future change can converge the two.

This task builds the module, the shared helper, and their own unit tests
(deterministic, no concurrency) only. The genuinely concurrent test lives
in task 05, which depends on this task. The live-execution rewiring
(SKILL.md/reference.md invoking this module) lives in task 06, which also
depends on this task.

## Touch

Only `.claude/skills/drain/admission.py`,
`.claude/skills/_shared/touch_disjoint.py`, and their unit-test files (e.g.
`.claude/skills/drain/test_admission.py`,
`.claude/skills/_shared/test_touch_disjoint.py` — covering this task's own
deterministic-logic acceptance criteria, distinct from task 05's concurrency
test file). Do not touch `.claude/skills/drain/{SKILL.md,reference.md}`
(task 06's scope), `.claude/rules/token-discipline.md` (task 02's scope),
the mirror/plugin files (task 03's scope), or `drain_frontier.py` itself
(owned by `specs/drain-frontier-scanner`).

## Steps

1. Read ../SPEC.md's Requirements R1, R2, R4, R5, R6, R12, R13, R14 in full,
   and read `specs/drain-frontier-scanner/tasks/01-scanner-and-tests.md`'s
   landed `drain_frontier.py` CLI interface (spec-dir args, `--window`,
   `--claimed`, JSON output fields `dispatchable`/`admissible`/`blocked`/`diagnostics`
   — no `Touch:` field) — confirm what `admission.py` can and cannot source
   from it before writing anything.
2. **Pin the predicate verbatim (round-10 critique fix, confidence 70):**
   `touch_disjoint.py` MUST implement the exact same algorithm
   `specs/drain-frontier-scanner/SPEC.md` R1 already specifies for
   `drain_frontier.py`'s own internal Touch-disjointness check — "normalize
   each entry to its literal prefix up to the first glob metacharacter; two
   entries conflict when either prefix is a prefix of the other; ambiguity
   resolves to 'not disjoint' (conservative)." A different resolution of the
   ambiguous case (e.g. defaulting to "disjoint") would let `admission.py`
   co-claim two specs `drain_frontier.py`'s own logic would treat as
   colliding — the exact cross-spec hazard this whole spec exists to
   prevent — even though the two scripts are never required to share code
   (R14's shared-helper convergence is optional, not this task's scope).
   Write failing unit tests first for `touch_disjoint.py`: given two specs'
   dispatchable-task `Touch:` header sets (read from fixture task files, not
   a live `drain_frontier.py` invocation), assert the glob-prefix
   disjointness predicate correctly identifies disjoint vs. overlapping
   footprints, AND include a dedicated fixture case exercising the
   ambiguous branch specifically (e.g. one entry's literal prefix is itself
   a prefix of the other's, with no unambiguous conflict or clearance either
   way) asserting it resolves to "not disjoint" — the conservative
   direction — never "disjoint". Confirm the tests fail before any
   implementation exists.
3. Implement `touch_disjoint.py`'s footprint-union and pairwise
   disjointness predicate as plain Python, reading `Touch:` headers from
   task files directly, implementing the pinned algorithm from step 2
   exactly (prefix-normalize, prefix-of-either conflicts, ambiguity → not
   disjoint).
4. Write failing unit tests for `admission.py` (`test_admission.py`): a
   fixture of 4 specs (3 mutually Touch-disjoint, plus a 4th overlapping one
   of them), each with dispatchable tasks (fixture `drain_frontier.py`-shaped
   JSON for the dispatchable/admissible/blocked lists, plus fixture task
   files on disk for `touch_disjoint.py` to read `Touch:` headers from).
   Confirm the tests fail before any implementation exists.
5. Implement the greedy footprint-disjointness spec-claim algorithm (R1,
   using `touch_disjoint.py`) and the task-level two-level admission cap
   (R2) as plain Python, consuming fixture `drain_frontier.py`-shaped JSON
   for dispatchable/admissible sets.
6. Implement the `DRAIN-OWNER.md` git-CAS lease-claim protocol as callable
   functions — read-check-write-commit-push-reread-confirm — matching
   reference.md's existing algorithm (absent → claim; FRESH → refuse unless
   baton lineage; ALL STALE → reclaim) exactly, mechanically unchanged, just
   expressed as code instead of hand-executed prose.
7. Assert fixture cases (a) and (b): all 3 mutually-disjoint specs admit
   simultaneously up to the cap (R1/R4); the 4th, overlapping spec is
   excluded from concurrent admission with its collision partner — only one
   of the colliding pair is ever admitted at a time (R5).
8. Add the degenerate-case fixture per R4: a 1-spec queue yields exactly 1
   claim, with no behavioral perturbation versus the single-spec path.
9. Assert fixture cases (c) and (d): two Touch-disjoint tasks in different,
   both-claimed specs (neither sharing a `Group:` line) both admit
   simultaneously (R2's cross-spec co-admissibility); two ungrouped tasks
   from the SAME spec, with no in-flight tasks in any other claimed spec,
   still do NOT co-admit, while an ungrouped task in one spec DOES admit
   while a task from a different spec is in flight — together proving
   "window empty" is scoped per-spec, not global.
10. Assert fixture case (e), the two-level cap throttle: 3 mutually-disjoint
    specs each offering 5 pairwise-disjoint-with-each-other dispatchable
    tasks (15 total candidates) — assert exactly 10 are admitted, and that
    no single spec is ever admitted more than its own `W` (≤5) worth of
    tasks. This is a deterministic, single-process assertion — the ≤10
    global cap is single-orchestrator in-memory bookkeeping (round-10
    critique finding: it is NOT tested via multiprocessing anywhere in this
    spec, since there is no persisted shared state to race against and Out
    of scope forbids inventing one; this case (e) is the sole test of the
    cap).
11. Confirm `admission.py` fails loudly (non-zero exit, clear error) if the
    `drain_frontier.py`-shaped JSON it's given for dispatchable/admissible
    sets is absent or malformed — never silently falling back to a
    duplicate re-derivation of dependency/window logic (R14's negative
    constraint on THAT part of the composition only — Touch-footprint
    computation is always done directly via `touch_disjoint.py`, per the
    corrected R14, so there is no "fallback" case for that half).

## Acceptance

- [ ] `test -f .claude/skills/drain/admission.py` and `test -f
.claude/skills/_shared/touch_disjoint.py` → both exist (absent today,
      verified 2026-07-19)
- [ ] `python3 .claude/skills/_shared/test_touch_disjoint.py` → exits 0
- [ ] `python3 .claude/skills/drain/test_admission.py` → exits 0
- [ ] The `test_admission.py` file contains distinct, separately-asserted
      fixture cases (a)–(e) as described in Steps 7–10 — not a single
      combined assertion that could pass with only some cases actually
      implemented. Runnable form: on success the test's stdout names each
      case it asserted (`python3 .claude/skills/drain/test_admission.py |
grep -co 'case [a-e]'` → 5; the file does not exist today, so this
      cannot pass vacuously)
- [ ] A unit test asserts `admission.py` errors (non-zero exit) when given
      fixture `dispatchable`/`admissible` input that doesn't match
      `drain_frontier.py`'s documented JSON schema, rather than silently
      re-deriving its own per-spec window logic (R14's negative constraint)
- [ ] A unit test in `touch_disjoint.py`'s own test file asserts its
      disjointness predicate reads `Touch:` headers directly from fixture
      task files (not from any `drain_frontier.py` JSON field), confirming
      the corrected R14 composition boundary is actually implemented as
      specified, not silently reverted to the original (infeasible) design
- [ ] A dedicated unit test in `touch_disjoint.py`'s own test file exercises
      the ambiguous-prefix case (step 2's pinned fixture) and asserts it
      resolves to "not disjoint" — round-10 critique fix (confidence 70):
      pins `touch_disjoint.py` to the exact algorithm
      `specs/drain-frontier-scanner/SPEC.md` R1 already specifies for
      `drain_frontier.py`'s own internal check, so the two scripts cannot
      silently diverge on the conservative-ambiguity direction and
      co-admit a real cross-spec Touch collision
- [ ] A tech-debt entry is added to `docs/TASKS.md` noting that
      `drain_frontier.py` and `touch_disjoint.py` are two independent
      implementations of the same pinned algorithm (not sharing code by
      this task's design, per R14) and recommending a follow-up spec
      converge `drain_frontier.py` onto the shared `_shared/touch_disjoint.py`
      helper
