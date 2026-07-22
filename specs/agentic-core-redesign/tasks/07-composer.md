# Task 07: the composer — compose, screen, spend metering

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: obsolete
Superseded: 2026-07-22 data-portability pivot (maintainer-ratified) — native ultracode is the execution engine; see ../SPEC.md addendum. Keeper fragments (screen, pre-flight budget check, tier doctrine) fold into specs/beads-daily-skill.
Depends on: 04, 06
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (statement 6; component "The composer", "Verdict transport"; D4; R-M, R-S)
Touch: agentic/compose.py, agentic/meter.py, agentic/screen.py, agentic/config/worker_instructions.md, agentic/schema/envelope.json, tests/test_agentic_compose.py, tests/test_agentic_screen.sh

## Goal

`agentic compose <id>` emits the complete dispatch document, validated
against `agentic/schema/envelope.json`: the task body, the repo's worker
instructions (`agentic/config/worker_instructions.md` — how to build,
test, and report here, including the verdict-file contract), a code map
from task 06's helper scoped to the task's touch metadata, derived tool
grants (marked UNENFORCED when the target runtime has no permission
primitive), the model/effort tier from config, the verdict schema, and
the verdict file path (also exported as AGENTIC_VERDICT where the
runtime allows). It refuses — nonzero exit, reason on stderr — when the
task text fails the injection screen or the run's spend cap is crossed;
the meter uses harness telemetry when configured, else its own
ceil(bytes/4) estimate accumulated in tracker metadata.

## Touch

The screen reuses the fixture set at
`.claude/skills/drain/screen-stub-fixtures/` — do not fork new fixture
content. No loop work (task 08).

## Steps

1. Write failing tests first: `tests/test_agentic_compose.py` (envelope
   validates against the schema; code map present and ≤ budget; grants
   marked UNENFORCED for a bare-shell runtime profile; cap refusal:
   with no telemetry configured, accumulate estimates to the cap and
   assert compose exits nonzero — R-M); `tests/test_agentic_screen.sh`
   (compose a fixture task whose description embeds a screen-stub
   injection string → refusal or neutralization asserted on output —
   R-S).
2. Write `agentic/config/worker_instructions.md` (the one hand-written
   judgment document compose injects).
3. Implement meter.py, screen.py, compose.py; make tests green.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_compose.py -q` → passes (covers R-M refusal)
- [ ] `bash tests/test_agentic_screen.sh` → prints `SCREEN OK` (R-S)
- [ ] `grep -cE "check\.sh|AGENTIC_VERDICT" agentic/config/worker_instructions.md` → ≥ `2` (the instructions actually name the check command and the verdict-file contract, not a placeholder)
- [ ] `bash scripts/check.sh` → green
