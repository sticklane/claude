# Task 02: agentic package scaffold, init, JSONL bootstrap, bd pin

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P0
Budget: 24 turns
Spec: ../SPEC.md (statements 1, 2, 11; D3, D10 pin; R-B, R-E, R-V)
Touch: agentic/, tests/test_agentic_bootstrap.sh, tests/test_agentic_roundtrip.sh, tests/test_agentic_pin.py, scripts/check.sh, .gitignore, AGENTS.md

## Goal

A Python package `agentic/` exists at the repo root with a console
entrypoint registering ALL planned subcommands (ready, claim, verdict,
resume, compose, ctx, init, inbox, demote — stubs exit 2 "not
implemented" for verbs later tasks fill), so sibling tasks stay
Touch-disjoint on their own modules. `agentic init` works end to end:
controlled `bd init` (side-effect files diffed and curated, never
auto-committed to the host repo), `.beads/interactions.jsonl`
gitignored, bd version checked against a pin (a MISSING bd produces a clean error
naming the pinned install command, never a confusing pin mismatch), and
tracker state imported from a committed JSONL when one exists.
`bd export` and `bd import` are wrapped as internal helpers other tasks
reuse. This task also CREATES `scripts/check.sh` — the repo previously
had none — as the canonical check: it runs the existing
`tests/test_*.sh` loop plus `python3 -m pytest` over
`tests/test_agentic_*.py`, discovering both BY GLOB so no later task
ever edits it. AGENTS.md's quick commands point at it and its Map
gains the `agentic/` component.

## Touch

Creates the package and shared test fixtures only. Does NOT implement
ready/claim/verdict/resume/compose/ctx/inbox bodies — those belong to
tasks 03, 04, 06, 07, 11 in their own modules.

## Steps

1. Write the failing tests first: `tests/test_agentic_pin.py` (a fake
   `bd` on PATH reporting the wrong version → `agentic init` refuses
   with the pin and an upgrade pointer), `tests/test_agentic_roundtrip.sh`
   (scratch git repo + JSONL fixture: init → import → re-export → diff
   filtered of volatile fields = empty), `tests/test_agentic_bootstrap.sh`
   (bare-clone a fixture remote containing a committed JSONL, run
   `agentic init`, assert the issue count from `bd list --json`).
2. Scaffold `agentic/` (pyproject or setup.cfg consistent with repo
   conventions; `python -m agentic` and a `bin/agentic` shim both work),
   register stub subcommands.
3. Implement the pin check, curated init, gitignore handling, and the
   export/import helpers; make the three tests pass.
4. Create `scripts/check.sh` (glob discovery, both suites); update
   AGENTS.md quick commands and Map accordingly.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_pin.py -q` → passes; committed test shown failing before implementation (red commit precedes green in this task's history)
- [ ] `bash tests/test_agentic_roundtrip.sh` → prints `ROUNDTRIP OK` after a zero-record diff (R-E)
- [ ] `bash tests/test_agentic_bootstrap.sh` → prints `BOOTSTRAP OK` with the imported count; only `git clone` + `agentic init` are executed against the fixture remote (R-B)
- [ ] `bash -c 'cd "$(mktemp -d)" && git init -q . && agentic init >/dev/null 2>&1; git -C . status --porcelain | grep -c interactions'` → `0` (telemetry never dirties status)
- [ ] `bash scripts/check.sh` → green, and its output lists both the pre-existing `tests/test_*.sh` names and the new agentic tests (proves glob discovery, not a hand-listed subset)
- [ ] `python3 -m pytest tests/test_agentic_pin.py -q -k missing` → passes (bd absent from PATH → clean install-command error)
- [ ] `grep -c "scripts/check.sh" AGENTS.md` → ≥ 1 (canonical check documented)
