# Task 99: Batch version bump + full acceptance sweep

Status: pending
Depends on: 01, 02, 03, 04, 05, 06, 07, 08, ../../model-agnostic/tasks/03-evals-runner-params.md, ../../model-agnostic/tasks/04-antigravity-mirrors.md, ../../context-management/tasks/03-tool-call-ceilings.md, ../../repo-orientation/tasks/02-onboard-and-record.md, ../../tournament-votes/tasks/01-majority-votes.md, ../../task-priority/tasks/02-research-record.md, ../../workflow-author/tasks/02-record-and-port-row.md, ../../work-tracking/tasks/02-research-record.md
Budget: 40 turns
Spec: ../SPEC.md (cluster 99)

## Goal

One minor version bump for the entire batch — satisfying every spec's
"bump version whenever skill behavior changes" clause exactly once — plus
a final sweep re-running every task's Acceptance across ALL queues.
Runs only after every other queue has landed.

## Touch

- `.claude-plugin/plugin.json` (`version` only)
- `specs/hardening-quick-wins/tasks/04-scout-idea-version.md` (stale
  version-pin note, only if its ticked acceptance conflicts with the bump)

## Steps

1. Confirm every other task in the combined queue is `Status: done` (or
   deferred/blocked with the orchestrator's sign-off) — this task must
   not run early.
2. Bump `version` in `.claude-plugin/plugin.json` by one minor: `0.3.0`
   becomes `0.4.0` (if an intervening bump landed, bump minor from
   whatever is current and adjust the acceptance pin below to match).
3. Run `claude plugin validate .` — must still exit 0 after the edit.
4. Sweep: re-run every task's `## Acceptance` commands across all queues
   in the combined batch (this queue's tasks 01-08 plus the other specs'
   task files). Record any failure in this task file and stop with
   verdict BLOCKED rather than merging a red sweep.
5. Hardening task 04 (`specs/hardening-quick-wins/tasks/04-scout-idea-version.md`)
   has a ticked acceptance pinning version `0.3.0`; after the bump that
   check is stale. Update its note (annotate the ticked box: pin
   superseded by the review-fixes batch bump) so the sweep doesn't count
   it as a regression. Same for hardening's SPEC R9 grep if the sweep
   runs SPEC-level checks.

## Acceptance

- [ ] `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.4.0'"` → exit 0 (single batch bump)
- [ ] `claude plugin validate .` → exit 0
- [ ] Every `## Acceptance` command in `specs/review-fixes/tasks/0*.md` re-run → all exit 0
- [ ] Every other queue's task acceptances re-run → all exit 0, except version-pin checks annotated in step 5
- [ ] `grep -q "superseded" specs/hardening-quick-wins/tasks/04-scout-idea-version.md || python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.3.0'"` → exit 0 (stale pin annotated iff the bump conflicts with it)
