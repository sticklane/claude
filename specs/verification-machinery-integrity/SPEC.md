Priority: P0

# Verification machinery integrity

## Problem

The toolkit's checks and guardrails have a class of defect where a check
passes while verifying nothing, and where one guardrail defeats another. One
drain run on 2026-07-30 surfaced nine such defects and four vacuous checks.
None were caught by a gate; every one was caught by a human or a critic
reading carefully, and several cost a full re-run of a five-minute suite to
diagnose or a whole branch rebuild to clear.

Three root causes account for all of them. **Liveness is inferred from a
proxy**: `worktree_recently_active` (`bin/lib/worktree-classify.sh:48`) reads
file mtimes, and drain runs the canonical gate *inside* a worktree immediately
before releasing it, so the proxy reports every close-out target as live and
release no-ops. The real signal — the runtime's session inventory — appears
nowhere in code; `.claude/rules/concurrent-sessions.md` names it as prose only.
**Tests read shared state**: `scripts/check.sh:325` backgrounds every suite, so
a suite reading the live bd database or issuing a machine-wide `pkill -f`
observes and signals its siblings. **Pins have no escape**: a surface-inventory
fragment is bound to the blob of the commit that added it, a `retain` surface
classified in a fragment can never be reclassified because a fragment may
supersede the BASELINE but not another fragment
(`scripts/inventory-core-surface.py:798`), and the test inventory has no
retirement value at all in its `{retain, quarantine, manual}` vocabulary
(`scripts/check.sh:170`).

## Solution

Fix the three causes rather than the nine symptoms.

Liveness becomes one shared helper in `bin/lib/worktree-classify.sh` that asks
the runtime's session inventory first (`claude agents --json`; `list_agents`
under Codex). It returns three values, never two: **live**, **not-live**, and
**unknown**. When the inventory cannot be consulted the helper still reads
mtime, but the result it returns is `unknown` — the mtime reading is reported
as supporting detail, never promoted to a confident not-live. Both
`bin/janitor` and `bin/drain-release-worktrees` call it, which also removes
their incompatible windows — 1440 minutes and 5 minutes today for the same
question. Both callers treat `unknown` as live and skip, because the
destructive action is removal: the cost of skipping a dead worktree is one
stale directory, and the cost of releasing a live one is another session's
work.

Test isolation follows a pattern this repo already has but applies
inconsistently: `tests/test_sync_workflows.sh` and `tests/test_session_claims.sh`
take env overrides (`SYNC_WORKFLOWS_SRC`, `SESSION_FILE`) pointing at fixtures.
The suites that read live state adopt it, and a new lint stops a future suite
reintroducing the pattern.

Both inventories gain a supersession path, and every pin diagnostic states its
remedy instead of only reporting a mismatch.

Vacuity detection is **not** built here. `/idea`'s step 4 already carries the
authoring-time procedure and `specs/idea-anchored-criteria-authoring-check` is
done — yet four vacuous criteria were authored on 2026-07-30 while following
it, because a model-executed procedure is not a gate. The runnable gate is
already scoped as bd issue `agentic-nac2` (`bin/spec-gate`). This spec adds one
requirement to that issue rather than duplicating it.

## Requirements

1. **R1**: `bin/lib/worktree-classify.sh` exposes a liveness function that
   consults the runtime session inventory before any mtime reading, and returns
   a distinct third result when the inventory cannot be consulted — so
   "unknown" never collapses into "not live", the same three-value discipline
   `.claude/rules/human-blockers.md` already requires of blocker probes.
2. **R2**: `bin/janitor` and `bin/drain-release-worktrees` both decide liveness
   through R1's function. Neither computes its own idle window; a single
   default lives with the helper. **Both callers treat `unknown` as live and
   skip.** Removal is the destructive action, so an undecidable answer must
   never authorize it.
