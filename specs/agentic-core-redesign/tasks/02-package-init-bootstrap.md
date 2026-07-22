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

## Answers

- [2026-07-22 maintainer] To the deferred question on criterion 5:
  option (a) — ignore the two pre-existing red tests for now.
  `scripts/check.sh` carries an explicit KNOWN-RED quarantine list
  naming `tests/test_skill_chain_determinism.sh` (retired by core
  task 10 with the mirror machinery — its owning spec is now
  obsolete, subsumed by the redesign) and `tests/test_eval_coverage_lint.sh`
  (owner: specs/eval-coverage-tiers — needs bash 4+, host has 3.2).
  Quarantined tests still run and print their status but do not fail
  the suite; the list is printed in check.sh output so the quarantine
  is visible, never silent. Remove each entry when its owning spec
  fixes the test. Criterion 5's "green" means green with this
  documented quarantine. Re-dispatch starts from the recorded
  Decisions; Steps 1-3 are done and verified.

## Deferred questions

- [2026-07-21 /drain] Contradicts-premise: true — this file. Contradicted
  excerpt: "`bash scripts/check.sh` → green, and its output lists both the
  pre-existing". Evidence: two pre-existing `tests/test_*.sh` files fail
  unconditionally on plain `main`, both outside this task's `Touch`, so a
  glob-all canonical check is honest-red for reasons this task cannot fix:
  `tests/test_skill_chain_determinism.sh` asserts
  `evals/lint-skill-chain-determinism.sh` exists (it doesn't — built by
  `specs/deterministic-skill-chaining`); `tests/test_eval_coverage_lint.sh`
  runs `evals/lint-eval-coverage.sh`, which uses bash 4+ `declare -A` against
  this host's bash 3.2. Question: should the new `scripts/check.sh` (a)
  quarantine these two as documented known-red so check.sh goes green (the
  worker declined to do this unilaterally — it reads as a gamed pass), (b)
  wait for those two specs to fix/quarantine their own tests first, then
  check.sh goes green unchanged, or (c) have criterion 5 amended to scope
  "green" to non-placeholder tests? All other criteria (1, 2, 3, 4, 6, 7)
  pass; the implementation is otherwise complete on branch
  `task/02-agentic-core-redesign` (discarded per drain's DEFERRED handling —
  re-derivable from this task's Steps on re-dispatch).

## Decisions

- [2026-07-21 /drain] Installed bd 1.1.0 via `brew install beads` (pulls
  dolt) — required because the task wraps bd, and bd is not buildable from
  source on this host (`go install` fails on ICU headers). Reverse: `brew
  uninstall beads dolt`.
- [2026-07-21 /drain] Symlinked `~/.local/bin/agentic` → repo `bin/agentic`
  so the bare `agentic` command resolves on the login PATH (neither repo
  `bin/` nor the pip framework-scripts dir is on PATH here). Points at the
  main checkout, so it activates on merge. Reverse: `rm ~/.local/bin/agentic`.
- [2026-07-21 /drain] Pinned bd version = `1.1.0`, install pointer `brew
  install beads`, upgrade pointer `brew upgrade beads` (SPEC pins 1.1.0; the
  brew bottle is the clean install path). Reverse: edit `agentic/bd.py`.
- [2026-07-21 /drain] Committed transport JSONL = `.beads/issues.jsonl` (bd
  export default); telemetry `.beads/interactions.jsonl` stays gitignored.
  Reverse: edit `agentic/initialize.py`.

## Progress

- [2026-07-21 /drain] DEFERRED (Contradicts-premise). Done: package,
  `agentic init`, bd pin + missing/wrong-version errors, curated bd
  bootstrap, JSONL round-trip/bootstrap against real bd, export/import
  helpers, `scripts/check.sh` (glob discovery), AGENTS.md/.gitignore — all
  implemented and independently verified (acceptance criteria 1–4, 6, 7
  pass). Remaining: criterion 5's "green" run of `scripts/check.sh`,
  blocked entirely on the two pre-existing out-of-Touch red tests named
  above — not on anything left to implement. A re-dispatch after this
  question is answered should start from the Decisions above rather than
  re-deriving them, and does not need to redo Steps 1–3.
