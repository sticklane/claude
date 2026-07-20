# Task 05: gate evalset (happy path + adversarial red-checks block)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4a)
Touch: evals/gate/

## Goal

`evals/gate/` holds two scenarios: `01-*` happy-path (a green-checks
fixture repo gets the Stop hook + format-on-edit + protected-file rules
installed, asserted on the produced settings/hook files) and `02-adv-*`
adversarial — a fixture repo whose checks are RED; assert.sh fails
unless the installed Stop-hook configuration would block "done" (assert
the hook wiring and the failing check command's presence — artifact
assertions, no live hook execution).

## Steps

1. Read `evals/breakdown/01-small-spec/` for the contract and the gate
   skill's reference.md for the exact hook JSON it installs (config
   lives there, not in SKILL.md).
2. setup.sh builds the two fixture repos (green and red check scripts);
   assert.sh parses produced settings JSON structurally (python3 json
   load, key checks), never exact-string output.

## Acceptance

- [ ] `ls -d evals/gate/0* | wc -l` → 2, one matching
      `evals/gate/02-adv-*` (dir absent today, verified 2026-07-19)
- [ ] `for f in evals/gate/*/assert.sh; do bash -n "$f" || exit 1;
    done` → exit 0
- [ ] `./evals/run.sh gate` passes — manual-pending (paid headless run,
      human-launched, per docs/memory/unattended-worker-tool-limits.md)
