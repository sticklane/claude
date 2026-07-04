# Task 01: push-on-completion for drain / build / parallel

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: pending
Depends on: none
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md
Touch: .claude/skills/drain/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/parallel/SKILL.md, .claude/skills/autopilot/SKILL.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/build.md, antigravity/.agents/workflows/parallel.md, .claude-plugin/plugin.json

## Goal

Add a push-on-completion step to the three attended execution stages so a
completed, verifier-PASSED task is pushed the moment it merges to `main`,
instead of sitting on local `main` until a human pushes by hand. Autopilot is
deliberately excluded (unattended; push stays human-escalated). See ../SPEC.md
for the defect map and per-skill line anchors.

## Answers

**Decisions (interview 2026-07-04):**

- **Per completed task, not batched at run end** — push immediately after each
  DONE merge so finished work is backed up as it lands.
- **Attended stages only** — drain, build, parallel push; autopilot keeps
  escalating push to the human (its `SKILL.md:28`/`:53` prohibition is a
  safety invariant, not an oversight).
- **Orchestrator/session pushes, never the worker** — drain's worker prompt
  (`reference.md:132` "do not push") is unchanged; only the code that merges to
  the integration branch pushes.
- **Upstream-guarded and non-fatal** — push only if the integration branch has
  a configured upstream; if none, skip silently. Never `--force`. A failed
  push (non-fast-forward, offline, rejected) warns and continues; the merge
  already landed locally, so it never fails the task or aborts the run.

## Steps (TDD where a check exists; prose-skill edits otherwise)

1. **drain** (R1) — at the post-merge bookkeeping commit (`SKILL.md:148–149`),
   add: push `main` per completed DONE task, subject to the R4 guard. Leave
   `reference.md:132` worker "do not push" intact.
2. **build** (R2) — replace `SKILL.md:84` ("push … only if the user asked")
   with an unconditional push-after-commit on completion, subject to R4.
3. **parallel** (R3) — after each DONE branch merges and its gates pass
   (`SKILL.md:63–66`), push `main`, subject to R4.
4. **guard wording** (R4) — state the upstream-guard + non-fatal + no-force
   rule once per skill, adjacent to its push step (cite, don't restate across
   files).
5. **autopilot** (R5) — keep the push prohibition; add one line recording that
   push-on-completion is intentionally attended-stages-only.
6. **mirror + bump** (R6) — port each change to
   `antigravity/.agents/workflows/{drain,build,parallel}.md` in the same
   commit; bump `.claude-plugin/plugin.json` `version` (currently 0.7.3).

## Acceptance

- `grep -n 'git push' .claude/skills/drain/SKILL.md .claude/skills/build/SKILL.md .claude/skills/parallel/SKILL.md`
  → a push step in each, each within ±3 lines of the upstream-guard wording.
- `.claude/skills/autopilot/SKILL.md` still contains its push prohibition AND
  the new attended-only-scope note.
- `git show --stat HEAD` includes both `.claude/skills/` and
  `antigravity/.agents/workflows/` paths for each changed skill; and
  `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a version bump.
- Manual E2E: `/build` on a toy task in a repo WITH an upstream pushes on
  completion; in a repo with NO upstream it completes without error.

Acceptance command (static portion):
`grep -n 'git push' .claude/skills/{drain,build,parallel}/SKILL.md && grep -nc 'push' .claude/skills/autopilot/SKILL.md`
