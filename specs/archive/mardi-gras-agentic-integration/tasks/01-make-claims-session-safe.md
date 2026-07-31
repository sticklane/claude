# Task 01: make claims session-safe

<!-- Task state is canonical in bd. The Status and Priority lines are frozen display and are not edited by workers. Task definitions are immutable after registration. -->

Status: pending
Depends on: none
Priority: P0
Budget: 34 turns
Spec: ../SPEC.md (requirements R9, R17)
Touch: agentic/claim.py, agentic/bd.py, agentic/lock.py, agentic/cli.py, tests/test_agentic_claim_races.py, tests/inventory/mardi-gras-01-claims.json, specs/toolkit-core-simplification/surface-inventory/mardi-gras-01-claims.json

## Goal

Make the existing positional `agentic claim <id>` the single toolkit claim
boundary across linked worktrees and same-human sessions. It returns the
canonical run identity, repairs an interrupted same-run marker write, and
loses safely to every different actor without invoking Git or JSONL sync.

## Touch

This task owns only the claim command, its Beads adapter, and the
canonical-repository lock. It must not instrument skills, add launch records,
or edit the retained `tests/test_agentic_events.py`.

## Steps

1. Write the failing multi-process and linked-worktree race fixtures first,
   including a raw `bd` actor and a crash between claim and marker append.
2. Key the short-lived lock from canonical `bd context --json` identity and
   remove the retired sync sequence from the claim path.
3. Implement the exact decision order: matching in-progress run reuses and
   repairs; open plus freshly ready attempts one claim; every other state
   loses.
4. Add the unambiguous drain-worker verification flag form and bounded JSON
   outcomes without creating a durable lease or recovery authority.
5. Add unique inventory fragments for every new canonical test or CLI
   surface.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_claim_races.py -q` → linked-worktree UI/direct/drain/raw races have exactly one winner; same-run retry repairs its marker; invalid preclaims lose; and orphan reopen with an empty assignee permits a distinct new run (L3).
- [ ] `python3 -m pytest tests/test_agentic_claim_races.py -q -k 'no_git_or_jsonl or positional_cli or verify_drain_worker'` → the existing positional grammar remains compatible, verifier parsing is unambiguous, and no claim branch invokes Git or reads/writes `.beads/issues.jsonl` (L2).
- [ ] `python3 scripts/inventory-core-surface.py --check specs/toolkit-core-simplification/BASELINE.json` → new claim/test surfaces are classified without changing retained content (L2).
- [ ] `bash scripts/check.sh` → the repository gate remains green after the claim migration (L3).
