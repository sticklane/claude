# Task 02: project normalization — (home), (tmp), no agent-dir projects

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
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

- [ ] `cd agentprof && go test ./internal/claude/` → pass including the
  three normalization fixtures (hermetic — no dependence on the real
  $HOME)
- [ ] `bash agentprof/scripts/check.sh` → green
