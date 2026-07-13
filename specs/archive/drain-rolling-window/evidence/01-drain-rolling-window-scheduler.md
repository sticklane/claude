# Verification: Task 01 — drain rolling-window scheduler

Verdict: PASS (with a process finding — see below)

## Append-only task-file check

Command: `git diff 5e8fc23 -- '*/tasks/*.md'`

Result: only the task's own PLAN comment block (lines 14-32) was added.
Status line unchanged (`Status: in-progress`), no acceptance checkboxes
ticked, no evidence-citation lines added. Goal/Steps/Touch/Budget/
Acceptance text is byte-identical to base. This is within the allowed set
(plan comment block is sanctioned) — no criterion text or other task's
file was touched.

**Process finding (not a criterion failure):** the worker did not tick any
`## Acceptance` checkboxes or add evidence-citation lines, and left
`Status: in-progress` even though the underlying SKILL.md/reference.md edits
are present and (per the grep evidence below) satisfy every acceptance
criterion. Per this repo's convention ("worker may flip only its own task's
Status: line, tick acceptance checkboxes and add evidence-citation lines")
this task file should have been updated to reflect completion; it wasn't.
Work itself is also uncommitted (git status shows SKILL.md, reference.md,
and the task file as unstaged modifications) — no commit was made per the
"Commit on Task Completion" convention.

## Acceptance criteria — run individually against the working tree

1. `grep -c 'Parallel-window' .claude/skills/drain/SKILL.md` → **1** (≥1) ✓
2. `grep -c '^- Group:\|Group:' .claude/skills/drain/SKILL.md` → **5** (≥1) ✓
3. `grep -n 'Group throughput mode' .claude/skills/drain/SKILL.md` → **no output** (heading gone) ✓
4. `grep -c "DRAIN-OWNER" .claude/skills/drain/SKILL.md` → **5** (≥2) ✓
5. `grep -n "compare-and-swap\|exact-match" .claude/skills/drain/SKILL.md` → non-empty:
   ```
   58:itself compare-and-swap: immediately after committing, re-read the file
   207:**The flip is compare-and-swap.** Re-read the task file immediately
   208:before flipping — the flip is an exact-match edit of the literal
   ```
   ✓
6. `grep -c "pull --rebase" .claude/skills/drain/SKILL.md` → **1** (≥1) ✓
7. `grep -c "Run-token" .claude/skills/drain/reference.md` → **5** (≥2) ✓
8. `grep -ci "tournament" .claude/skills/drain/reference.md` → **24** (≥1) ✓, and
   `grep -ci "emptied\|empty window\|window-empty" .claude/skills/drain/reference.md` → **3** (≥1) ✓
9. `grep -ci "zombie" .claude/skills/drain/reference.md` → **16** (≥1) ✓, and
   `grep -ci "blocked by suspected zombie" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` →
   `SKILL.md:0`, `reference.md:1` — reference.md contributes ≥1 ✓
10. `grep -ci "top.up\|re-computes admission\|refills the window" .claude/skills/drain/SKILL.md` → **2** (≥1) ✓
11. `grep -ci "scratch worktree\|throwaway.*worktree" .claude/skills/drain/SKILL.md` → **1** (≥1) ✓
12. `grep -ci "subset of the task" .claude/skills/drain/SKILL.md` → **1** (≥1) ✓, and
    `grep -ci "merge failure\|slot.machine" .claude/skills/drain/SKILL.md` → **8** (≥1) ✓

**All 12 acceptance criteria: PASS.**

## Semantic sanity checks

- **Group throughput mode replaced by rolling-window prose.** Confirmed via
  `git diff 5e8fc23 -- .claude/skills/drain/SKILL.md`: the "Sequential by
  default" + "**Group throughput mode**" paragraph (old lines ~124-149) is
  replaced by "**Rolling window of W workers**" prose that explicitly
  covers: window size W (default 1, `Parallel-window: N` header, explicit
  user override, hard cap 5) — R1; claim set + co-admissibility +
  `Group:` line grammar (cites specs/drain-rolling-window/SPEC.md) — R1;
  "Top-up on verdict, not on wave (R2)"; "Serial merge queue with mechanical
  rebase recovery (R3)" including the throwaway scratch worktree; "Runtime
  Touch enforcement at merge (R4)" naming subset-of-Touch and merge failure.
  Confirmed present.

- **Out-of-scope sections unchanged.** `git diff 5e8fc23 -- .claude/skills/drain/SKILL.md`
  shows the only hunk is inside "## 2. Dispatch"; the "**The flip is
  compare-and-swap.**" subsection and headings "## 1. Inventory",
  "## 3. Collect the verdict", "## 3a. Baton pass (self-relaunch)" appear
  with no diff hunks touching them (confirmed both via the diff output and
  `grep -n "^## 1. Inventory\|^## 3. Collect the verdict\|^## 3a. Baton pass"`
  which found all three headings intact at lines 43, 230, 353).
  `git diff 5e8fc23 -- .claude/skills/drain/reference.md | grep -n "Owner lease\|Run-token\|DRAIN-OWNER"`
  → no matches, confirming those sections are untouched by this diff.

- **reference.md new R8/R8a/R9.2/R9.3 content.** `git diff 5e8fc23 -- .claude/skills/drain/reference.md`
  shows: a new "**Window-slot vs. Touch claim (R9.2)**" bullet ("blocked by
  suspected zombie `<task>`", slot released / Touch claim persists) plus a
  new "**Termination (R9): no deadlock, no livelock**" block with an
  explicit "**termination check (R9.3)**" subsection, both added under the
  Stale-lock liveness check's zombie bullet; a new
  "**Emptied-window dispatch (R8a)**" paragraph under "## Tournament"
  (exactly 3 workers regardless of W); and a new
  "**Drain-down before the baton (R8)**" paragraph under
  "## Baton pass (self-relaunch)" (stops admitting, waits for every
  in-flight verdict, writes baton only at window-empty quiescence, verdict
  counter counts recorded verdicts regardless of window size). All four
  match the task's Steps 6-9 description. Confirmed present.

## Scope / gates

- `git status --porcelain` → only `.claude/skills/drain/SKILL.md`,
  `.claude/skills/drain/reference.md`, and this task's own file are
  modified. No antigravity mirror or plugin.json touched (correctly
  deferred to task 05 per the plan block) — no scope creep.
- No `specs/drain-rolling-window/evidence/` directory exists yet (the
  worker did not create one, consistent with not having ticked evidence
  lines in the task file).
- This repo's skills are prose/markdown; there is no `scripts/check.sh` /
  lint/build gate applicable to a markdown-only Touch set, and none was
  found required by the task file.

## Conclusion

Every one of the 12 grep-based acceptance criteria passes exactly as
specified, and the semantic rewrite (rolling window replacing the strict
group barrier, R1-R4 in SKILL.md, R8/R8a/R9.2/R9.3 in reference.md, and all
named out-of-scope sections left byte-for-byte untouched) is verified by
direct diff inspection. The task-file diff against base is append-only
(plan block only). The verdict is **PASS** on the acceptance criteria
proper; the process finding above (task file not marked done, work not
committed) should be resolved before this task is considered closed.
