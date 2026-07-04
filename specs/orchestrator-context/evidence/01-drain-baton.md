# Verification: Task 01 — Drain baton-pass step + relaunch flag set

Verdict: **PASS**

Repo: /Users/sjaconette/claude/.claude/worktrees/agent-a571c48f410951a76
Base commit for diff: 7f7dfa094a92a52557f4d58d58017e9a00e5f8bb

## Acceptance criteria

### A1 — PASS
Command: `grep -n "baton" .claude/skills/drain/SKILL.md`
The "## 3a. Baton pass (self-relaunch)" block is lines 155–174 (20 lines
including heading; 18 content lines) — `awk 'NR>=155 && NR<=174' | wc -l` = 20,
i.e. ≤ 20. The step names:
- default: "hand off every 4 recorded verdicts this session (default…)" ✓
- degradation override signs: "re-reading files already read, losing queue
  position, repeated failed corrections, or a compaction event" ✓
- cap (10): "max-generations cap of 10" ✓
- read-state-then-verify ritual: "Fresh-instance ritual (R1a)… (1) read the
  baton, (2) read task files' Status: lines, (3) git log --oneline -15,
  (4) run ONE cheap verification … only then dispatch" ✓

### A2 — PASS
Command: `grep -n "Relaunch-every" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
Hit at SKILL.md:159. Override location described as the drained spec's SPEC.md
header block: "`Relaunch-every: N` header in the drained spec's SPEC.md header
block overrides N". (No reference.md hit, but criterion requires only hit(s).)

### A3 — PASS
Command: `grep -n "generation" .claude/skills/drain/reference.md`
Relaunch command template present (reference.md:292–306) WITH orchestrator flag
set: `--allowedTools "Task,Read,Edit,…"`, `Task` explicitly allowed, git+gate
allowlist, `--max-turns`. Recorded background-dispatch verification verdict
present (reference.md:315–327): "Background-dispatch verification (2026-07-03,
recorded verbatim)… **Verdict: SUPPORTED.**"

### A4 — PASS
Command: `grep -qi "attended" .claude/skills/drain/SKILL.md` → exit 0
"Gen 1 is always attended; passing `attended` in the /drain invocation makes
every trigger OFFER the baton + relaunch command instead of self-relaunching."

### A5 — PASS
Command: `grep -q "DRAIN_RELAUNCH_CMD" .claude/skills/drain/reference.md` → exit 0
reference.md:308 documents the `DRAIN_RELAUNCH_CMD` env override.

### A6 — PASS
Command: `grep -qi "baton" antigravity/.agents/workflows/drain.md` → exit 0
Line 135: "**Baton pass (write the baton and stop).**" with "an Antigravity run
cannot self-relaunch" (line 144) and the read-state-then-verify ritual mirrored.

## Task-file diff (append-only check) — PASS
Command: `git diff 7f7dfa094a92a52557f4d58d58017e9a00e5f8bb -- '*/tasks/*.md'`
Only 01-drain-baton.md changed. Only two edits: Status pending→in-progress, and
an added `<!-- PLAN … -->` comment block. No edits to Goal/Steps/Touch/Budget/
Acceptance text. Compliant.

## Scope / Touch check — PASS
Command: `git diff <base> --stat`
Changed files:
- .claude/skills/drain/SKILL.md (Touch ✓)
- .claude/skills/drain/reference.md (Touch ✓)
- antigravity/.agents/workflows/drain.md (Touch ✓)
- specs/orchestrator-context/tasks/01-drain-baton.md (allowed task-file edit)
No untracked files. `git diff <base> -- '*plugin.json'` is empty — `.claude-plugin/plugin.json`
NOT touched (task 05 owns that bump). No scope creep.

## Gates
No `scripts/check.sh` in repo. Changes are markdown-only (skill/workflow prose).
No build/lint/test gate applicable.

## Overfitting check
Criteria are prose-presence checks against skill docs; implementation adds
genuine procedural content, not test-gaming. No red flags.
