# Task 06: Whole-tree verification, plugin.json version bump, sequencing check

Status: in-progress
Depends on: 01, 02, 03, 04, 05
Priority: P1
Budget: 5 turns
Spec: ../SPEC.md (requirement R8, R6's manifest replacement line, plus the spec's whole-tree AC and sequencing note)
Touch: .claude-plugin/plugin.json, tests/mirror-procedure-manifest.txt

## Goal

`.claude-plugin/plugin.json`'s version is bumped. The whole-tree verifying
grep confirms every `/autopilot` reference outside the four exempt files
has been reworded or deleted. The mirror-coverage manifest's replacement
pairing line (deferred from Task 03, since it needs both build legs
landed) is added. The sequencing constraint against the sibling
`build-doc-currency-check` spec is confirmed clear before this spec is
considered complete.

## Touch

Only `.claude-plugin/plugin.json` and `tests/mirror-procedure-manifest.txt`
(one new line, added below). This task does not otherwise edit any file
Tasks 01-05 already swept.

## Steps

1. Confirm `specs/build-doc-currency-check` has no task `in-progress` or
   merged against `.claude/skills/build/SKILL.md` concurrently with this
   spec's own edits to that file — check its `SPEC.md`/`tasks/` state
   directly (`ls specs/build-doc-currency-check/tasks/ 2>/dev/null`, and
   grep any existing task files' `Status:` lines). If any task is found
   in-progress or merged against that file, STOP and report DEFERRED with
   this exact finding rather than proceeding — this is the hard
   sequencing constraint the spec's Problem section states, not a
   judgment call.
2. Run the whole-tree verifying grep:
   `git grep -ln '\bautopilot\b' -- .claude/ docs/ CLAUDE.md .claude-plugin/ codex/ antigravity/ evals/ runtimes/ README.md AGENTS.md bin/ tests/ agent-console/`
   and confirm it returns exactly the four exempt files.
3. Add the mirror-coverage replacement pairing line to
   `tests/mirror-procedure-manifest.txt`:
   `.claude/skills/build/SKILL.md|antigravity/.agents/workflows/build.md|Two triggers escalate to a human`.
   This was deliberately deferred from Task 03 (which only deleted the old
   autopilot→autopilot.md line) because this line's mirror side only
   exists once Task 04 has landed; by this point both Task 01's and Task
   04's fold-ins are merged, so the phrase is present in both legs — confirm
   with `grep -qF 'Two triggers escalate to a human' .claude/skills/build/SKILL.md antigravity/.agents/workflows/build.md`
   before adding the line.
4. Bump `.claude-plugin/plugin.json`'s `version` field (increment the
   patch component unless a prior task already changed skill behavior in
   a way that warrants a minor bump — this spec's changes are a skill
   retirement/fold, so a patch bump is the default).
5. Record the manual-pending item as evidence (not an automated check): a
   human must wrap `/build` against a fixture task in
   `/goal "tests pass, or stop after 5 turns"` and confirm it completes
   within the cap, following the classification gate and escalation
   triggers now documented in `build/SKILL.md` — this cannot be verified
   by an unattended worker (`/build` requires live-conversation launch
   authorization). Note this explicitly in the task's evidence rather than
   silently skipping it.

## Acceptance

- [ ] `git grep -ln '\bautopilot\b' -- .claude/ docs/ CLAUDE.md .claude-plugin/ codex/ antigravity/ evals/ runtimes/ README.md AGENTS.md bin/ tests/ agent-console/`
      returns exactly the 4 files: `docs/orchestration-research-2026-07.md`,
      `.claude/rules/mirror-procedure-discipline.md`,
      `tests/mirror-procedure-manifest.txt`, `tests/test_check_token_discipline.sh`.
- [ ] `grep -qF '.claude/skills/build/SKILL.md|antigravity/.agents/workflows/build.md|Two triggers escalate to a human' tests/mirror-procedure-manifest.txt`
- [ ] `.claude-plugin/plugin.json`'s version is higher than its value at
      this task's own base commit (`git show <base-commit>:.claude-plugin/plugin.json | grep version`
      compared against the current value — not a hard-coded prior literal,
      since a sibling task landing first could already have bumped it).
- [ ] **Manual-pending**: the `/goal`-bounded fixture-task confirmation
      (Step 5) is recorded as evidence, not an automated check — a human
      action, not something this task can complete unattended.
- [ ] **Sequencing**: this task's own evidence states explicitly that
      `specs/build-doc-currency-check` had no `in-progress` or merged task
      against `build/SKILL.md` at the time this task ran (Step 1) — cite
      the check's output, not just a claim.
