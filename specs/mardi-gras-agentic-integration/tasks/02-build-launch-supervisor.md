# Task 02: build the launch and supervisor boundary

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: 01
Priority: P0
Budget: 44 turns
Spec: ../SPEC.md (requirements R2, R3, R4, R5, R6, R8, R12)
Touch: agentic/cli.py, agentic/launch.py, agentic/dispatch.py, agentic/schema/control-v1.json, agentic/schema/dispatch-v1.json, tests/test_agentic_launch.py, tests/inventory/mardi-gras-02-launch.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-02-launch.json

## Goal

Add a provider-neutral prepare/supervise protocol that validates only trusted
issue identifiers and contained authored paths, records immutable intent, and
starts one packaged skill through an argv array in the inherited PTY. The
boundary observes process lifecycle but never claims, schedules, retries, or
interprets tracker prose.

## Touch

The launcher may pass fixed identifiers and paths only. It must not modify
Beads, import skill orchestration, construct a shell command, or implement
Mardi Gras UI behavior.

## Steps

1. Write failing target-resolution, malicious-input, dispatch-store, PTY,
   signal, and process-reaping fixtures first.
2. Implement `agentic launch --prepare` with fresh-ready validation,
   physical containment, explicit drain confirmation, immutable package
   identity, bounded JSON, and exact reused-dispatch semantics.
3. Implement `agentic supervise` with no-shell child creation, inherited
   file descriptors, atomic lifecycle appends, signal forwarding, and
   verified correlation environment.
4. Make boot identity and monotonic-time handling downgrade uncertain
   evidence instead of expiring by wall clock.
5. Add JSON schemas and unique inventory fragments for the new commands,
   records, and tests.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_launch.py -q -k 'TargetResolution or PromptContract'` → only fresh repo-local targets and physically contained authored paths reach pointer-only argv; malicious tracker/path data and unsupported drain/runtime pairs fail before spawn (L3).
- [ ] `python3 -m pytest tests/test_agentic_launch.py -q -k 'SupervisorTopology or PackageLifecycle'` → prepare is bounded, reused replies are exact, PTY descriptors are inherited, one child is reaped, signals are forwarded, lifecycle writes are atomic, and resolver/plugin pruning cannot change a recorded dispatch (L3).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → launch/control surfaces and tests are inventoried (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green with the new commands (L3).
