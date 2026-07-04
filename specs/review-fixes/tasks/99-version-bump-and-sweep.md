# Task 99: Batch version bump + full acceptance sweep

Status: done
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

## Sweep record

Sweep ran 2026-07-03 over all 30 queue task files (specs/QUEUE.md): 135
backticked acceptance commands executed from repo root (134 in the batch
runner + `./evals/run.sh breakdown` separately, PASS 1/1). Results:

- 133/134 batch commands exit 0; `./evals/run.sh breakdown` exit 0.
- 1 literal failure, accounted for: review-fixes/01 version pin `0.3.0`
  — superseded by this task's batch bump (annotated in 01's acceptance;
  criterion-4 exception; its evidence file requested exactly this).
- 1 rc=2 on first run, resolved: review-fixes/08's drain-tournament grep
  — spec archived to `specs/archive/drain-tournament/SPEC.md` after 08
  landed; command passes verbatim at the archived path, and 08's
  acceptance line already carries that annotation. Not a regression.
- 7 items are explicit manual dry-runs (chaining-antipatterns 02,
  code-vs-llm 01, context-management 02, repo-orientation 01,
  task-priority 01, tournament-votes 01, work-tracking 01) — not
  shell-runnable, so not re-run by this sweep; their per-task evidence
  files record how each was handled at completion (context-management
  02's is honestly marked MANUAL / NOT RUN with the box unticked).
- code-vs-llm 01's R8 note ("no command here") records pre-bump version
  0.6.2; this bump lands 0.7.0 > 0.6.2, satisfying work-tracking R8's
  "strictly greater" clause.

## Acceptance

- [x] `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.7.0'"` → exit 0 (single batch bump; pin adjusted from 0.4.0 per step 2 — intervening bumps rf-02/rf-07 landed 0.6.1/0.6.2, minor from current = 0.7.0)
  Evidence: verifier exit 0; single-line minor bump confirmed in diff — evidence/99-version-bump-and-sweep.md
- [x] `claude plugin validate .` → exit 0
  Evidence: verifier "Validation passed", exit 0 — evidence/99-version-bump-and-sweep.md
- [x] Every `## Acceptance` command in `specs/review-fixes/tasks/0*.md` re-run → all exit 0
  Evidence: verifier re-extracted and re-ran independently; all exit 0 except 01's superseded 0.3.0 pin (annotated, criterion-4 exception) and 08's grep, which passes verbatim at the archived drain-tournament path already annotated on 08's line — evidence/99-version-bump-and-sweep.md; see Sweep record
- [x] Every other queue's task acceptances re-run → all exit 0, except version-pin checks annotated in step 5
  Evidence: verifier's independent 132-command batch: 130/132 exit 0, only the two annotated items above failing literally; all 29 other tasks Status: done; run.sh breakdown PASS 1/1 — evidence/99-version-bump-and-sweep.md
- [x] `grep -q "superseded" specs/archive/hardening-quick-wins/tasks/04-scout-idea-version.md || python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.3.0'"` → exit 0 (stale pin annotated iff the bump conflicts with it; path adjusted — hardening-quick-wins was archived after this task was authored)
  Evidence: verifier verbatim run exit 0; path adjustment judged faithful (archive predates this task) — evidence/99-version-bump-and-sweep.md
