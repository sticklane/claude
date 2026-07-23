Task: cross-repo beads adoption + skill retirement + skill health-check (all substantially complete)
Status: done, with 5 real follow-up items open in bd
Next step: triage the 5 open bd items below by priority (agentic-vtp is P0/critical)
Resume with: bd ready (or bd show <id> on each item below)
Blocking on: nothing technical — these are judgment/priority calls

## What this session did (all pushed to origin/main, all verified)

1. **Resumed and completed the 2026-07-22 architecture pivot** (`specs/agentic-core-redesign`): all 15 tasks done/obsolete, epic `agentic-4t2` closed at 11/11 children. bd is now `~/claude`'s own source of truth.
2. **Full bd cutover across every other repo on this machine** — automation, fooszone, interview-prep, portfolio-tracker, ynab-mcp-server, hub, budget_analysis, `~/specs`, and the life-vault. Each got: `agentic init`, a verified non-lossy import of existing task/checkbox state into bd, CLAUDE.md/AGENTS.md rewritten to make bd the sole tracker with the discovered-work convention, and a push. Real merge conflicts in portfolio-tracker/ynab-mcp-server (genuine unrelated upstream commits) were resolved without data loss.
3. **Retired `/list-specs` and `/prioritize`** (never re-pointed onto bd per core task 09's own stated goal) — deleted, all references swept, critic-reviewed, 3 critic-found nits fixed, plugin bumped to 0.13.0.
4. **Redesigned `hooks/session-refresh/refresh-check.sh`** to read `transcript_path` directly off its own hook payload instead of shelling out to `agentprof` — same budget defaults, same underlying "ctx" formula (mirrored from `agentprof/internal/costsummary/costsummary.go`, not reinvented), re-prime detection now fully self-contained too. `agentprof` stays the tool for general cost-attribution digging, decoupled from this guardrail.
5. **Fixed a real eval-wiring bug**: `evals/work/01-queue-discipline` was failing not because `/work` misbehaves (forensic evidence from real transcripts confirms it claims before implementing, correctly) but because its stub runner wasn't being auto-applied on the plain invocation. Fixed with a `runner-cmd.txt` convention in `evals/run.sh`; now passes deterministically.
6. **Removed dead code**: `.claude/skills/_shared/touch_disjoint.py` + its test (orphaned since `admission.py`'s deletion).
7. Added trigger phrases to `breakdown`/`distill` skill descriptions (health-check finding).
8. Clarified `.claude/rules/token-discipline.md`'s wake-budget doctrine: it gates main-session context only, not subagent/workflow token totals — a genuinely different concept from the Workflow tool's own `budget.total`.

`bash scripts/check.sh` is green (40 pytest + all shell tests; only the 2 pre-existing documented quarantine entries are non-green, as expected).

## Open follow-up items in bd (not yet fixed — this is the actual remaining work)

- **`agentic-vtp` (P0, CRITICAL)** — `agentic/initialize.py`'s `_controlled_bd_init()` blindly runs `git reset HEAD~1` to undo bd init's auto-commit, assuming that commit is always exactly HEAD. In the `~/automation` cutover this was false: it silently un-committed an unrelated, already-pushed commit (recovered via reflog this time, not lost — but the mechanism is a live landmine for any repo where something else commits in the same window). Needs a real fix: verify the commit being reset is actually bd's own before resetting, abort loudly otherwise.
- **`agentic-49u`** — `docs/TASKS.md` (a dated tech-debt journal, not checkbox-based) was never swept for pivot-mooted entries or converted to bd; at least 2 entries are already stale (a drain/SKILL.md line-count entry, a since-deleted dual-implementation entry).
- **`agentic-d3x`** — `breakdown/SKILL.md` still has a stale mirror-check reference (antigravity trees, deleted by task 10) and a stale drain-baton generation-budget mention (deleted by task 09). Distinct from the list-specs/prioritize retirement nits already fixed this session.
- **`agentic-bsd`** — `workboard/SKILL.md` line ~58 still mentions drain "batons" (deleted by task 09). Not confirmed whether the retirement track's `workboard.py` edits also touched this SKILL.md prose line — check before assuming it's fixed.
- **`agentic-ml6`** — `drain/SKILL.md` carries a short "Launch authorization (execution stage)" paragraph that may read as contradicting `CLAUDE.md`'s claim that "the contract blocks are gone from the SKILL.md files" (core task 11). It's a brief citation, not a restated contract — worth a maintainer read to decide whether to trim it or soften CLAUDE.md's claim.

## Gotchas learned this session

- **`bd init` run bare auto-commits and duplicates content into CLAUDE.md/AGENTS.md.** Always use the curated `agentic init` wrapper (built this session's earlier resume work) instead, or `bd init --non-interactive --remote "" --skip-agents` as a manual fallback. See `agentic-vtp` above for the one real gap even the curated wrapper has.
- **`python3 -m agentic.shadow`, run with `PYTHONPATH=/Users/sjaconette/claude` and `cd`'d into a target repo, is fully portable** — it scans that repo's own `specs/*/tasks/*.md` and imports into that repo's own bd store. Used successfully across 5+ other repos this session.
- **Concurrent background agents editing the same shared checkout will detect and self-stop per `.claude/rules/concurrent-sessions.md`** — this happened once this session (harmlessly — the orchestrating session was the undetected "other editor"). If you see an agent report a collision and refuse to push, check whether it's actually you before assuming a stray process.
- Full per-repo cutover details (exact issue counts, commit hashes) are in this session's transcript / the two workflow journals if ever needed: `.claude/workflows/cross-repo-beads-adoption.js` and `.claude/workflows/full-cutover-and-health-check.js` (both committed as repo workflows for reuse).

## Verification

Every claim above has a corresponding verified commit on `origin/main` (independently re-verified per task/repo by a fresh verifier agent, not self-reported) except the 5 open bd items, which are genuinely not yet done.

Next stage: none — /clear and resume with "Read .claude/HANDOFF.md and continue," which will surface the 5 open items above for triage.
