# Task 03: Make the three container-hostile tests portable (GNU sed/stat, root)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md
Discovered-from: specs/fleet-viz-css-resync/tasks/01-resync-and-drift-guard.md
Touch: tests/test_drain_owner_protocol.sh, tests/test_hook_templates.sh, tests/test_install_gates.sh

## Goal

`tests/test_drain_owner_protocol.sh`, `tests/test_hook_templates.sh`, and
`tests/test_install_gates.sh` pass in a root Linux container as well as
on macOS: BSD-vs-GNU `sed`/`stat` invocations become portable, and
permission-denial fixtures relying on `chmod 000` being unreadable
(false as root) either use a root-safe denial mechanism or skip that one
assertion as root with an explicit skip message — never by deleting the
assertion (docs/memory/root-container-test-failures.md has the incident
context).

## Steps

1. Reproduce: run each test as root in this container; record the exact
   failures (they fail today — this is the red step).
2. Fix portability per failure: feature-detect `sed -i`/`stat` variants
   or use portable constructions; replace root-defeated `chmod 000`
   checks with a root-safe mechanism (e.g. a nonexistent path) or a
   guarded, messaged skip that still runs for non-root users.
3. Confirm guarding still bites: for one assertion per file, temporarily
   break the guarded behavior in a scratch copy and confirm the test
   goes red.
4. Full sweep green.

## Acceptance

- [ ] `bash tests/test_drain_owner_protocol.sh` → exit 0 (as root, this container)
- [ ] `bash tests/test_hook_templates.sh` → exit 0
- [ ] `bash tests/test_install_gates.sh` → exit 0
- [ ] `for t in tests/test_*.sh; do bash "$t" || { echo "FAIL: $t"; exit 1; }; done` → exit 0 (whole sweep, no regressions)
- [ ] Evidence cites each added skip (if any) with its reason — skips are the exception, not the fix
