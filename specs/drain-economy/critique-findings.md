# drain-economy — critique findings

Spec content hash (bytes the settled verdict was produced from):
`b5672c8454748ea89cb67b22a14d4277ae84a40773646e60407357ab68a9309c`
Verdict: **NOT READY** (2026-07-30, single-pass)

## 2026-07-30 — round 1

Eight findings, ranked as returned. All eight were addressed in commits
`03de70da` (mechanical), `98a02d85` (repair + re-application), and the task
edits alongside them. Under the single-pass rule adopted the same day, no
second critic pass confirmed the fixes — implementation is the next
verification, not another review round.

1. **Command policy did not exist; tasks 02 and 08 cited each other for it.**
   EP18 and EP12 both deferred to "the same command policy," which a grep
   across `.claude/`, `bin/`, `agentic/`, `scripts/`, and `docs/` showed does
   not exist. Task 08 depended only on 07, so it could land first and invent
   one, while task 02 was told never to author one. → Resolved by decision D11
   (modeled on `.claude/rules/human-blockers.md`'s probe contract) and a new
   task 00 owning the single implementation, with tasks 02 and 08 both
   depending on it.
2. **EP20's ceremony auto-ran `expensive` criteria unattended**, contradicting
   `docs/memory/unattended-worker-tool-limits.md` and this spec's own
   manual-pending markings. → EP20 now gates on `--tier cheap` plus a
   human-recorded expensive pass; a missing record halts the ceremony and files
   an `ask:`. EP11 defines the tiers by who may launch them.
3. **`spec-gate` ran criteria with real side effects against live state** — the
   spec's own A2 was `bd create "x" --labels triage`, leaking a bead every
   pass, on a schedule, with the result committed. → Decision D12 (criteria are
   read-only or idempotent), enforced at authoring time by EP16's READY bar,
   and A2 rewritten.
4. **Two registry files sat in every task's `Touch` with no serializing edges**,
   while the Parallelization prose claimed the chains shared no file. → Each
   task now writes its own `drain-economy-NN.json` in both `tests/inventory/`
   and the surface-inventory directory; the prose states this.
5. **Two workboard paths were unclassified and registered by no task**, so task
   10 would stall on the acceptance pre-flight. → Added to task 01's fragment
   enumeration and to its preflight criterion.
6. **EP17's reporting half had no check** outside the manual-pending
   end-to-end. → Task 05 gained an L2 criterion on `imported blocking work`
   with the donor slug, plus a spillover-section check.
7. **The spec's own acceptance block violated EP11 and EP16** — eight criteria
   with no command and no grammar. → All 22 rewritten under
   `A<k> (<tier>): \`<command>\` — <expected>`, each pointing at a command that
   exists in a task file.
8. **Undecided seam between tasks 02 and 04**: task 02 was told to record the
   spillover event "through whatever recording surface exists," but task 04
   defines that surface and lands later. → Task 04 explicitly owns the record;
   task 02's steps stop at narration and branch logic.

## Open, not applied

Two digest items from the round-2 read, left for implementation to settle:

- `tasks/08-spec-gate.md`'s fixture criteria run `bin/spec-gate <fixture>` and
  then read `specs/<fixture>/acceptance-status.json`, while the fixtures live
  under `tests/fixtures/spec-gate/`. Whether the gate takes a slug under
  `specs/` or an arbitrary path is undecided; the implementing worker pins it
  and states which.
- `tasks/13-critique-ready-bar.md`'s `ls evals/critique/*/ -d | wc -l`
  criterion compares against "the pre-task count recorded in this task's commit
  message," which a verifier cannot run without the commit in hand. Pin the
  absolute expected count when implementing.
