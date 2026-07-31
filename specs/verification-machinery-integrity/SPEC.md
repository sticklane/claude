Priority: P0
Breakdown-ready: false

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
under Codex) and falls back to mtime only when that inventory is unavailable,
saying so. Both `bin/janitor` and `bin/drain-release-worktrees` call it, which
also removes their incompatible windows — 1440 minutes and 5 minutes today for
the same question.

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
   default lives with the helper.
3. **R3**: a worktree whose branch was just gated by the calling process is not
   reported live on that basis alone. Concretely: releasing a branch
   immediately after running the canonical gate inside its worktree releases
   it, which is the `agentic-j7rw` failure.
4. **R4**: `tests/test_status_cutover.sh` no longer reads the live bd database.
   It compares against a fixture or a single snapshot taken inside the test, so
   a concurrent `bd` write cannot change its verdict.
5. **R5**: a lint refuses a test suite that reads shared machine or repository
   state — the live bd database, a machine-wide `pgrep -f`/`pkill -f`, or the
   repository's real `.beads/`, worktrees, or `HUMAN.md` — unless that suite is
   marked `serial` in its inventory row with a stated reason.
6. **R6**: the lint itself demonstrably fails. It exits nonzero against a
   deliberately non-isolated fixture suite, proving it can detect the pattern
   rather than merely running.
7. **R7**: `scripts/inventory-core-surface.py` permits a fragment to supersede
   an identity classified in another fragment, matching the
   fragment-supersedes-BASELINE path it already allows.
8. **R8**: the test inventory gains a retirement value in its disposition
   vocabulary, so a deliberately removed test is representable without deleting
   its row and its fragment.
9. **R9**: every pin or freeze diagnostic names its remedy. The git-blob-pin
   mismatch says the fragment must be introduced in final form and the branch
   rebuilt; the frozen-content-drift diagnostic says which supersession path
   applies.
10. **R10**: bd issue `agentic-nac2` (`bin/spec-gate`) carries a recorded
    requirement that a criterion is accepted only when it demonstrably fails
    against a deliberately broken target. This spec does not implement
    `spec-gate`; it records the requirement on that issue.

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
- [ ] A5 (cheap): `bash tests/test_status_cutover.sh` — passes while a concurrent `bd create` runs against the live database. Covers R4. (L2)
- [ ] A6 (cheap): `bash bin/check-test-isolation` — exits 0 against the repository's own suites. File absent today, verified 2026-07-30. Covers R5. (L2)
- [ ] A7 (cheap): `bash tests/test_check_test_isolation.sh` — passes, and includes a case asserting the lint exits NONZERO against a fixture suite that reads live bd and a fixture suite that issues a machine-wide `pkill -f`. Covers R6 — this is the prove-it-can-fail property, so a lint that always exits 0 fails this criterion. (L2)
- [ ] A8 (cheap): `bash tests/test_inventory_supersession.sh` — passes, asserting a fragment supersedes an identity classified in another fragment, and that a genuine duplicate identity with no supersession marker still errors. Covers R7. (L2)
- [ ] A9 (cheap): `bash tests/test_check_inventory.sh` — passes, including a case that retires a test through the new disposition without deleting its row. Covers R8. (L2)
- [ ] A10 (cheap): `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json` — exits 0, and the repo's existing inventories remain valid under R7's change. **This criterion already passes today (verified 2026-07-30, exit 0) and is deliberately a regression guard, not a new bar**: R7 loosens a duplicate-identity error, and the risk it carries is that existing inventories stop validating. Stated explicitly so it is not mistaken for evidence of new work — the same annotation discipline `docs/memory/anchored-acceptance-criteria.md` requires of any criterion whose expected result matches today's. (L2)
- [ ] A11 (cheap): `bash tests/test_inventory_diagnostics.sh` — passes, asserting the git-blob-pin mismatch and frozen-content-drift diagnostics each contain a remedy clause naming the action to take. Covers R9. (L2)
- [ ] A12 (cheap): `bd show agentic-nac2 --json` — its description or a comment records the prove-it-can-fail requirement verbatim. Covers R10. (L1; depth ceiling: this spec deliberately does not implement `spec-gate`, so the behavioural complement is `agentic-nac2`'s own acceptance.)
- [ ] A13 (cheap): `bash scripts/check.sh` — green, 0 FAIL lines, run with no concurrent `bd` writes. End-to-end.

## Open questions

None.