3. **R3**: when the session inventory IS successfully consulted and reports no
   owning session, a fresh mtime does not by itself make a worktree live —
   that combination releases it. This is the `agentic-j7rw` failure, where
   drain runs the canonical gate inside a worktree and the gate's own writes
   then read as a live owner. **R3 applies only on a successful inventory
   consult**; when the inventory is unavailable the result is `unknown` and R2
   governs, so mtime is never discounted while it is the only evidence
   available.
   The mechanism is a caller-passed exclusion, not inference: the caller that
   just ran the gate passes its own process group to the helper, and the
   helper disregards mtime changes attributable to it. A worker must not
   substitute a pre-gate mtime baseline, a marker file, or a time window —
   those are different failure modes and this requirement names one.
4. **R4**: `tests/test_status_cutover.sh` no longer reads the live bd database.
   It compares against a fixture or a single snapshot taken inside the test, so
   a concurrent `bd` write cannot change its verdict.
5. **R5**: a lint refuses a test suite that reads shared machine or repository
   state — the live bd database, a machine-wide `pgrep -f`/`pkill -f`, or the
   repository's real `.beads/`, worktrees, or `HUMAN.md`.
   The `serial` inventory marking is **not** an exemption for machine-wide
   signal patterns (`pkill -f`, `pgrep -f`): `serial` only orders suites within
   a single `scripts/check.sh` run, while a machine-wide signal reaches a
   concurrent drain worker or another session entirely, so it does not make
   that class safe. `serial` may exempt only live-bd reads, and only with a
   stated reason.
   The lint is registered in the test inventory so `scripts/check.sh` runs it,
   following the pattern `bin/check-token-discipline` uses via
   `tests/test_check_token_discipline.sh`. A lint that exists but never
   executes does not satisfy this requirement.
   `tests/test_status_cutover.sh` and `tests/test_human_blockers.sh` are
   isolated to fixtures, not merely marked — they are the two suites whose
   failures were measured on 2026-07-30.
6. **R6**: the lint itself demonstrably fails. It exits nonzero against a
   deliberately non-isolated fixture suite, proving it can detect the pattern
   rather than merely running.
7. **R7**: `scripts/inventory-core-surface.py` permits a fragment to supersede
   an identity classified in another fragment, matching the
   fragment-supersedes-BASELINE path it already allows.
8. **R8**: the test inventory gains a retirement value in its disposition
   vocabulary, so a deliberately removed test is representable without deleting
   its row and its fragment. `scripts/check.sh` dispatches on that value: a
   retired row is **not executed and not reported as a failure**, and its
   absent file is not a "inventoried test missing" error. Adding the value to
   the vocabulary without the runtime branch leaves a retired test still being
   run.
9. **R9**: every pin or freeze diagnostic names its remedy. The git-blob-pin
   mismatch says the fragment must be introduced in final form and the branch
   rebuilt; the frozen-content-drift diagnostic says which supersession path
   applies.
10. **R10**: bd issue `agentic-nac2` (`bin/spec-gate`) carries a recorded
    requirement, in exactly this sentence so a check can compare against it:

    > A criterion is accepted only when it demonstrably fails against a
    > deliberately broken target.

    This spec does not implement `spec-gate`; it records that sentence on that
    issue.

## Out of scope

Chosen by the author, not the interview — the exclusion question returned
unselected.

- **The registration gap** (`agentic-led9`) and the **unarchived completed
  specs** (`agentic-ugig`). Both were found while scouting this spec, but they
  are a missing pipeline step, not a defective check.
- **`bin/spec-gate`'s implementation** — `agentic-nac2` owns it. R10 adds a
  requirement to that issue and stops there.
- **janitor's dead handoff staleness check** (`agentic-bcuz`) — an
  IndentationError in an embedded heredoc, a plain bug with a one-line fix.
- **`bin/` and `scripts/` being unregisterable as inventory surfaces** —
  `discover_surfaces()` never scans them, so probes and entry points cannot be
  inventoried. Real, but a coverage gap rather than a broken check.
- **Retrofitting already-frozen surfaces.** R7 gives the mechanism; migrating
  the surfaces frozen before it existed is separate work.

## Acceptance criteria

Anchor checks run against on-disk state on 2026-07-30 and recorded inline.

