# Verification: Task 04 — worker prompt resolution

Verdict: PASS
Date: 2026-07-03
Verifier: independent (did not write this code)
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a950661a5370dee03
Branch: task/04-worker-prompt-resolution (changes present in working tree, NOT yet committed)

## Acceptance criteria (all commands run from repo root, exactly as written)

### C1 — dead branch gone ✓
```
! grep -rq "plugin's skills\|plugin's build skill" .claude/skills/drain/reference.md .claude/skills/parallel/SKILL.md .claude/skills/autopilot/SKILL.md .claude/skills/autopilot/reference.md
```
Exit 0. Also confirmed repo-wide: `grep -rn "plugin's skills\|invoke /agentic:build" .claude/skills/ antigravity/` returns nothing.

### C2 — concrete-path substitution instruction present ✓
```
grep -q "resolved at dispatch" .claude/skills/drain/reference.md && grep -q "resolved at dispatch" .claude/skills/parallel/SKILL.md && grep -qr "resolved at dispatch" .claude/skills/autopilot/
```
Exit 0. Each dispatcher instructs: resolve to `.claude/skills/build/SKILL.md` in-repo, else the plugin cache path found at dispatch, and substitute for `<build-skill-path>`; each notes workers cannot invoke `disable-model-invocation` skills.

### C3 — Budget stop forwarded ✓
```
grep -q "over budget" .claude/skills/parallel/SKILL.md && grep -qr "over budget" .claude/skills/autopilot/
```
Exit 0. Both carry drain's wording: stop with verdict BLOCKED "over budget" when remaining work clearly exceeds the remaining budget.

### C4 — integer format pinned ✓
```
grep -q "Budget: <N> turns" .claude/skills/breakdown/SKILL.md
```
Exit 0. Template line is now `Budget: <N> turns`; guidance text pins "integer N — no ranges, no prose" and says dispatchers parse it.

### C5 — headless --max-turns cites the pinned format ✓
```
grep -q "<N> turns" .claude/skills/drain/reference.md
```
Exit 0. Headless block: `--max-turns <N from the task's Budget header, else 80>`; prose cites "the task's pinned `Budget: <N> turns` header (integer N, the format /breakdown writes)".

### C6 — antigravity mirrors ✓
```
grep -q "resolved at dispatch" antigravity/.agents/workflows/drain.md && grep -q "over budget" antigravity/.agents/workflows/parallel.md && grep -q "over budget" antigravity/.agents/workflows/autopilot.md && grep -q "Budget: <N> turns" antigravity/.agents/skills/breakdown/SKILL.md
```
Exit 0. Mirrors resolve to `.agents/workflows/build.md` (the correct artifact for that port) and carry the over-budget stop and pinned Budget format.

## Steps sanity check

- Dead "invoke /agentic:build or read from the plugin's skills directory" branch removed from drain reference worker prompt, parallel step 2, autopilot reference prompt template (confirmed in `git diff HEAD`; old text visible only on `-` lines).
- Drain reference "both worker prompts": the main verbatim worker prompt (line ~56) got `<build-skill-path>` resolution; the headless prompt is self-contained by design (its section explicitly says "no skill references") and instead got the pinned `--max-turns` citation — consistent with the task's step 4. The relaunch/tournament prompts append to the base prompt, so they inherit the resolution.
- `autopilot/SKILL.md` is in the Touch list but unmodified — verified it contains no prompt template and no dead-branch text (the template lives in `reference.md`, which was updated), so no edit was needed and C1 passes on it.
- Autopilot and parallel worker prompts carry the over-budget BLOCKED stop; drain already had it (present in both drain prompts).
- Breakdown SKILL.md (both trees) pins `Budget: <N> turns` in the template block and the guidance paragraph.

## Gates

- `bash tests/test_hook_templates.sh` → pass: 77, fail: 0
- `bash tests/test_install_gates.sh` → pass: 156, fail: 0
- `bash tests/test_sync_skills.sh` → passed: 24, failed: 0
- `bash evals/run.sh breakdown` (repo convention: run /evals before committing skill changes with a stored evalset; breakdown changed) → `PASS breakdown/01-small-spec`, 1/1 scenarios passed.

## Scope creep / overfitting

- Diff (`git diff HEAD --stat`) touches exactly the 8 Touch-list files plus the task file itself (Status: pending → in-progress). No scope creep.
- No test/eval files modified; the acceptance greps are satisfied by substantive prose rewrites, not keyword stuffing — the old dead-branch text was actually deleted and replaced with dispatch-time resolution instructions.

## Findings (non-blocking)

1. All changes are uncommitted (working tree only) and the task file still reads `Status: in-progress`. Repo convention requires committing on task completion, with .claude/ and antigravity/ mirrored in the same commit.
2. Repo CLAUDE.md convention: bump `version` in `.claude-plugin/plugin.json` when skill behavior changes. Not in this task's Touch list, so the implementer correctly did not edit it — noting the convention here for the orchestrator to handle at commit time.
