# Verification: Task 01 — drain orchestrator exhaustion contract

Verdict: PASS (with process-completeness finding — see below)

## 1. Acceptance commands (run verbatim from worktree root)

1. `grep -qi "dispatchable work remains" .claude/skills/drain/SKILL.md` → PASS
   (matches SKILL.md:19 "Exhaustion contract (R1). So long as dispatchable
   work remains in the launched scope, the session never ends.")
2. `grep -qi "critique intake" .claude/skills/drain/SKILL.md` → PASS
   (section header at SKILL.md:450 "## Critique intake (fires at the
   exhaustion trigger, before 3b)")
3. `grep -q "## Decisions" .claude/skills/drain/SKILL.md` → PASS
   (SKILL.md:357 "drain appends it to the reporting task file under a
   `## Decisions` section"; also cross-referenced at :589, :604)
4. `grep -q "/handoff" .claude/skills/drain/SKILL.md && grep -qi "generations cap" .claude/skills/drain/SKILL.md` → PASS,
   both matches confirmed in the SAME passage (SKILL.md:427-434, "3a. Baton
   pass"): "A max-generations cap of 10 stops with the baton written ...
   The baton is always the first escape ... The /handoff escape applies
   only where the baton cannot: once this generations cap is exhausted ...
   the session writes the /handoff file and leads its exit checklist (step 4) with the resume command instead of continuing degraded." Baton-first
   ordering confirmed by manual read.
5. `grep -qi "checklist" .claude/skills/drain/SKILL.md` → PASS
   (six-section exit checklist at SKILL.md:582-598)
6. `bash evals/lint-ultra-gate.sh` → PASS, exit 0
   Output: "lint-ultra-gate: OK — all ultra mentions gated in 4 files"

## 2. Append-only task-file discipline

Command: `git diff 2ce18add45466d49e1c7f764ab96b820886e4427..HEAD -- '*/tasks/*.md'`

Only one file changed: `specs/work-exhaustion/tasks/01-drain-orchestrator-contract.md`.
The only addition is a `<!-- PLAN (delete at close-out) ... -->` comment
block (16 lines) inserted right after the header fields — this is within
the allowed "plan comment block" category. No other tasks/\*.md file was
touched. No Goal/Steps/Touch/Budget/acceptance TEXT was modified.

FINDING (process completeness, not a criterion FAIL): the `Status:` line
is still `in-progress` (not `done`), no acceptance checkboxes are ticked,
and no evidence-citation lines were added, even though all six acceptance
commands pass and the plan block (marked "delete at close-out") was never
removed. The task was not formally closed out per the worker's own
append-only convention, even though the underlying SKILL.md deliverable is
complete and correct. This does not violate the append-only allow-list
(the block added is a permitted category) but flags that task-file
bookkeeping (Status/checkbox/evidence) was left undone.

## 3. Touch discipline

Command: `git diff --stat 2ce18add45466d49e1c7f764ab96b820886e4427..HEAD`

```
 .claude/skills/drain/SKILL.md                                    | 122 +++++++++++++++++++--
 .../tasks/01-drain-orchestrator-contract.md                      |  16 +++
 2 files changed, 131 insertions(+), 7 deletions(-)
```

Only `.claude/skills/drain/SKILL.md` and the task file changed. Confirmed
untouched (empty diff) for: `.claude/skills/drain/reference.md`,
`.claude/skills/build/SKILL.md`, `.claude/skills/autopilot/SKILL.md`,
`docs/human-gates.md`, `antigravity/`, `.claude-plugin/plugin.json`.

## 4. Semantic spot-check

(a) Exhaustion contract (SKILL.md:19-35, within first 35 lines): states
no-arg launch = whole `specs/` queue, consumed one spec at a time
(sequential walk); lease released "the moment that spec has nothing left
to dispatch"; re-claimed "before re-dispatching" on interview-answer
re-dispatch; transient 3b/critique-intake lease overlap explicitly allowed.
Matches criterion (a).

(b) Critique-intake section (SKILL.md:450-493) sits between "## 3a. Baton
pass" (411) and "## 3b. Auto-breakdown" (494) — immediately before 3b as
required. It claims the spec's owner lease first, invokes `/critique`,
and releases on both READY and NOT READY branches. Once-per-run-across-
generations is stated via the `Intake-failed:` baton line (SKILL.md:483-488),
cross-referenced from 3a's fresh-instance ritual (SKILL.md:442, "critique
intake's set from its `Intake-failed:` line"). Matches criterion (b).

(c) The /handoff passage (SKILL.md:427-434) is baton-first: "The baton is
always the first escape ... The /handoff escape applies only where the
baton cannot: once this generations cap is exhausted." Scoped correctly to
generations-cap exhaustion (also "or in attended /build"). Matches
criterion (c).

(d) Exit checklist (SKILL.md:582-598) has exactly six numbered sections,
each naming a file-path artifact: (1) Deferred questions — task file; (2)
Defaults taken — task file; (3) Blocked items — task file; (4) NOT-READY
specs — SPEC.md path; (5) Draft stubs awaiting promotion — file; (6) Next
commands. Stated "once per session at scope exhaustion." Matches
criterion (d).

No semantic inconsistencies or contradictions found in the changed
regions.

## Scope creep

None found. Diff is confined to `.claude/skills/drain/SKILL.md` (prose
additions per the plan) and the task file's permitted plan-block addition.

## Overall

All six runnable acceptance commands PASS. Append-only and touch
discipline hold. Semantic content matches all four spot-check criteria.
The only deviation is a process-completeness gap in the task file itself
(Status not flipped to done, boxes not ticked, plan block not deleted) —
noted as a finding, not a criterion failure, since the task's own
`## Acceptance` section defines PASS/FAIL purely via the six commands
above.
