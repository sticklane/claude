# Verification: Task 01 — onboard split + mirror + bump

Verdict: **PASS** (all six acceptance criteria met; close-out bookkeeping incomplete — see findings)

## Acceptance criteria (all run against working tree)

1. ✓ `grep -c 'pointer-only' .claude/skills/onboard/SKILL.md` → `0`
2. ✓ R1 chain (`## Repo map` && `## Commands` && `## State` && `@AGENTS.md`) → `R1-ok`
3. ✓ migration grep (`grep -qi 'migration' ... || grep -qi 'already-onboarded' ...; echo $?`) → `0`
4. ✓ `grep -q '## Repo map' antigravity/.agents/skills/onboard/SKILL.md && grep -qi 'native' ...` → `R3-ok`
5. ✓ `test -s specs/onboard-split-default/evidence/e2e-scratch-onboard.md` → `e2e-ok`.
   Evidence file's captured AGENTS.md shows all three sections (## Repo map,
   ## Commands, ## State) with real commands: `npm install`, `npm test` (exit 0,
   1 pass), `node --version` v26.4.0; build/lint/typecheck recorded as none
   configured (absent, not invented). CLAUDE.md carries `@AGENTS.md` bridge on line 3.
6. ✓ plugin.json version `0.7.9` > pre-task `0.7.8` (base b34ffca) — strictly greater.

## Substance checks

- R2 (main §3): defines AGENTS.md (orientation) + CLAUDE.md (conventions) split;
  `@AGENTS.md` bridge line required in CLAUDE.md's first 10 lines (lines 52-54);
  migration note present (lines 61-65: move orientation out of CLAUDE.md, add
  bridge, delete duplicated prose; template-debris → rewrite). ✓
- R3 (antigravity): uses the three section names; states "AGENTS.md is
  Antigravity's native context file" (lines 8, 46-47, 61-62); NO bridge line
  (`grep -c '@AGENTS.md'` = 0), conventions live in AGENTS.md instead. ✓
- Verify-by-running doctrine (§2 "RUN every command") preserved in both. ✓
- Per-line pruning test ("would removing this ... cause an agent to make a
  mistake?") preserved (main line 36; antigravity line 34). ✓
- Include-list + numbered-step structure intact (§§1-5); deliverable contract
  in first 30 lines (main lines 6-13). ✓

## Scope

`git diff --stat b34ffca`: only the 4 Touch targets changed
(plugin.json, .claude SKILL.md, antigravity SKILL.md, task file) + evidence file
added. No scope creep; repo's own AGENTS.md/CLAUDE.md untouched.

Task-file diff vs b34ffca: shows ONLY the PLAN comment block added. No edits to
Goal/Steps/Touch/Budget/Acceptance text. ✓

## Findings (non-blocking, close-out incomplete)

- Task file Status still `in-progress` (Step 7 requires `done`).
- Acceptance checkboxes still unticked `[ ]` (no evidence lines added).
- PLAN comment block not removed ("delete at close-out" per its own header).
- Changes are UNCOMMITTED in the working tree (Step 7 requires one commit
  recording both plugin.json versions in the message).

All six functional acceptance criteria pass; no test-gaming or overfitting
observed (e2e evidence reflects a genuine headless run with real command output).
