# Task 08: the work loop and the any-runtime end-to-end test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: obsolete
Superseded: 2026-07-22 data-portability pivot (maintainer-ratified) — native ultracode is the execution engine; see ../SPEC.md addendum. Keeper fragments (screen, pre-flight budget check, tier doctrine) fold into specs/beads-daily-skill.
Depends on: 05, 07
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (statement 8; component "The loop"; R-G; D9 batching)
Touch: agentic/loop.py, tests/test_agentic_loop.py, tests/test_agentic_generic.sh

## Goal

`agentic loop [--max-tasks N] --worker <command>` runs
ready→claim→compose→dispatch→verdict until the frontier is empty, the
cap is hit, or N tasks complete. The worker command receives the
composed document on stdin and the verdict path in AGENTIC_VERDICT; a
missing or invalid verdict file marks the attempt failed and returns
the task to ready with the failure recorded. The loop batches one
export-commit-push per iteration (D9). Deferred questions in verdicts
become tracker records.

## Touch

The `--worker` abstraction is what keeps R-G honest: any runtime is a
command that reads the document and writes the verdict file. Runtime
adapters (task 10) wire real agents into it; this task uses stub
workers only.

## Steps

1. Write failing tests first: `tests/test_agentic_loop.py` (stub worker
   scripts: one returns DONE, one BLOCKED with typed Unblock, one
   writes no file → attempt failed and task back to ready; commit count
   equals iterations, not writes).
2. `tests/test_agentic_generic.sh` (R-G): in a bare shell — no MCP, no
   runtime-native tools, PATH restricted to system + agentic + bd —
   run init→shadow-sync→ready→claim→compose→stub-worker→verdict→resume
   end to end against a fixture repo; exit 0.
3. Implement loop.py; make everything green.
4. Re-run task 04's two race scripts against the loop-integrated write
   path (the spec lands R-C here).

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_loop.py -q` → passes
- [ ] `bash tests/test_agentic_generic.sh` → prints `GENERIC OK` (R-G)
- [ ] `bash tests/test_agentic_write_lock.sh && bash tests/test_agentic_clone_race.sh` → both still pass post-integration (R-C)
- [ ] `bash scripts/check.sh` → green
