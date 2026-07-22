# Task 07: the calibrated turns-to-tokens factor

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q '^Status: done' specs/agentic-core-redesign/tasks/05-shadow-sync-import.md || echo "core task 05 (shadow sync) not done"
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (DW4; RW-F)
Touch: agentic/shadow.py, scripts/measure_turn_factor.py, tests/test_agentic_turns_factor.py

## Goal

`Budget: N turns` task headers resolve through a calibrated
tokens-per-turn factor in the runtime profile to `budget_tokens` in
the shadow-synced metadata. The factor's value is measured — derived
from agentprof's per-turn token distribution — and recorded in the
profile with its source and date; the audit job re-measures it. A
factor nobody measures is a fudge factor; this task ships the
measurement, not a guess.

## Touch

Extends core task 05's shadow module (hence the gate). Nothing
auto-flips this task: re-run the Unblock check and flip Status once
core 05 is done.

## Steps

1. Write `tests/test_agentic_turns_factor.py` failing first: a
   fixture task with `Budget: 6 turns` and a fixture profile factor
   of 9000 tokens/turn resolves to `budget_tokens: 54000` in the
   synced metadata; a profile with no factor produces a typed
   warning and no budget_tokens (never a silent default).
2. Write `scripts/measure_turn_factor.py`: derives the factor from
   agentprof transcript data and, with `--check <profile>`, re-runs
   the measurement and asserts the recorded value reproduces within
   ±20% — the measurement is a committed, re-runnable script, not a
   one-time claim. Record value, source query, sample size, and date
   in the profile.
3. Implement the mapping in the shadow module.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_turns_factor.py -q` → passes (RW-F, incl. the no-factor warning path)
- [ ] `python3 scripts/measure_turn_factor.py --check agentic/config/*.toml` → prints `FACTOR REPRODUCED` (re-measurement matches the recorded value within ±20% — fails on any unmeasured or stale value; a pasted "source" string cannot pass this)
- [ ] `bash scripts/check.sh` → green
