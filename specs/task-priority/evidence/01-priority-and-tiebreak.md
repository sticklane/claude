# Verification evidence: task-priority 01-priority-and-tiebreak

Verdict: PASS
Verified: 2026-07-03, worktree /Users/sjaconette/claude/.claude/worktrees/agent-a1ab37be29ee10ddb, branch task/01-priority-and-tiebreak (HEAD a542eee + 4 uncommitted file edits)
Scope: SPEC.md requirements R1, R2, R3, R5 only (R4/R6 owned by other tasks; no plugin.json bump expected — rf-99 owns it).

## Acceptance criteria

### 1. R1+R3 grep — PASS (exit 0)

Command (from worktree root):

    grep -q "Priority: P2" .claude/skills/breakdown/SKILL.md \
      && grep -q "P0" .claude/skills/breakdown/SKILL.md \
      && grep -qi "unblocking" .claude/skills/breakdown/SKILL.md

Output: none (exit code 0).

### 2. R2 grep — PASS (exit 0)

Command:

    grep -q "tie-break" .claude/skills/drain/SKILL.md \
      && grep -q "Priority" .claude/skills/drain/SKILL.md \
      && grep -qi "unblocking" .claude/skills/drain/SKILL.md

Output: none (exit code 0).

### 3. R5 grep — PASS (exit 0)

Command:

    grep -q "Priority" antigravity/.agents/skills/breakdown/SKILL.md \
      && grep -qi "tie-break" antigravity/.agents/workflows/drain.md

Output: none (exit code 0).

### 4. Manual paper dry-run — PASS

Rule text evaluated as written in .claude/skills/drain/SKILL.md (section
"## 2. Dispatch one worker", lines 45-53): dispatch lowest `Priority`
value first (absent = P2), then greatest unblocking-power (count of
still-`pending` tasks whose `Depends on:` names this task, counted over
this run's inventory, resolving `Depends on:` exactly as the
dispatchability check does), then lexicographic task-file path.

Scenario: A (Priority: P1, 0 pending dependents), B (no header, 3
pending dependents), C (no header, 0 dependents, lexicographically
earliest path).

- Stage 1 (Priority): A=P1; B, C absent -> P2. A dispatches first.
- Stage 2 (unblocking-power, B vs C at equal P2): B=3 > C=0, so B
  before C. The lexicographic backstop is reached only on a further
  tie, so C's earlier path cannot promote it.
- Result: A, B, C — matches expected order.
- With A absent: B vs C resolves at stage 2, B first — matches.

antigravity/.agents/workflows/drain.md step 2 carries the identical
tie-break sentence, so the mirror yields the same order.

## Substance checks (beyond greps)

- R1: .claude/skills/breakdown/SKILL.md template has `Priority: P2`
  among the header lines (between `Depends on:` and `Budget:`, above the
  first `##`), plus the comment line "Priority values run P0 (highest)
  through P3; the header is optional — absent means P2." Confirmed via
  `git diff main`.
- R3: ordering step (step 4) has the four-line rubric — P0
  repair/unblocking or riskiest assumption; P1 longest remaining
  dependency chain; P2 default; P3 cleanup/nice-to-have — plus "The
  human may re-prioritize at any time by editing the headers."
- R2: tie-break sentence sits in drain's dispatch section, names
  Priority (absent = P2), unblocking-power counted over this run's
  inventory resolving `Depends on:` as the dispatchability check does
  (numbers within a spec, task-file-relative paths across specs), then
  lexicographic path; ends "the model never reorders the queue mid-run."
  Drain's inventory header list already includes `Priority` (line 27,
  landed by rf-03).
- R5: antigravity/.agents/skills/breakdown/SKILL.md mirrors the R1
  comment+header line and the R3 rubric verbatim;
  antigravity/.agents/workflows/drain.md mirrors the R2 sentence. The
  5-line shim antigravity/.agents/workflows/breakdown.md is NOT edited
  (git diff main --name-only on it is empty), as R5 requires.

## Standard gates

- `evals/run.sh breakdown` — PASS. Output tail:

      assert: all checks passed (2 task files)
      PASS  breakdown/01-small-spec
      ----
      1/1 scenarios passed

  (exit 0). No stored evalset exists for drain.

## Scope creep

None. `git diff main --stat` touches exactly the four Touch-list files:

    .claude/skills/breakdown/SKILL.md             | 11 +
    .claude/skills/drain/SKILL.md                 |  9 +
    antigravity/.agents/skills/breakdown/SKILL.md | 11 +
    antigravity/.agents/workflows/drain.md        | 10 +

plugin.json is not bumped — correct per the task file ("rf-99 owns it"),
overriding the repo convention to bump on skill-behavior changes.

## Overfitting check

The changes are prose/contract edits, not code; the grep markers
("tie-break", "Priority: P2", "unblocking") appear inside full,
substantive rubric/tie-break text matching the spec's exact wording, not
as bare marker strings. No test files exist for this task to have been
modified.
