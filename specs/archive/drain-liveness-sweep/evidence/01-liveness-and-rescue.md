# Verification evidence — Task 01: Liveness-checked sweep, parked tasks, rescue branches

Verdict: **PASS**

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-aa2a65b2b691101b6
Files under test: S=.claude/skills/drain/SKILL.md, R=.claude/skills/drain/reference.md,
A=antigravity/.agents/workflows/drain.md

## Acceptance greps (task file + SPEC)

| Check | Command | Result |
|---|---|---|
| C1 grace window | `grep -qi "grace window" $R` | PASS |
| C2a park both files | `grep -qi park $S && grep -qi park $R` | PASS |
| C2b zombie in R | `grep -qi zombie $R` | PASS |
| C2c 4-extension bound count | `tr -s '[:space:]' ' ' <$R \| grep -o "After 4 consecutive window extensions on the same task" \| wc -l` | 1 (exactly one place; SKILL says "bounded zombie escalation" without restating the number) |
| C3 "15 min" count | `grep -o "15 min" $R \| wc -l` | 1 |
| C4 pid caveat | `grep -qi "not a liveness signal" $R` | PASS |
| C5 rescue pos+neg | `grep -q "rescue/NN-<slug>-" $R && grep -q "rescue/" $S && ! grep -q "discard its branch/worktree" $S && ! grep -q "discard the dead run's worktree/branch" $R` | PASS |
| C6 DONE cleanup S | rescue cleanup in SKILL step-3 DONE bullet (lines 95-97) | PASS |
| C6 DONE cleanup R | reference DONE-bookkeeping passage (lines 59-61) | PASS |
| C7 worker clause | `grep -q "worktree or branch disappears" $R` (lines 152-156, inside prompt block 117-192) | PASS |
| C8 sweep race | `grep -qi "sweep race" $R` | PASS |
| C9 liveness check in S | `grep -q "liveness check" $S` | PASS |
| C10 residual/safety net | `grep -qi residual $R \|\| grep -qi "safety net" $R` | PASS |
| Mirror rescue | `grep -qi rescue $A` | PASS |

Note: the raw C2c grep in the task (`grep -oi "4 consecutive window extensions"`) returns 0
only because the phrase is line-wrapped in reference.md ("window\nextensions"). Whitespace-normalized
it matches exactly once — the bound is present and unique.

## Substance review R1–R10

- R1 PASS — reference.md "Stale-lock liveness check": ordered (1) TaskList/harness, (2) activity
  scan over `task/NN-<slug>` + `task/NN-<slug>-t*` worktrees/branches, newest of file mtimes
  (excl node_modules/.git) AND tip-commit time. All named signals present, correctly ordered.
- R2 PASS — parked flow (R lines 90-107); SKILL step-4 trigger requires "no tasks are parked"
  (line 170) and re-checks each parked task before interview (173-178). 4-extension zombie bound
  in exactly one place (R line 101); zombie-reported task treated like blocked, status stays
  in-progress; park+extension logged one line.
- R3 PASS — 15 min stated once as named default (R 69-70), referenced elsewhere as "the window".
- R4 PASS — pid "not a liveness signal" with spawning-session/`/clear` rationale (R 86-88).
- R5 PASS — rescue-branch procedure in BOTH files (S 40-44, R 46-57): shortsha=tip, tip-dedup,
  pre-existing rescue counts, worktrees force-removed first, forensic-only, post-Filter losers
  unchanged. Old "discard" instructions removed from both (negative greps pass).
- R6 PASS — DONE rescue cleanup in SKILL step-3 DONE bullet (95-97) AND reference (59-61); mirror
  also carries it (A 120-122).
- R7 PASS — vanished-worktree clause inside verbatim worker prompt block (R 152-156): stop, preserve
  as rescue if git permits, exit BLOCKED naming the sweep.
- R8 PASS — "Sweep-race BLOCKED verdict" (R 201-208, S 124-130): never counts toward
  slot-machine/tournament threshold; pending/blocked → re-dispatch; any other status → log+discard,
  rescue branch is durable artifact.
- R9 PASS — SKILL step-1 sentence: "a dead worker's lock ONLY after the liveness check in
  reference.md confirms it" (36-39).
- R10 PASS — residual-risk note (R 109-115): activity can go silent a full window; rescue branch +
  worker clause are the deliberate safety net; heartbeats explicitly rejected.

## E2E scenarios (evaluated by close reading of the two amended files)

- (1) 4-min mtime, TaskList empty → park, keep draining, re-check; NOT sweep. Prose: 4<15min window
  → park (R 82-84, 90-93). Supported unambiguously.
- (2) 40-min activity, TaskList empty → sweep + name rescue/07-<slug>-<shortsha>. Prose: full window
  passed → sweep via rescue procedure (R 46-57, 83-84). Supported.
- (3) parked 4 windows, mtimes refreshing → report suspected zombie, do not sweep. Prose: bounded
  escalation after 4 extensions → report zombie, does NOT silently sweep (R 101-107). Supported.

Method note: verified by reading the amended prose rather than a live fresh-agent dispatch; the three
answers are unambiguously determined by the text.

## Append-only task-file check

Base SHA in the task prompt (7f7dfa09...a52a52...) had a typo; actual HEAD is
`7f7dfa094a92a52557f4d58d58017e9a00e5f8bb` = the base, so no committed task-file changes exist.
All four changed files are uncommitted (working tree). HEAD commit touches only ultra-mode task 01
(unrelated prior queue commit), no drain-liveness-sweep task edits committed.

Working-tree diff of specs/drain-liveness-sweep/tasks/01-liveness-and-rescue.md contains ONLY:
- `Status: pending` → `Status: in-progress`
- inserted `<!-- PLAN (delete at close-out) ... -->` comment block

No changes to Goal / Steps / Touch / Budget / acceptance-criteria text; no checkbox ticks yet.
Matches the permitted append-only set exactly.

## Antigravity mirror semantics

antigravity/.agents/workflows/drain.md carries: liveness check + park (step 1, 23-50), pid caveat
(33-34), 4-extension zombie bound (37-39), rescue-branch preserve/force-remove/dedup/forensic
(44-50), DONE rescue cleanup (120-122), sweep-race routing distinguishing status cases (132-139),
worker vanished-worktree clause (76-80), residual-risk/no-heartbeat note (40-43), step-5 parked-task
re-check + zombie handling (227-234). Full semantic parity.

## Scope

Touched files match the Touch header exactly (SKILL.md, reference.md, antigravity/drain.md, plus the
task file's own Status/plan). No autopilot/parallel/harness/plugin.json edits. No scope creep.
