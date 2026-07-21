# Task 05: shadow-mode markdown→bd sync and live-queue import

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
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
4. Wire the test into scripts/check.sh.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_shadow.py -q` → passes; red commit precedes green in this task's history
- [ ] `bash -c 'a=$(agentic ready --json | python3 -c "import json,sys;print(len(json.load(sys.stdin)))"); b=$(grep -l "^Status: pending" specs/*/tasks/*.md | xargs -I{} sh -c "grep -q \"^Depends on: none\" {} && echo {}" | wc -l); echo "agentic=$a md=$b"'` → the two counts are consistent with the frontier rules (record both numbers as evidence; investigate any mismatch rather than accepting it)
- [ ] `git status --porcelain | grep -c interactions.jsonl` → `0` after a sync run
- [ ] `bash scripts/check.sh` → green
