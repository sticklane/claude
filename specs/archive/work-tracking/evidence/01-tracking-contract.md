# Verification: Task 01 — tracking contract (work-tracking)

Verdict: PASS
Verified: 2026-07-03, working tree of branch task/01-tracking-contract
(uncommitted changes vs base 51a12de). Verifier had no part in the
implementation.

## Acceptance criteria

All greps run from repo root
`/Users/sjaconette/claude/.claude/worktrees/agent-aa2d085991f37dadf`.

### [x] R1 — worker report contract
Command:
`grep -q "Discovered:" .claude/skills/drain/reference.md && grep -q "Discovered:" .claude/skills/build/SKILL.md`
Result: exit 0.
Content check: reference.md worker prompt gains the fixed `Discovered:`
section ("what + where + why it matters", empty means none, NEVER
create/edit task files for discoveries) and the `Done vs remaining:`
line for non-DONE verdicts; the DEFERRED sentence is amended to "the
verdict plus these two fixed sections are all the orchestrator will
ever see". The headless prompt template mirrors both sections.
build/SKILL.md report step ends with the same fixed sections.

### [x] R2 — drain materializes drafts
Command:
`grep -q "Status: draft" .claude/skills/drain/SKILL.md && grep -qi "dedup" ... && grep -q "Discovered-by:" ... && grep -q "only a human" ... && grep -qi "never dispatchable" ... && grep -qi "vet" .claude/skills/drain/SKILL.md`
Result: exit 0 (all six clauses).
Content check: "Materialize discoveries" step in drain SKILL.md step 3:
title-line dedupe against the reporting task's spec tasks/ dir first;
header-only stub `NN-<kebab-slug>.md` with `Status: draft`,
`Depends on: none`, `Spec: ../SPEC.md`, `Discovered-by:` line, Goal
quoting the worker verbatim under "verbatim worker report — vet/rewrite
before promoting"; committed with the next bookkeeping commit (verdict
flip, or post-merge for DONE); drain never writes a draft's Status, not
even on an interview yes; final report lists drafts created. Step 1's
dispatchable definition explicitly excludes `Status: draft`.

### [x] R3 — attended capture
Command: `grep -q "only on the user's yes" .claude/skills/build/SKILL.md`
Result: exit 0.
Content check: /build closing step offers a `Status: draft` stub per
Discovered item, "written only on the user's yes; no silent queue
writes".

### [x] R4 — append-only task files
Command:
`grep -q "may flip only" .claude/skills/drain/reference.md && grep -q "may flip only" .claude/skills/breakdown/SKILL.md && grep -qi "git diff" .claude/agents/verifier.md && grep -q "merge-base" .claude/skills/drain/SKILL.md`
Result: exit 0.
Content check: reference.md worker prompt carries the "may flip only"
rule (own Status line, checkboxes, evidence lines, plan block;
Goal/Steps/Touch/Budget/criterion text read-only in every task file;
## Progress / ## Deferred questions drain-written). breakdown template
gains the same note as a comment. verifier.md gains mechanical step 6:
`git diff <base> -- '*/tasks/*.md'` with defined base (caller-passed
commit, or worktree merge-base with default branch), whitelist,
automatic FAIL otherwise. drain SKILL.md DONE collection re-runs the
same whitelist diff over `merge-base..branch` before merging, routing
violations to the merge-failure/slot-machine path. build SKILL.md
step 0 records `git rev-parse HEAD` and step 3 passes it to the
verifier.

### [x] R5 — stopping points
Command:
`grep -q "## Progress" .claude/skills/drain/SKILL.md && grep -qi "done vs remaining" .claude/skills/drain/SKILL.md`
Result: exit 0.
Content check: "Record stopping points" covers all four spec events
(BLOCKED incl. over budget, DEFERRED, DONE-candidate verification
failure, tournament entry, terminal failed); one dated line block, done
vs remaining, sourced from the worker's `Done vs remaining:` line or
the verifier's report; written in the main checkout before any
relaunch/tournament; the relaunch prompt in reference.md now cites the
`## Progress` entry.

### [x] R7 — antigravity mirrors
Command:
`grep -q "Discovered:" antigravity/.agents/workflows/drain.md && grep -q "merge-base" antigravity/.agents/workflows/drain.md && grep -q "may flip only" antigravity/.agents/skills/breakdown/SKILL.md && grep -qi "git diff" antigravity/.agents/skills/verifier/SKILL.md`
Result: exit 0.
Content check: workflows/drain.md mirrors R1 (report sections in
worker prompt), R2 (materialize-discoveries paragraph incl. dedupe,
vet/rewrite label, never dispatchable, only-a-human), R5 (record
stopping points), and R4's merge-time `merge-base..branch` re-check.
workflows/build.md mirrors R1 + R3 ("only on the user's yes").
Breakdown mirror is the SKILL (template note), NOT the 5-line workflow
shim — per R7. Verifier skill mirror gains the same mechanical step 6.

### [x] Manual paper dry-run (judged from the edited skill texts)
Walkthrough of a BLOCKED worker with one Discovered item against
.claude/skills/drain/SKILL.md + reference.md (and the antigravity
mirror):
- Worker report carries `Discovered:` (one item) + `Done vs remaining:`
  (reference.md prompt mandates both for non-DONE) → drain's
  "Materialize discoveries" writes exactly ONE `Status: draft` stub,
  Goal quoting the line verbatim under the "verbatim worker report —
  vet/rewrite before promoting" label. ✓
- "Record stopping points" fires on BLOCKED → one `## Progress`
  done-vs-remaining entry in the main-checkout task file. ✓
- Stub commits "with drain's next bookkeeping commit for that task —
  the verdict flip"; Progress written before relaunch and drain commits
  every mutation → one bookkeeping commit with the status flip. ✓
- Second identical discovery → title-line dedupe ("first compare
  against the TITLE lines ... check the list first") → no second stub. ✓
- Draft never dispatchable: step 1 defines dispatchable as
  `Status: pending` + deps done and explicitly says draft stubs are
  never dispatchable; materialize step repeats it. ✓
- Drain never flips a draft: "drain never writes a draft's `Status:` —
  not even on an interview yes: only a human edits `draft` →
  `pending`". ✓

## Gates

- `./evals/run.sh breakdown` → `1/1 scenarios passed` (PASS
  breakdown/01-small-spec), re-run independently by this verifier.

## Scope creep / append-only check

- `git status --porcelain`: exactly the 9 Touch-list files + the task
  file. No other modifications.
- `git diff 51a12de -- '*/tasks/*.md'`: changes only in
  specs/work-tracking/tasks/01-tracking-contract.md, and only the plan
  comment block (Status: in-progress was already at base). Allowed set
  respected; no criterion text touched; checkboxes left unticked (they
  are ticked by this verification, evidenced here).
- plugin.json NOT bumped: deliberate — R8 is outside this task's scoped
  requirements (task header scopes R1–R5, R7) and plugin.json is
  outside Touch. Finding (not a failure): CLAUDE.md's "bump version in
  plugin.json whenever skill behavior changes" convention is
  unsatisfied by this working tree; the plan block routes R8 to the
  commit-set bump — reported here per the convention rather than
  edited.
- No test/eval files were modified; the greps cannot pass vacuously
  (spec Solution section confirms marker phrases did not pre-exist;
  spot-checked: all six marker phrases are additions in this diff).
