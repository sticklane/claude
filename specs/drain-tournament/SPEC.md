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
three concurrent fresh workers in independent worktrees on distinct
branches, same task, each prompted from a different angle. The filter is
the existing verifier PASS/FAIL per candidate; drain ranks survivors
mechanically and merges the winner. Changes touch
`.claude/skills/drain/SKILL.md` (step 3 and the stale-lock text),
`.claude/skills/drain/reference.md` (new `## Tournament` section, one
stale-lock sentence), and `antigravity/.agents/workflows/drain.md`. No
other files — in particular, `.claude/agents/verifier.md` is not
modified; ranking stays out of the verifier.

## Requirements

- R1: drain SKILL.md step 3's DONE bullet routes a second failure into a
  tournament instead of straight to `Status: failed`: 3 concurrent
  background workers, `isolation: worktree`, each carrying the failure
  evidence from the prior attempts. Before dispatch, drain deletes any
  existing `task/NN-<slug>-t*` branches/worktrees (crash leftovers), and
  the stale-lock recovery text (SKILL.md step 1 and reference.md) is
  extended to sweep `-t*` branches/worktrees too.
- R2: reference.md gains a `## Tournament` section with three
  angle-variant suffixes appended to the standard worker prompt, each of
  which ALSO overrides the branch name to `task/NN-<slug>-tN`: (t1)
  minimal-diff — smallest change that passes acceptance; (t2) strict
  test-first — write all acceptance-shaped tests before any
  implementation; (t3) re-derive — reread the task's Goal and Spec
  reference and design from scratch, ignoring the failed approach.
- R3: filter-then-rank, with roles kept separate:
  - Filter: each DONE candidate is verified exactly as in /build — one
    verifier run per candidate, inside that candidate's worktree,
    PASS/FAIL against the task's acceptance criteria — except no
    evidence path is passed (the winner's branch already carries the
    worker's committed evidence file). FAIL = discarded.
  - Rank: drain (not the verifier) orders the PASSing survivors
    mechanically — fewest gate findings in the verifier report, then
    smallest `git diff --stat` total. No new verifier output mode.
  - Merge: winner merges via the normal DONE bookkeeping, EXCEPT the
    slot machine does not re-enter: if the winner's merge or post-merge
    gates fail, drain moves to the next-ranked survivor; survivor
    branches/worktrees are deleted only after some merge passes gates.
    All survivors failing to merge → `Status: failed`, no relaunch.
- R4: verdict routing when not all candidates are DONE: any DEFERRED
  verdict's questions are collected; if no candidate survives the
  filter, then (a) if at least one candidate DEFERRED, drain takes the
  normal DEFERRED path — write all collected questions under
  `## Deferred questions`, `Status: deferred` — in preference to
  `failed`; (b) otherwise `Status: failed` with all three verdicts'
  evidence recorded. BLOCKED candidates are non-survivors whose reason
  goes into the evidence. If a DONE candidate wins, other candidates'
  deferred questions are dropped (the task shipped without needing
  them). A tournament never re-runs for the same task in the same drain
  run, and the `-t*` sweep in R1 makes cross-run re-entry safe.
- R5: cost gate, judged from data drain actually has: the SKILL.md text
  states a tournament costs ~3 more worker runs and is skipped (straight
  to the R4 routing with the two prior verdicts) when either prior
  attempt returned BLOCKED over budget — the one verdict drain holds
  that speaks to budget. The one-line log drain emits when starting a
  tournament states the ~3× cost.
- R6: the antigravity drain workflow mirrors the design: three Agent
  Manager launches (one per angle suffix, each naming its own
  `task/NN-<slug>-tN` branch and worktree, created with
  `git worktree add -b`), the same filter-then-rank collection, the same
  verdict routing and `-t*` sweep.

## Out of scope

- Tournaments in /build or /parallel (attended contexts; the human is
  the escalation path there).
- More than 3 candidates, configurable tournament sizes, or
  behavior-clustering of candidates (AlphaCode's full method) — v1 is
  fixed at 3 with angle diversity.
- Any change to `.claude/agents/verifier.md` (evidence-artifacts spec
  owns verifier changes; this spec only invokes it per-candidate in its
  existing PASS/FAIL mode).
- plugin.json version (owned by the hardening-quick-wins spec).

## Acceptance criteria

- [ ] `grep -qi "tournament" .claude/skills/drain/SKILL.md` and the text places it strictly after the slot-machine relaunch (R1)
- [ ] `grep -qF -- "-t*" .claude/skills/drain/SKILL.md` — stale-lock sweep covers tournament branches (R1)
- [ ] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -c "task/NN-<slug>-t"` ≥ 3 — every angle names its own branch (R2)
- [ ] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -qi "one verifier run per candidate\|per candidate"` and the same section shows drain doing the ranking (diff --stat) (R3)
- [ ] `awk '/^## Tournament/,0' .claude/skills/drain/reference.md | grep -qi "DEFERRED"` — verdict routing present, deferred beats failed (R4)
- [ ] `grep -qi "3 more worker runs\|three more" .claude/skills/drain/SKILL.md` cost gate keyed to prior BLOCKED-over-budget verdicts only (R5)
- [ ] `grep -qi "tournament" antigravity/.agents/workflows/drain.md && grep -q "\-t1\|t1" antigravity/.agents/workflows/drain.md` (R6)
- [ ] End to end: dry-read check — a fresh session asked to execute /drain step 3 against a mock "second failure" verdict describes: sweep `-t*`, dispatch 3 distinct-branch workers, filter by per-candidate verifier PASS/FAIL, rank mechanically, next-ranked on merge failure, DEFERRED-beats-failed routing (manual until the eval harness covers /drain).

## Open questions

(none)
