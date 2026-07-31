# Task 15: build the repaired launch and supervisor boundary

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01, 14, 37
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R2, R3, R4, R5, R6, R8, R12, R15, R17)
Touch: agentic/cli.py, agentic/launch.py, agentic/dispatch.py, agentic/schema/control-v1.json, agentic/schema/dispatch-v1.json, tests/test_agentic_launch.py, tests/inventory/mardi-gras-15-launch-v2.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-15-launch-v2.json

## Goal

Add the provider-neutral prepare/supervise protocol on the repaired claim,
package/runtime/process, and drain-integration foundations. Prepare validates
only fresh trusted targets and writes immutable intent; supervise atomically
starts at most one exact runtime child in the inherited PTY and records
process lifecycle without claiming, scheduling, or interpreting tracker
prose.

## Touch

This task owns launch target resolution, dispatch state, exact prompt/argv,
and supervisor process control. It consumes Task 14 identity APIs and Task 37
drain integration without modifying them. It must not implement Beads
authorization, claim/requeue behavior, runtime package construction, run-event
v2, Mardi Gras UI behavior, or a second scheduler.

## Steps

1. Write failing target, malicious-input, dispatch-race, runtime-swap, PTY,
   signal, and process-reaping fixtures first.
2. Implement `agentic launch --prepare` with a fresh authorized ready read,
   provider-ID grammar, physical authored-path containment, explicit drain
   confirmation, supported runtime/workflow matrix, and a new UUIDv7 dispatch
   for every success.
3. Emit exact canonical `agentic.control/v1` with the closed issue/drain
   target union and absolute `agentic supervise --dispatch-id <id>` argv,
   returning within three seconds without a claim or reservation.
4. Under the dispatch lock, permit exactly one `prepared` to `starting`
   transition; every retry or concurrent supervisor returns
   `dispatch_already_started` without spawning.
5. Construct the exact four-line pointer-only prompt and invoke the recorded
   physical runtime path without a shell after package and runtime-fingerprint
   revalidation.
6. Inherit FDs 0/1/2, start exactly one child, forward termination signals,
   wait/reap it, export only validated correlation variables, and append
   atomic started/failed-to-start/exited lifecycle records using Task 14's
   process identity contract.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_launch.py -q -k 'TargetResolution or PromptContract'` → only fresh repo-local provider IDs and physically contained authored paths reach the exact four-line pointer-only prompt; tracker prose, malicious paths, and unsupported drain/runtime pairs fail before spawn (L3).
- [ ] `python3 -m pytest tests/test_agentic_launch.py -q -k 'DispatchSingleStart or SupervisorTopology or ProcessIdentity or RuntimeFingerprint'` → prepare is fresh and bounded, concurrent supervisors spawn once, PTY descriptors/signals/reaping are correct, correlation fields follow the shared fixture, and package/runtime drift fails before execution (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → launch/control records, schemas, tests, and commands are uniquely classified (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green with the repaired launch boundary (L3).
