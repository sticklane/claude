# Task 02: project normalization — (home), (tmp), no agent-dir projects

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 01
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R2)
Touch: agentprof/internal/claude/, agentprof/testdata/

## Goal

The home-directory transcript dir maps to project `(home)` (home
detection injectable — param or env override consulted before
`os.UserHomeDir()` — so tests are hermetic); mktemp-shaped dirs
(`tmp.[A-Za-z0-9]{6,}`) map to `(tmp)`; agent sidecar dirs
(`agent-<hex>`) are folded into their owning session's project when
cheaply resolvable, else dropped with a parse-stat counter — never
emitted as projects.

## Touch

Same file as task 01 — runs after it (serial chain). Do NOT touch
costsummary (task 05) or the denylist/emit hygiene (task 06).

## Steps

1. Failing tests first: fixtures for home→`(home)`, `tmp.XXXXXXXXXX`→
   `(tmp)`, and an `agent-*` dir emitting no project (counter
   incremented).
2. Implement in the project-frame derivation; add the injectable home
   override.

## Acceptance

- [x] `cd agentprof && go test ./internal/claude/` → pass including the
  three normalization fixtures (hermetic — no dependence on the real
  $HOME) — verifier: all four normalization tests pass, each pins home via
  `t.Setenv("AGENTPROF_HOME", …)` (evidence/02-project-normalization.md)
- [x] `bash agentprof/scripts/check.sh` → green — verifier: format-check ok,
  lint ok, tests ok (evidence/02-project-normalization.md)

## Decisions

- 2026-07-11 — Home injection uses env override `AGENTPROF_HOME` (consulted before `os.UserHomeDir()`) rather than a new function parameter: `Collect`/`CollectWithReprime` callers live outside this task's Touch. SPEC allows "param OR env override"; env satisfies hermeticity. Reverse: add a param overload later without breaking the env path.
- 2026-07-11 — Dropped agent-dir counter folds into the existing `skipped` parse-stat return rather than a new return value (same signature-stability reason). Reverse: promote to a dedicated stats field when a future task widens the parser's return shape (task 03's pending-count parse-stat is a natural point).
