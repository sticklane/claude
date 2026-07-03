# Task 02: Distill memory layer + cache economics, with antigravity mirrors

Status: pending
Depends on: none
Budget: 30 turns
Spec: ../SPEC.md (requirements R3, R4, R8-part; R9 note)

## Goal

/distill gains an agent-maintained memory layer: lessons too narrow or
too long for CLAUDE.md go to a topic file under `docs/memory/`, indexed
in `docs/memory.md` (≤200 lines, one line per topic file: path +
when-to-read trigger phrase); the index is loaded on demand, never at
session start; /distill prunes stale entries when it writes (semantic
decay, manual-trigger version); the skill states the artifact locations
and that CLAUDE.md remains the home for always-on rules. /distill also
gains one sentence batching CLAUDE.md writes at session end (cache
preservation). `.claude/rules/token-discipline.md` gains a short "Cache
economics" section containing the phrase "static-first": stable content
belongs at the front of prompts and must not churn mid-session;
CLAUDE.md/rules edits invalidate the cached prefix; tool-set changes
bust caches — don't add/remove MCP servers or edit agent `tools:` lists
mid-run (harness-managed deferred tool loading is exempt). Mirrors per
R8: `antigravity/AGENTS.md` gets the cache-economics section AND the R6
machine-state-in-headers convention (wording per SPEC R6, consistent
with task 01's CLAUDE.md bullet); the antigravity distill skill gets the
memory step. Do NOT bump plugin.json — the combined bump (R9) is owned
by global task 99 in specs/review-fixes.

## Touch

- `.claude/skills/distill/SKILL.md`
- `.claude/rules/token-discipline.md` — Cross-spec: also edited by
  model-agnostic, chaining-antipatterns — see specs/QUEUE.md
- `antigravity/AGENTS.md` (cache economics + R6 convention mirror)
- `antigravity/.agents/skills/distill/SKILL.md` (memory-step mirror)

## Steps

1. Add the memory-layer step to `.claude/skills/distill/SKILL.md`:
   routing rule (CLAUDE.md vs `docs/memory/` topic file), index format
   for `docs/memory.md` (≤200 lines, path + trigger phrase per line,
   loaded on demand), stale-entry pruning on write, artifact locations,
   and the session-end batching sentence for CLAUDE.md writes (R3, R4).
2. Add the "Cache economics" section to
   `.claude/rules/token-discipline.md` per R4 (must contain
   "static-first"; deferred tool loading exemption).
3. Mirror the cache-economics section and the R6 header convention into
   `antigravity/AGENTS.md` (its token-discipline content lives there).
4. Mirror the memory step into
   `antigravity/.agents/skills/distill/SKILL.md`.

## Acceptance

- [ ] `grep -q "docs/memory.md" .claude/skills/distill/SKILL.md && grep -qi "stale" .claude/skills/distill/SKILL.md` (R3, distill half — CLAUDE.md half lives in task 01)
- [ ] `grep -q "static-first" .claude/rules/token-discipline.md && grep -qi "session end" .claude/skills/distill/SKILL.md` (R4)
- [ ] `grep -q "static-first" antigravity/AGENTS.md && grep -q "docs/memory.md" antigravity/.agents/skills/distill/SKILL.md` (R8-part)
- [ ] End to end (manual, until the eval harness covers /distill): in a
      fresh session, run /distill after a session that produced one
      narrow lesson; verify it lands as a `docs/memory/` topic file plus
      one index line in `docs/memory.md` (not a CLAUDE.md edit), and
      `wc -l docs/memory.md` ≤ 200.
