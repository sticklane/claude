# Task 05: shadow-mode markdown→bd sync and live-queue import

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 03, 04
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (Migration step 2; statement 11)
Touch: agentic/shadow.py, tests/test_agentic_shadow.py, .beads/, .gitignore

## Goal

Shadow mode is live in this repo: `agentic shadow-sync` reads the
markdown task headers (Status, Depends on, Priority, Budget, Touch,
Rigor — the `_shared/headers.py` regexes) and one-way syncs them into
bd, so bd mirrors the queue while markdown remains the source of truth.
The real open queue — as re-triaged by task 01 — is imported, and the
committed JSONL export in `.beads/` reflects it. Existing readers
(status.sh, list_specs) keep working untouched.

## Touch

One-way only: shadow-sync never writes markdown. Depends on task 01 so
subsumed items are excluded from the import rather than imported and
immediately obsolete.

## Steps

1. Write `tests/test_agentic_shadow.py` failing first: fixture spec dir
   with three task files (one pending, one blocked with Unblock, one
   done); sync; assert bd states, dependency edges, and metadata
   (touch/rigor/budget) match; re-run after editing a header → bd
   reflects the change; markdown files byte-identical throughout.
2. Implement shadow.py over task 02's helpers and 04's lock (sync takes
   the write lock like any writer).
3. Run the real import in this repo; commit the resulting JSONL export.

## Acceptance

- [x] `python3 -m pytest tests/test_agentic_shadow.py -q` → passes
      Evidence: `8 passed` — status→bd-class mapping, blocking dep edges, touch/rigor/budget metadata, re-sync reflects an edited header, markdown byte-identical across syncs, and the write-lock contention path (`sync` blocks on a live `RepoLock`).
- [x] `python3 -m pytest tests/test_agentic_shadow.py -q -k differential` → passes: the test computes the dispatchable ID set from the markdown headers via `.claude/skills/drain/drain_frontier.py` (the pre-cutover implementation of the same rules) and asserts set equality with `agentic ready --json` on the real imported queue — two independent implementations agreeing, not a recorded observation
      Evidence: `2 passed, 6 deselected` — over the real re-triaged queue the two independent frontier implementations agree: `drain_frontier` dispatchable set == `agentic` dispatchable set (dependency-resolution), and `agentic ready --json` == that dispatchable set projected through the same global Touch admission seeded with the in-flight claims (`agentic ready` is the Touch-admitted frontier; `drain_frontier`'s raw `dispatchable` is pre-Touch).
- [x] `git status --porcelain | grep -c interactions.jsonl` → `0` after a sync run
      Evidence: prints `0` — `.beads/interactions.jsonl` is gitignored (root `.gitignore`), so a sync run never surfaces it in the working tree.
- [x] `bash scripts/check.sh` → green
      Evidence: `check.sh: green` (EXIT=0) — 22 shell suites ok, 32 pytest tests pass including `tests/test_agentic_shadow.py`; the only FAIL is the pre-existing quarantined `test_skill_chain_determinism.sh` (owner: another spec), which does not fail the suite.
