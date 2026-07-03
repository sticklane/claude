# Evidence: task 02 — distill memory layer + cache economics (verify run 2026-07-03)

Verdict: PASS

Branch: task/02-distill-memory-cache-economics
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-af4bbe5f3a73a1cc6
Verified independently; implementer claims not trusted.

## Acceptance criteria

### C1 (R3, distill half) — ✓ PASS

Command:
```
grep -q "docs/memory.md" .claude/skills/distill/SKILL.md && grep -qi "stale" .claude/skills/distill/SKILL.md
```
Output: exit 0 (echoed `OK1`).

Content spot-check against SPEC R3 (diff vs main inspected):
- Routing table row: "Too narrow or too long for CLAUDE.md, but worth keeping →
  Topic file under `docs/memory/`, indexed in `docs/memory.md`" — present.
- Index format: "one line per topic file in the `docs/memory.md` index: path +
  a when-to-read trigger phrase. The index stays ≤200 lines and is loaded on
  demand ... never at session start" — present.
- Stale pruning on write: "Each time /distill writes to the index, prune stale
  entries in the same edit ... (this manual pass is the layer's only decay
  mechanism)" — present.
- "CLAUDE.md remains the home for always-on rules" — present.
- CLAUDE.md always-on pointer line is task 01's half per the task file; correctly
  not touched here.

### C2 (R4) — ✓ PASS

Command:
```
grep -q "static-first" .claude/rules/token-discipline.md && grep -qi "session end" .claude/skills/distill/SKILL.md
```
Output: exit 0 (echoed `OK2`).

Content spot-check against SPEC R4:
- New "## Cache economics" section in `.claude/rules/token-discipline.md`
  (+12 lines) contains: "cached static-first" with stable content at the front
  of prompts / no mid-session churn; "Editing CLAUDE.md or `.claude/rules/`
  mid-session invalidates the cached prefix ... batch such writes at session
  end (as /distill does)"; "Tool-set changes bust caches: don't add/remove MCP
  servers or edit an agent's `tools:` list mid-run. Harness-managed deferred
  tool loading is exempt". All four required elements present.
- Distill SKILL.md batching sentence: "Batch all CLAUDE.md writes into one
  edit at session end — mid-session CLAUDE.md churn invalidates the cached
  prompt prefix (see the Cache economics section of
  `.claude/rules/token-discipline.md`)." — present.

### C3 (R8-part) — ✓ PASS

Command:
```
grep -q "static-first" antigravity/AGENTS.md && grep -q "docs/memory.md" antigravity/.agents/skills/distill/SKILL.md
```
Output: exit 0 (echoed `OK3`).

Content spot-check:
- `antigravity/AGENTS.md` gains a "## Cache economics" section mirroring R4
  with Antigravity-appropriate adaptations (AGENTS.md instead of CLAUDE.md,
  "mid-conversation", "tool configuration" instead of `tools:` lists) —
  static-first, prefix invalidation + end-of-conversation batching, tool-set
  cache-bust warning, deferred-tool-loading exemption all present.
- `antigravity/AGENTS.md` also gains the R6 machine-state bullet under
  "Quality discipline": fields any skill reads programmatically (Status,
  Depends on, Budget, and — after the review fix wave — Touch) are single-line
  `Key: value` headers above the first `##` heading; body sections never for
  orchestrator parsing. Wording matches SPEC R6 (authoritative per the task
  note; correctly not waiting on task 01's CLAUDE.md phrasing).
- `antigravity/.agents/skills/distill/SKILL.md` mirrors the full memory step
  (routing row, `docs/memory.md` index format ≤200 lines with path + trigger
  phrase, on-demand load, stale pruning, AGENTS.md-remains-home) plus the
  conversation-end batching sentence.

### C4 (end-to-end /distill run) — MANUAL / NOT RUN

Explicitly marked manual in the task file until the eval harness covers
/distill; per verification instructions, not attempted.

## Negative constraints and scope

- plugin.json NOT modified (R9 owned by global task 99):
  `git diff main -- .claude-plugin/plugin.json plugin.json` → empty. ✓
- `git diff main --name-only` → exactly:
  `.claude/rules/token-discipline.md`, `.claude/skills/distill/SKILL.md`,
  `antigravity/.agents/skills/distill/SKILL.md`, `antigravity/AGENTS.md`.
  All four are on the Touch list; no files outside it; no untracked files. ✓
- No version bumps, formatting sweeps, or other convention-driven edits
  outside the Touch list. ✓
- Note: CLAUDE.md's mirror-in-same-commit convention is satisfied within this
  change-set (antigravity mirrors are part of the same diff). Repo's
  version-bump convention is deliberately overridden by the task's R9
  carve-out — correctly followed.

## Standard gates

- No build/lint/test gates apply (prose/markdown toolkit repo).
- /evals: only `evals/breakdown/` exists; no stored evalset for distill, so
  the "run /evals before committing a skill change" gate is not applicable
  to this diff. Noted, not a finding.
- SKILL.md size convention: distill SKILL.md is 54 lines (limit: well under
  500). ✓

## Overfitting check

Diff is prose additions matching the SPEC's semantic requirements, not
grep-bait: required phrases ("static-first", "docs/memory.md", "stale",
"session end") appear inside substantive, coherent instructions rather than
as isolated tokens. Task file itself unmodified (Status still in-progress —
drain-managed; not a defect).
