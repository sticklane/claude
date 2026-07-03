# Verification evidence: Task 02 — Core prose to tier language

Verdict: **PASS**
Verified: 2026-07-03, worktree `/Users/sjaconette/claude/.claude/worktrees/agent-ab8c41600753b1ac2`, branch `task/02-core-tier-language`, diffed against `main`.
Verifier: independent (did not author the change).

## Acceptance commands (all run from the worktree root; exit codes recorded)

1. R2 — scout.md tier line, frontmatter, fallback clause
   Command: `grep -q "scout-tier" .claude/agents/scout.md && grep -q "model: haiku" .claude/agents/scout.md && grep -qi "absent in plugin installs" .claude/agents/scout.md`
   Exit code: 0 ✓

2. R3 — scout-tier in token-discipline and README
   Command: `grep -q "scout-tier" .claude/rules/token-discipline.md && grep -q "scout-tier" README.md`
   Exit code: 0 ✓

3. R11 — routing ladder in the always-on rule
   Command: `grep -q "tier pin" .claude/rules/token-discipline.md && grep -q "frontier-tier" .claude/rules/token-discipline.md && grep -q "deep-tier" .claude/rules/token-discipline.md`
   Exit code: 0 ✓
   Note: token-discipline.md now contains the four-rung ladder (scout-tier / session-tier / deep-tier Opus 4.8 / frontier-tier Fable), the "tier pin" dispatch rule naming drain's tournament workers + per-candidate verifier runs, /design's candidate investigators, on-demand verifier escalation, the inherit-session fallback, and "Pins bind Agent-tool dispatch only". No restatement of drain ranking mechanics.

4. R3 — evaluator lines reworded, no tier mislabel
   Command: `grep -qi "built-in transcript evaluator" .claude/skills/autopilot/reference.md && grep -qi "built-in transcript evaluator" .claude/skills/gate/reference.md && ! grep -qi "scout-tier" .claude/skills/autopilot/reference.md && ! grep -qi "scout-tier" .claude/skills/gate/reference.md`
   Exit code: 0 ✓ (both files say "the runtime's built-in transcript evaluator (Claude Code: Haiku)")

5. R4 — active runtime profile framing, claude -p present
   Command: `grep -q "active runtime profile" .claude/skills/drain/reference.md && grep -q "active runtime profile" .claude/skills/autopilot/reference.md && grep -q "claude -p" .claude/skills/drain/reference.md`
   Exit code: 0 ✓

6. R5 — fallback clauses in plugin-shipped citers
   Command: `grep -q "absent in plugin installs" .claude/skills/drain/reference.md && grep -q "absent in plugin installs" .claude/skills/autopilot/reference.md`
   Exit code: 0 ✓

7. R9 — README runtimes subsection, CLAUDE.md pointer
   Command: `grep -qi "Other runtimes" README.md && grep -q "runtimes/" CLAUDE.md`
   Exit code: 0 ✓ (README gains "### Other runtimes and models" under Install; CLAUDE.md gains one conventions bullet citing `runtimes/` profiles)

## Constraint checks

(a) `claude -p` code blocks byte-identical to main
    Method: `git diff main -- <file>` inspected hunk-by-hunk (all hunks touch prose only), PLUS extracted all fenced code blocks (`awk '/^```/{inb=!inb; print; next} inb'`) from `git show main:<file>` and the working copy and diffed them.
    Result: `.claude/skills/drain/reference.md`: fences IDENTICAL; `.claude/skills/autopilot/reference.md`: fences IDENTICAL ✓

(b) `.claude-plugin/plugin.json` unchanged vs main
    Command: `git diff main -- .claude-plugin/plugin.json` → empty diff ✓ (version bump correctly deferred to review-fixes task 99)

(c) critic.md / verifier.md unchanged vs main
    Command: `git diff main --stat -- .claude/agents/critic.md .claude/agents/verifier.md` → empty diff ✓

(d) "scout-tier" absent from autopilot and gate references
    Covered by acceptance check 4 (case-insensitive negative greps), exit 0 ✓

(e) Touch-list scope
    Command: `git diff main --name-only` →
    .claude/agents/scout.md, .claude/rules/token-discipline.md, .claude/skills/autopilot/reference.md, .claude/skills/drain/reference.md, .claude/skills/gate/reference.md, CLAUDE.md, README.md
    Exactly the 7 Touch-list files; no scope creep ✓

## Gates

- No build/lint/test harness exists (prose-only repo; no package.json/Makefile/pyproject.toml).
- `bash evals/runner-selftest.sh` → "runner selftest: OK (PASS and FAIL plumbing verified ...)", exit 0 ✓
- Full `/evals` not run: the only stored evalset is `evals/breakdown/`, for a skill this task does not touch; running it spawns paid headless claude sessions and is human-gated per CLAUDE.md.

## Overfitting review

Acceptance criteria are grep-based; inspected the full diffs to confirm each required phrase appears inside substantive prose implementing the corresponding step (tier ladder, framing sentences, fallback clauses, README subsection, CLAUDE.md bullet), not as keyword stuffing. No test files exist for this change to have been modified.

## Findings (non-blocking)

- Changes are uncommitted (working tree only, branch `task/02-core-tier-language`). Repo conventions require committing on task completion; not an acceptance criterion here, so noted only.
- Task file status is "in-progress" and unchanged vs main, consistent with the caller's "Touch list minus the specs task file itself" instruction.
