# Evidence: Task 03 — Task-file header contract

Verdict: PASS
Verified: 2026-07-03, branch task/03-header-contract, HEAD b887d47 (changes in working tree, uncommitted)
Verifier: independent verification agent (did not write this code)

## Acceptance criteria

All commands run from repo root /Users/sjaconette/claude/.claude/worktrees/agent-ac6623e302f3861c0.

### A1 ✓ Template Touch header line
Command: `grep -q "^Touch:" .claude/skills/breakdown/SKILL.md`
Exit: 0. Line added in the header block of the task template:
`Touch: <comma-separated paths this task may change>` — sits after `Spec:` and above the first `##` (`## Goal`).

### A2 ✓ Optional ## Touch body section retained
Command: `grep -q "## Touch" .claude/skills/breakdown/SKILL.md`
Exit: 0. `## Touch` section retained, reworded as optional prose:
"Optional prose on boundaries (why a path is in or out). Dispatchers parse the `Touch:` header line above, not this section; anything not listed there is scope creep."

### A3 ✓ Drain inventory lists all five headers
Command: `grep -q "Budget" .claude/skills/drain/SKILL.md && grep -qE '\(.?Status.?, .?Depends on.?, .?Priority.?, .?Budget.?, .?Touch.?\)' .claude/skills/drain/SKILL.md`
Exit: 0. Inventory paragraph now reads:
"(`Status`, `Depends on`, `Priority`, `Budget`, `Touch`) — not the bodies; ... `Budget` feeds the worker's over-budget stop and the headless `--max-turns` cap; `Priority` is an optional tie-break (absent = P2)."
Budget and Priority consumption both noted, as Step 2 requires.

### A4 ✓ Plan-block placement pinned below header lines
Command: `grep -qi "below the header lines" .claude/skills/build/SKILL.md`
Exit: 0. Single occurrence at line 28, inside `## 1. Plan proportionally`:
"...as a comment block in the task file, placed below the header lines (never between them — dispatchers parse the headers and the block must not break them)."

### A5 ✓ Close-out deletes the plan block — and the sentence IS in close-out
Command: `grep -qi "delete" .claude/skills/build/SKILL.md`
Exit: 0. Location check: `grep -ni "delete" .claude/skills/build/SKILL.md` → exactly one match, line 76:
"...rather than duplicating output; delete the plan comment block from step 1."
Section map: `## 4. Close out` starts at line 67; next content runs to EOF region — line 76 is inside close-out. No "delete" occurrences elsewhere in the file.

### A6 ✓ Antigravity mirrors
Command: `grep -q "^Touch:" antigravity/.agents/skills/breakdown/SKILL.md && grep -q "Budget" antigravity/.agents/workflows/drain.md && grep -qi "below the header lines" antigravity/.agents/workflows/build.md`
Exit: 0.

## Steps 1–4 honored (diff inspection, `git diff HEAD`)

1. Breakdown template: `Touch:` header line above first `##`; `## Touch` retained as optional prose; states dispatchers parse the header line. ✓
2. Drain inventory: five-header parenthesized list; Budget → over-budget stop + headless `--max-turns`; Priority → optional tie-break, absent = P2. ✓
3. Build step 1 pins the plan block below header lines; build close-out (## 4) deletes the plan block. ✓
4. All three antigravity mirrors carry the same changes:
   - antigravity/.agents/skills/breakdown/SKILL.md — identical template change (Touch: line + optional ## Touch prose).
   - antigravity/.agents/workflows/drain.md — five-header list, Budget over-budget stop, Priority tie-break (absent = P2). Omits the `--max-turns` clause, a reasonable port adaptation (Antigravity has no headless flag).
   - antigravity/.agents/workflows/build.md — plan block below header lines in step 2; close-out says "delete the plan comment block from step 2" (correct step number for that file's numbering).

## Gates

- Evals: `./evals/run.sh breakdown` (breakdown is a changed skill with a stored evalset) → exit 0, `PASS breakdown/01-small-spec`, "1/1 scenarios passed".
- No other build/lint/test gates exist in this repo (prose/skill repo; drain and build have no evalsets under evals/).

## Scope creep

None. `git status --porcelain` shows exactly the six Touch-listed files plus the task file itself. The task-file change is the plan comment block placed below its header lines (build step 1 behavior; expected to be deleted at close-out — task is still `Status: in-progress`, boxes unticked, consistent with a pre-close-out verification pass).

Note for close-out: repo CLAUDE.md says to bump `version` in `.claude-plugin/plugin.json` on skill behavior changes. The implementer correctly did NOT edit it — plugin.json is outside this task's binding Touch list — but the convention exists and the orchestrator may want a follow-up.

## Overfitting check

Not a code task; grep criteria are structural. The prose is general (no test-input special-casing possible). A3's regex requires the exact backticked five-header list; the drain text satisfies it with natural sentence structure, not a keyword stuffed to game the grep — the surrounding paragraph explains consumption of each header.