- [ ] A1 (cheap): `grep -c 'worktree_owner_is_live' bin/lib/worktree-classify.sh` — at least 1. Phrase absent today, verified 2026-07-30 (`grep -c` → 0). Covers R1. (L0; depth ceiling: naming proves only the function exists — the behavioural complement is A2 and A4.)
- [ ] A2 (cheap): `bash tests/test_worktree_liveness.sh` — passes, asserting the runtime inventory is consulted before any mtime read, and that an unavailable inventory yields the third "unknown" result rather than "not live". Covers R1. (L2)
- [ ] A3 (cheap): `grep -c 'idle_minutes=' bin/drain-release-worktrees bin/janitor` — 0 in both. Each declares its own default today, verified 2026-07-30 (`bin/drain-release-worktrees:36` sets `idle_minutes=5`; `bin/janitor` carries `1440`). Covers R2. (L0)
- [ ] A4 (cheap): `bash tests/test_worktree_liveness.sh` — includes a case that gates a branch inside its worktree, then releases it, and asserts the worktree is removed. Covers R3, the `agentic-j7rw` failure. (L2)
- [ ] A5 (cheap): `bash bin/check-test-isolation tests/test_status_cutover.sh` — exits 0, proving the suite no longer reaches the live database. Deterministic by construction: it asserts the absence of a live-bd read rather than that one concurrent write happened to be survived, because a timing race can pass by luck and this spec's own subject is checks that pass without verifying. Covers R4. (L2)
- [ ] A6 (cheap): `bash bin/check-test-isolation` — exits 0 against the repository's own suites, **and** `grep -c '"serial": true' tests/inventory/*.json` returns no more than 2 (today: 1, verified 2026-07-30 — only `test_agentic_latency.sh`). The second clause exists because the first is otherwise satisfiable by marking every offending suite serial instead of isolating it. File absent today, verified 2026-07-30. Covers R5. (L2)
- [ ] A7 (cheap): `bash tests/test_check_test_isolation.sh` — passes, and includes a case asserting the lint exits NONZERO against a fixture suite that reads live bd and a fixture suite that issues a machine-wide `pkill -f`, and that marking the `pkill` fixture `serial` does NOT silence it. Covers R6 — this is the prove-it-can-fail property, so a lint that always exits 0 fails this criterion. (L2)
- [ ] A7b (cheap): `grep -c 'check-test-isolation' tests/inventory/*.json` — at least 1, so `scripts/check.sh` actually runs the lint. Phrase absent today, verified 2026-07-30 (`grep -c` → 0). Covers R5's registration clause; without it A13 is green while the lint never executes. (L1)
- [ ] A8 (cheap): `bash tests/test_inventory_supersession.sh` — passes, asserting a fragment supersedes an identity classified in another fragment, and that a genuine duplicate identity with no supersession marker still errors. Covers R7. (L2)
- [ ] A9 (cheap): `bash tests/test_check_inventory.sh` — passes, including a case that retires a test through the new disposition without deleting its row. Covers R8. (L2)
- [ ] A10 (cheap): `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json` — exits 0, and the repo's existing inventories remain valid under R7's change. **This criterion already passes today (verified 2026-07-30, exit 0) and is deliberately a regression guard, not a new bar**: R7 loosens a duplicate-identity error, and the risk it carries is that existing inventories stop validating. Stated explicitly so it is not mistaken for evidence of new work — the same annotation discipline `docs/memory/anchored-acceptance-criteria.md` requires of any criterion whose expected result matches today's. (L2)
- [ ] A11 (cheap): `bash tests/test_inventory_diagnostics.sh` — passes, asserting the git-blob-pin mismatch text contains `introduced in final form` and the frozen-content-drift text names its supersession path. Asserting the specific phrases, not "a remedy clause", because any string satisfies the latter. Covers R9. (L2)
- [ ] A12 (cheap): `bd show agentic-nac2 --json | grep -c 'demonstrably fails against a deliberately broken target'` — returns at least 1, matching R10's quoted sentence exactly. The sentence is pinned in R10 so this check can decide; "records it verbatim" with no canonical text lets two workers write two sentences and both self-certify. Covers R10. (L1; depth ceiling: this spec deliberately does not implement `spec-gate`, so the behavioural complement is `agentic-nac2`'s own acceptance.)
- [ ] A13 (cheap): `bash scripts/check.sh` — green, 0 FAIL lines, run with no concurrent `bd` writes. End-to-end.

## Open questions

None.
