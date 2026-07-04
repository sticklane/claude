# Verification: Task 07 — Evals distribution caveat + conditional evidence commits

Verdict: PASS (with one scope-creep finding, see below)
Verified: 2026-07-03, worktree /Users/sjaconette/claude/.claude/worktrees/agent-a33806fb6c1192b1a, branch task/07-evals-distribution-and-evidence
Note: all changes are UNCOMMITTED working-tree edits (`git diff main...HEAD` is empty; 8 modified files in `git status`).

## Acceptance criteria

### AC1 — evals SKILL.md caveat ✓
Command:
```
grep -q "toolkit repo" .claude/skills/evals/SKILL.md && grep -qi "not usable from plugin installs\|not with installs" .claude/skills/evals/SKILL.md
```
Exit 0. Intent check: caveat is in the first body paragraph (lines 8–11), i.e. near the top:
```
$ARGUMENTS. The runner (`evals/run.sh`) and the fixture scenarios it
consumes ship in the toolkit repo, not with installs — /evals is not
usable from plugin installs.
```
Wording matches drain SKILL.md line 17 ("the toolkit repo, not with installs").

### AC2 — evals reference.md caveat ✓
Command:
```
grep -qi "not usable from plugin installs\|not with installs" .claude/skills/evals/reference.md
```
Exit 0. Added: "Runner and scenarios ship in the toolkit repo, not with installs — not usable from plugin installs."

### AC3 — build close-out conditional evidence commit ✓
Command:
```
grep -q "inline in the task file" .claude/skills/build/SKILL.md
```
Exit 0. Intent check: close-out now reads "Commit code + task file ... — plus the verifier's `evidence/` file when an evidence path was passed; otherwise note that evidence was not persisted and keep the one-line evidence inline in the task file as the artifact." Matches the required "when an evidence path was passed / otherwise ... inline in the task file" structure. Evidence-citing bullet also made conditional ("citing the `evidence/` file when an evidence path was passed in step 3").

### AC4 — drain DONE bullet + tournament filter scoped ✓
Command:
```
grep -q "specs/<slug>/ layout" .claude/skills/drain/SKILL.md && grep -q "specs/<slug>/ layout" .claude/skills/drain/reference.md
```
Exit 0. Intent check: SKILL.md DONE bullet — "for queues using the `specs/<slug>/ layout` it also carries the verifier's `evidence/` file — for other layouts the task file's inline evidence is the artifact". reference.md tournament filter carries the same scoping ("for queues using the `specs/<slug>/ layout` the winner's branch already carries the worker's committed evidence file; for other layouts the task file's inline evidence is the artifact"). Both applied on top of the task-02 rewrites as required.

### AC5 — antigravity mirrors ✓
Command:
```
grep -q "inline in the task file" antigravity/.agents/workflows/build.md && grep -q "specs/<slug>/ layout" antigravity/.agents/workflows/drain.md
```
Exit 0. Intent check: build.md step mirrors the conditional commit + inline fallback verbatim in structure; drain.md mirrors BOTH the DONE-collect scoping and the tournament-filter scoping (two hunks, matching the .claude sources).

## Gates
- No build/lint/test commands exist in this repo. The repo's stated gate for skill changes is /evals (`evals/run.sh`), which spawns paid headless agent sessions — not run by this verifier; flagged for the human gate per docs/human-gates.md.

## Scope creep
- `.claude-plugin/plugin.json`: version bumped 0.6.1 → 0.6.2. NOT in the task's Touch list. The repo convention (CLAUDE.md: "Bump `version` in `plugin.json` whenever skill behavior changes") motivates it, but the Touch list is binding — reporting the convention rather than accepting the edit. Recommend either dropping this hunk from the task-07 change or having the queue owner sanction it explicitly.
- No other out-of-scope files changed; remaining 7 modified files are exactly the Touch list.

## Overfitting check
- No test files exist for these criteria (grep-based acceptance). The prose changes satisfy the intent (conditional contract, layout scoping, distribution caveat), not just the literal grep tokens — e.g. the exact phrases appear inside full sentences that state the conditional behavior, and the mirrors restate the behavior rather than embedding bare tokens. No gaming detected.
