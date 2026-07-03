# Tournament mode for /drain (generate–filter–rank)

## Problem

/drain currently gives a failing task two attempts (initial + one
slot-machine relaunch) and then marks it `failed`, parking work until a
human returns — on exactly the tasks where unattended progress matters
most. AlphaCode 2's generate–filter–rank result (~2× solve rate from
sampling diverse candidates and ranking survivors; see
docs/external-playbooks.md, "Generate–filter–rank") points at a bounded
third stage: sample wider before giving up.

## Solution

After the slot-machine relaunch also fails, /drain runs one tournament:
three concurrent fresh workers in independent worktrees, same task, each
prompted from a different angle, ranked by the verifier; the winner
merges, the rest are discarded, and only an empty field marks the task
`failed`. Changes touch `.claude/skills/drain/SKILL.md` step 3,
`.claude/skills/drain/reference.md` (new Tournament section), and the
antigravity drain workflow.

## Requirements

- R1: drain SKILL.md step 3's DONE bullet routes a second failure into a
  tournament instead of straight to `Status: failed`: 3 concurrent
  background workers, `isolation: worktree`, distinct branch names
  (`task/NN-<slug>-t1..t3`), each carrying the failure evidence from the
  prior attempts.
- R2: reference.md gains a Tournament section with three angle-variant
  prompt suffixes appended to the standard worker prompt: (t1)
  minimal-diff — smallest change that passes acceptance; (t2) strict
  test-first — write all acceptance-shaped tests before any
  implementation; (t3) re-derive — reread the task's Goal and Spec
  reference and design from scratch, ignoring the failed approach.
- R3: ranking is filter-then-rank: candidates whose acceptance commands
  do not all pass are discarded without ranking; survivors are ranked by
  the verifier agent (given the diffs and evidence) on gate cleanliness,
  then diff size (smaller wins ties). The winner merges via drain's
  normal step-3 DONE path; losing branches and worktrees are deleted.
- R4: zero survivors → `Status: failed` with all three verdicts' evidence
  recorded; the tournament never re-runs for the same task in the same
  drain run.
- R5: cost gate: the SKILL.md text states a tournament costs ~3 worker
  runs and is skipped (straight to `failed`) when the task file's
  `Budget:` line, if present, is already exhausted; the one-line log
  drain emits when starting a tournament says so.
- R6: the antigravity drain workflow mirrors the design: the workflow
  hands the user three Agent Manager launches (one per angle suffix) and
  runs the same filter-then-rank collection.

## Out of scope

- Tournaments in /build or /parallel (attended contexts; the human is
  the escalation path there).
- More than 3 candidates, configurable tournament sizes, or
  behavior-clustering of candidates (AlphaCode's full method) — v1 is
  fixed at 3 with angle diversity.
- plugin.json version (owned by the hardening-quick-wins spec).

## Acceptance criteria

- [ ] `grep -qi "tournament" .claude/skills/drain/SKILL.md` and the text places it strictly after the slot-machine relaunch (R1)
- [ ] `grep -c "t1\|t2\|t3" .claude/skills/drain/reference.md` ≥ 3 with three distinct angle suffixes present (R2)
- [ ] `grep -qi "acceptance" .claude/skills/drain/reference.md` in the Tournament section — discard-before-rank is explicit, verifier ranks survivors only (R3)
- [ ] Tournament section states zero-survivors → `failed` + no repeat within a run (R4)
- [ ] `grep -qi "budget" .claude/skills/drain/SKILL.md` in the tournament sentence (R5)
- [ ] `grep -qi "tournament" antigravity/.agents/workflows/drain.md` (R6)
- [ ] End to end: dry-read check — a fresh session asked to execute /drain step 3 against a mock "second failure" verdict describes dispatching 3 angle-variant workers and filter-then-rank, without inventing unspecified behavior (manual until the eval harness covers /drain).

## Open questions

(none)
