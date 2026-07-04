# Task 01: /onboard writes the orientation split by default (skill + mirror + bump)

Status: in-progress
Depends on: ../../workflow-token-efficiency/tasks/05-bump-and-e2e.md
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R5; R4 landed with the spec)
Touch: .claude/skills/onboard/SKILL.md, antigravity/.agents/skills/onboard/SKILL.md, .claude-plugin/plugin.json, specs/onboard-split-default/evidence/

## Goal

/onboard's default deliverable is the orientation split: root AGENTS.md
(purpose paragraph, `## Repo map`, `## Commands` verified by running,
`## State`) plus CLAUDE.md (conventions with the `@AGENTS.md` bridge line in
its first 10 lines), both ≤200 lines. The "pointer-only" AGENTS.md offer is
gone, a migration note covers already-onboarded repos, the Antigravity port
mirrors the change (same commit, per CLAUDE.md's mirror convention), and
plugin.json carries a minor bump.

## Touch

The dependency on wte 05 exists only because plugin.json is the queue's
bump-chain contention point — do not edit any drain/ultra/workflow skill
files, and do not touch this repo's own AGENTS.md or CLAUDE.md (conformant
via repo-orientation; out of scope per spec).

## Steps

1. Read `../SPEC.md` in full, then `.claude/skills/onboard/SKILL.md`.
2. Rewrite the deliverable definition: default output = AGENTS.md
   (`## Repo map` / `## Commands` / `## State`, section names matching this
   repo's own AGENTS.md) + CLAUDE.md with the `@AGENTS.md` bridge line;
   delete the step-5 "pointer-only" offer bullet; keep the verify-by-running
   doctrine and pruning test untouched; stay within the existing structure
   (Include list + step numbering), first-30-lines contract preserved.
3. Add the migration note (R2): already-onboarded repo → move orientation
   content from CLAUDE.md to AGENTS.md, add bridge line, delete duplicated
   prose; template-debris AGENTS.md (lacks `## Repo map`) → rewrite.
4. Mirror into `antigravity/.agents/skills/onboard/SKILL.md`, replacing the
   bridge-line requirement with one sentence noting AGENTS.md is
   Antigravity's native context file.
5. Bump the minor version in `.claude-plugin/plugin.json` from the value
   found (wte 05 has landed by dependency order — bump from its result).
6. E2E: scaffold a throwaway repo (e.g. `$(mktemp -d)` with a package.json +
   one test), run /onboard against it in a fresh headless session, and save
   the produced AGENTS.md + CLAUDE.md and the session's closing summary to
   `specs/onboard-split-default/evidence/e2e-scratch-onboard.md`.
7. Run the acceptance commands below; commit skill + mirror + bump +
   evidence as one commit; set this file's Status to done.

## Acceptance

- [ ] `grep -c 'pointer-only' .claude/skills/onboard/SKILL.md` → outputs `0`
- [ ] `grep -q '## Repo map' .claude/skills/onboard/SKILL.md && grep -q '## Commands' .claude/skills/onboard/SKILL.md && grep -q '## State' .claude/skills/onboard/SKILL.md && grep -q '@AGENTS.md' .claude/skills/onboard/SKILL.md && echo R1-ok` → `R1-ok`
- [ ] `grep -qi 'migration' .claude/skills/onboard/SKILL.md || grep -qi 'already-onboarded' .claude/skills/onboard/SKILL.md; echo $?` → `0`
- [ ] `grep -q '## Repo map' antigravity/.agents/skills/onboard/SKILL.md && grep -qi 'native' antigravity/.agents/skills/onboard/SKILL.md && echo R3-ok` → `R3-ok`
- [ ] `test -s specs/onboard-split-default/evidence/e2e-scratch-onboard.md && echo e2e-ok` → `e2e-ok`, and the captured AGENTS.md shows all three sections with commands that were actually run
- [ ] plugin.json minor version strictly greater than the pre-task value (record both in the commit message)
