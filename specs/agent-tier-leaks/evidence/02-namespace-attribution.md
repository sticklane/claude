# Verification: 02-namespace-attribution

Verdict: PASS

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a1f20a6a075871b8e
Diff base: 0a5bcf322fce47cf7e7c5474497f13eceb1ab6dc

## Criterion 1 — grep exit 0

Command:
```
grep -riqE 'agentic:' agentprof/README.md agentprof/SCHEMA.md; echo "exit=$?"
```
Output: `exit=0`. Hits at README.md L58 (`agent:agentic:verifier`), L63 (`` `agentic:` prefix ``), L67 (`agentic:build`). SCHEMA.md had no hit but grep still exits 0 because README.md matched (grep with multiple files exits 0 if ANY file matches). PASS.

## Criterion 2 — MANUAL: doc explains the mechanism correctly

Read agentprof/README.md lines 57-71 in full (the added paragraph). It states:

> Agent frames appear in two forms — bare (`agent:verifier`) and
> plugin-namespaced (`agent:agentic:verifier`) — and both are the *same*
> logical agent; the difference records where Claude Code resolved the
> definition from. A bare name means the agent was dispatched from a
> **repo-local `.claude/agents/` definition** ... the `agentic:` prefix means
> the same agent was served by the installed **`agentic` plugin** ... The
> adapter passes `agentType` straight through (`agent:` + agentType) with no
> normalization, so — unlike skill frames, which strip the plugin namespace
> so `agentic:build` and `build` collapse into one — agent frames keep
> theirs, and the two dispatch sources stay distinguishable.

This is coherent and mechanistically correct. I independently read
agentprof/internal/claude/claude.go: line ~177-178 shows
`frame = "agent:" + meta.AgentType` (verbatim passthrough, no stripping),
while `normalizeSkillFrame` (~465-477) explicitly does
`strings.Cut(attributionSkill, ":")` to strip a leading plugin namespace for
skill frames only. This exactly matches the doc's claimed asymmetry between
agent frames (kept verbatim) and skill frames (namespace-stripped). PASS —
correct, clear, and code-grounded explanation, not just a string match.

## Criterion 3 — evidence lines naming transcripts + traced source

Task file evidence names 5 session IDs. Verified each exists on disk and
its cwd project-folder + subagent_type values match the claim:

- `eed20d5f-829c-4a98-94ea-1e780af8aede` — dir
  `~/.claude/projects/-Users-sjaconette-claude/...jsonl` (cwd = `~/claude`).
  `grep -o '"subagent_type":"[^"]*"' ...jsonl | sort -u` → `critic`,
  `implementation-worker`, `scout` (all bare). `~/claude/.claude/agents/`
  contains critic.md, implementation-worker.md, scout.md, verifier.md —
  confirms repo-local definition source. Matches claim.
- `5dcdc5c4-7776-4ac7-a064-8ed03a36fbd8` — dir
  `~/.claude/projects/-Users-sjaconette-fooszone/...jsonl` (cwd =
  `~/fooszone`, which has no `.claude/agents/`). subagent_types found:
  `agentic:critic`, `agentic:scout`, `agentic:verifier`, `general-purpose` —
  all prefixed. Matches claim (plugin-served).
- `61ec4803-...`, `b4bdc20a-...`, `9acb6dc5-...` — all found under
  `~/.claude/projects/-Users-sjaconette-hub/`, consistent with the claimed
  hub cwd.

Shadow-copy check (Step 3 of Steps): `~/.claude/agents/` is present but
empty (`ls -la` shows only `.`/`..`). `~/hub/.claude/agents/` does not exist
at all (task text says "empty (only hub-specific skills...)" — mildly
imprecise phrasing since the dir is actually absent, not empty, but the
substantive conclusion — no stale shadow copies to flag — holds either way).
PASS.

## Append-only compliance

Command: `git diff 0a5bcf3 -- specs/agent-tier-leaks/tasks/02-namespace-attribution.md`

Diff shows only: Status line flip (`in-progress` → `done`), three
checkboxes ticked `[ ]` → `[x]`, and four added evidence-citation bullet
lines under each checkbox. No changes to Goal, Steps, Touch, Budget, or the
acceptance-criterion text itself. PASS.

## Scope / Touch check

Touch: `agentprof/README.md, agentprof/SCHEMA.md`.

`git diff --stat 0a5bcf3 -- agentprof` shows only `agentprof/README.md`
changed (+17/-1 lines, all within the stack-frames paragraph). SCHEMA.md
untouched (task allowed README.md and/or SCHEMA.md — only one was needed).
No other agentprof files touched; `git -C agentprof status --short` shows
only README.md modified (plus the outer task-file edit, which lives outside
the agentprof git tree). No scope creep. agentprof's own `scripts/check.sh`
was not required to be run since only docs were touched (per Touch note).

## Overall

All three acceptance criteria PASS. Append-only and scope-creep checks
PASS. No evidence of overfitting — the doc explanation is general and
grounded in the actual adapter code path, not tailored to specific sample
strings; the cited session IDs and code line numbers were independently
verified against live transcripts and source rather than taken on faith.
