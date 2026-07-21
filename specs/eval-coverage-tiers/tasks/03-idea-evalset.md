# Task 03: idea evalset (happy path + adversarial gameable-criterion)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: done
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4a)
Touch: evals/idea/

## Goal

`evals/idea/` holds two scenarios: `01-*` happy-path (a pitch produces
specs/<slug>/SPEC.md with the template sections and runnable criteria)
and `02-adv-*` adversarial — a pitch whose OBVIOUS criterion is a
doctrine-word grep; assert.sh fails if the written SPEC.md contains an
unanchored grep criterion (no "verified <date>" note) or a
self-referential doctrine-word grep with no depth-ceiling annotation.
This is the behavioral complement criterion-depth-ladder's task 02
names.

## Steps

1. Read `evals/breakdown/01-small-spec/` for the contract; /idea is
   interactive — prompt.txt must pre-answer the interview inline.
2. setup.sh builds a minimal target repo; assert.sh parses the produced
   SPEC.md's Acceptance section (structure, not exact wording — assert
   the anchoring/ceiling markers, never incidental prose).

## Acceptance

- [x] `ls -d evals/idea/0* | wc -l` → 2, one matching
      `evals/idea/02-adv-*` (dir absent today, verified 2026-07-19)
- [x] `for f in evals/idea/*/assert.sh; do bash -n "$f" || exit 1;
done` → exit 0
- [ ] `./evals/run.sh idea` passes — manual-pending (paid headless run,
      human-launched, per docs/memory/unattended-worker-tool-limits.md)

## Evidence

- AC1 — `ls -d evals/idea/0*` returns two dirs, count 2:
  `evals/idea/01-happy-path-spec` and `evals/idea/02-adv-doctrine-grep`;
  the latter matches `evals/idea/02-adv-*`.
- AC2 — `bash -n` clean (exit 0) on both `assert.sh` files (and both
  `setup.sh` files, checked as a bonus).
- AC3 — manual-pending: `./evals/run.sh idea` is a paid headless model
  session, human-launched only (docs/memory/unattended-worker-tool-limits.md);
  not run by this unattended worker. Left unchecked.
- Extra confidence (not an acceptance gate): both `assert.sh` graders were
  self-tested against synthetic good/bad SPEC.md fixtures — 9/9 discrimination
  cases correct (bare doctrine grep → FAIL; anchored-only grep → FAIL;
  anchored grep + `Depth ceiling:` → PASS; behavioral non-grep criterion →
  PASS; degenerate/empty acceptance → FAIL; happy-path template present →
  PASS, missing section → FAIL). Both `setup.sh` scripts run clean, seed no
  `specs/`, and 02's README omits "strict" so the anchoring check is truthful.

## Decisions

- Scenario names: `01-happy-path-spec` (pitch: task due-dates + `overdue`
  command on a flat-file tasks CLI) and `02-adv-doctrine-grep` (pitch:
  document a `--strict` flag whose obvious criterion is `grep 'strict'
README.md`). Reversible — any `0*` / `02-adv-*` names satisfy AC1.
- Each `prompt.txt` pre-answers /idea's interview inline (non-interactive
  run) and asks for the spec ONLY (no /critique or /breakdown self-chain) —
  a legitimate SKILL.md step-7 fallback that keeps the eval focused on
  step-4 spec authorship (where anchoring/depth-ceiling doctrine applies).
- `02`'s assert treats a grep on a checkbox criterion line as the trap:
  present ⇒ require BOTH a "verified <date>" anchor note AND a `Depth
ceiling:` annotation; absent (criterion deepened past L0) ⇒ pass. This
  encodes the task's two named fail conditions and the ladder's
  deepest-feasible rule (docs/memory/anchored-acceptance-criteria.md).
- `allowed-tools.txt` adds `Task` (idea fans out scouts) plus
  `Bash(grep *)` (step-4 anchoring check) to the runner's default allowlist.
