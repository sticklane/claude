# Task 09: cutover — bd becomes source of truth, old machinery deleted

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: test -f .claude/skills/work/SKILL.md && test -f hooks/bd-compliance/check.sh && echo "/work implemented - gate open" || echo "waiting: /work implementation (specs/beads-daily-skill, implemented directly per the 2026-07-22 maintainer direction - no tasks/ breakdown exists)"
Depends on: 05
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (Migration step 4; statement 9)
Touch: .claude/skills/, specs/status.sh, evals/, AGENTS.md, README.md, .claude-plugin/plugin.json, tests/test_drain_owner_protocol.sh, tests/test_drain_scheduler_window.sh, tests/test_status_cutover.sh

## Goal

bd is the source of truth. The four markdown-header readers —
`drain_frontier.py`, `list_specs.py`, `specs/status.sh`,
`prioritize_scan.py` — re-point onto bd (`bd ready --json`/`bd list`,
thin wrappers where display formatting warrants) or retire. Drain's
baton, lease (DRAIN-OWNER), and drain-handoff machinery are deleted;
drain/SKILL.md shrinks to judgment framing around the beads-daily flow
(a saved native workflow looping `bd ready`, per the 2026-07-22 pivot
addendum in ../SPEC.md). Evals assert the bd-backed flow instead of
prose-procedure behavior. AGENTS.md's Commands/State
sections and README describe the new commands. plugin.json version
bumps.

## Touch

Markdown task headers become generated output after this task — the
shadow sync direction reverses (bd→markdown display, or headers freeze
with a pointer). The general-session /handoff skill is retained; only
drain's own baton/lease/handoff paths are deleted.

## Steps

1. Re-point or retire each reader; every replacement keeps its consumers
   working (status.sh callers, workboard).
2. Delete DRAIN-BATON/DRAIN-OWNER writing and reading paths, the
   flip-commit grep recovery, and the drain generation counters; rewrite
   drain/SKILL.md around the beads-daily saved workflow inside its
   existing launch framing. Delete or rewrite the tests that exercise the deleted
   machinery (`tests/test_drain_owner_protocol.sh`,
   `tests/test_drain_scheduler_window.sh`) in the same commit — the
   suite must be green AFTER the deletion, not around it. Add
   `tests/test_status_cutover.sh` asserting `specs/status.sh` totals
   equal the `bd ready --json` count plus the non-ready statuses it
   reports from `bd list --json`.
3. Update evals/drain to drive the loop; update AGENTS.md and README;
   bump plugin.json version (compare against this task's base commit,
   not a hard-coded literal).
4. Run the full check suite and the drain evals.

## Acceptance

- [ ] `bash tests/test_status_cutover.sh` → prints `CUTOVER OK` (computed equality between status.sh totals and bd's counts — an assertion, not a recording)
- [ ] `grep -rn "DRAIN-BATON\|DRAIN-OWNER" .claude/skills/ tests/ | wc -l` → `0` (machinery AND its tests gone)
- [ ] `bash evals/run.sh drain 2>/dev/null || bash evals/drain/01-rolling-window/assert.sh` → the updated drain eval passes against the bd-backed flow
- [ ] `bash -c 'base=$(git merge-base HEAD origin/main); git show $base:.claude-plugin/plugin.json | grep version | diff - <(grep version .claude-plugin/plugin.json) >/dev/null && echo UNBUMPED || echo BUMPED'` → `BUMPED`
- [ ] `bash scripts/check.sh` → green

Depth ceiling: L1 for the AGENTS.md/README currency criteria — doc
accuracy is a human read; the behavioral complement is the verifier
running each documented command verbatim and confirming its output
matches the doc's claim.
