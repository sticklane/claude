# Task 03: agentic ready and resume (read verbs)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 02
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (statements 3, 9; R-L)
Touch: agentic/ready.py, agentic/resume.py, agentic/frontier.py, tests/test_agentic_ready.py, tests/test_agentic_latency.sh

## Goal

`agentic ready [--json]` lists tasks whose blockers are done AND whose
Touch paths (bd metadata `touch`) do not overlap any claimed task —
priority-ordered, porting the Touch-disjoint co-admission and ordering
logic from `.claude/skills/drain/drain_frontier.py` and
`.claude/skills/_shared/touch_disjoint.py` onto `bd ready --json`
output. `agentic resume` prints the frontier plus in-flight claims (who,
what, since when) from tracker state alone.

## Touch

Reads bd only through task 02's helpers. Does not modify
drain_frontier.py or the drain skill (cutover is task 09). cli.py stub
registration exists from 02 — fill the module bodies only.

## Steps

1. Write `tests/test_agentic_ready.py` failing first: fixture store
   seeded via helpers with (a) a blocked task excluded, (b) two tasks
   with overlapping `touch` metadata where the claimed one excludes the
   other, (c) P0 ordered before P2, (d) `--json` output parseable with
   the documented fields.
2. Implement frontier.py (port the disjointness + ordering math),
   ready.py, resume.py.
3. Write `tests/test_agentic_latency.sh`: seed ≥500 issues in a scratch
   store, assert median wall time of 5 `agentic ready` runs < 1s (R-L).

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_ready.py -q` → passes
- [ ] `bash tests/test_agentic_latency.sh` → prints `MEDIAN <n>s OK` with n < 1 at ≥500 seeded issues (R-L)
- [ ] `bash scripts/check.sh` → green
