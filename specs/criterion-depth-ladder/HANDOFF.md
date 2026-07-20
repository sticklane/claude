# HANDOFF — three-spec pipeline (criteria depth / frontier scanner / eval tiers)

## Task

Implement the three proposal specs on PR sticklane/claude#19 (draft),
branch `claude/verification-criteria-depth-w9lofa`:
`specs/criterion-depth-ladder` (6 tasks), `specs/drain-frontier-scanner`
(4 tasks), `specs/eval-coverage-tiers` (8 tasks). All three are
critiqued (`Breakdown-ready: true`; verdicts + spec hashes in each
spec's `critique-findings.md`) and broken down. Maintainer authorized
the full pipeline including drain ("do it all", 2026-07-19).

## State

- DONE: ladder task 01 — depth ladder + trivially-satisfiable pattern
  landed in `docs/memory/anchored-acceptance-criteria.md`; merged with
  verifier PASS (`evidence/01-doctrine-depth-ladder.md`). Draft stub
  `tasks/07-memory-index-refresh.md` created from its discovery.
- PENDING: ladder 02–06 (02/03/04 were in-flight; workers died in a
  harness reconnect with zero commits — swept, Progress entries
  recorded, reset to pending; lease released). Scanner 01–04 and tiers
  01–08 untouched.
- EXACT NEXT STEP: `/drain specs/criterion-depth-ladder` (resumes at
  02/03/04 — one Group line, `Parallel-window: 3`), then
  `/drain specs/drain-frontier-scanner`, then
  `/drain specs/eval-coverage-tiers`.
- After the drains: refresh PR #19's stale body (still says
  "pre-critique"); all paid `./evals/run.sh` executions are
  manual-pending, human-launched.
- Earlier this session (already landed, pushed): criteria remediation
  sweep over all unimplemented specs (4 sweep commits + grandfathering
  commit), HUMAN.md blocker filed re: `Status: obsolete` vocabulary.

## Files touched (groups)

- `specs/{criterion-depth-ladder,drain-frontier-scanner,eval-coverage-tiers}/`
  — SPEC.md + tasks/ + critique-findings.md (+ ladder evidence/).
- 12 unimplemented spec dirs — anchored/deepened acceptance criteria.
- `docs/memory/anchored-acceptance-criteria.md` — task 01 implementation.
- `HUMAN.md` — one new agent-filed `decide` blocker.

## Gotchas

- This session's branch stands in for `main` everywhere drain says
  default-branch; NEVER push to any other branch.
- A formatter hook rewraps every written spec/task file — re-read a
  region before editing it again; quoted anchor phrases can gain line
  breaks.
- Worker agents did not survive a harness reconnect (died silently,
  branches at dispatch base). Check `git worktree list` + branch tips
  before trusting live workers.
- `evals/lint-skill-size-gate.sh` FAILS today on drain/SKILL.md (505
  lines, pre-existing; `specs/drain-hub-context-discipline` owns it).
  Scanner task 02 must add minimal lines; treat the size gate as
  no-NEW-failure there.
- Foreign stale lease `specs/commit-message-doctrine/DRAIN-OWNER.md`
  predates this session — out of scope, leave alone.
- `send_later` (claude-code-remote) failed repeatedly after the
  reconnect; the hourly PR check-in is NOT re-armed. Re-verify the PR
  subscription when resuming.

## Verification

- Ladder 01: independent verifier PASS, report committed; both anchor
  greps now ≥ 1; doc-links gate 16/0.
- Specs: three critic rounds each, settled READY WITH NITS; hashes in
  `critique-findings.md` enable /critique's re-run skip.
- Remediation sweep: every rewritten anchor re-verified against the
  tree at authoring (dates inline in each criterion).
- CI: green at every push so far; latest wind-down commits re-run it.
