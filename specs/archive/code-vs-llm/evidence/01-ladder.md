# Verification evidence — task 01-ladder (branch task/01-ladder)

Verified: 2026-07-03, independent verifier (did not write this code).
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-aebf17aa4e68be2a3
HEAD: e9a2285 (drain: task cvl-01 in-progress) + uncommitted working-tree changes.

## Verdict: PASS

## Acceptance commands (all run from repo root, exactly as written)

1. R1 sections — PASS (rc=0)
   `test -f .claude/skills/design/reference.md && grep -q "^## The ladder" .claude/skills/design/reference.md && grep -q "^## Per-part tests" .claude/skills/design/reference.md && grep -q "^## Seam rules" .claude/skills/design/reference.md`

2. R1 rungs + seam rule — PASS (rc=0)
   `for n in 0 1 2 3 4; do grep -qi "rung $n" .claude/skills/design/reference.md || exit 1; done && grep -qi "evaluator-optimizer" .claude/skills/design/reference.md && grep -qi "validated in application code\|validate.*application code" .claude/skills/design/reference.md`

3. R1 size/TOC — PASS (rc=0; file is 65 lines, under the 100-line cap so no TOC required)
   `[ "$(wc -l < .claude/skills/design/reference.md)" -le 100 ] || head -5 .claude/skills/design/reference.md | grep -qi "contents\|TOC"`

4. R2 — PASS (rc=0): `grep -q "code-vs-LLM" .claude/skills/design/SKILL.md`
5. R3 — PASS (rc=0): `grep -q "lowest rung" .claude/skills/design/SKILL.md`
6. R4 — PASS (rc=0): `grep -q "which parts are code" .claude/skills/idea/SKILL.md`
7. R5 — PASS (rc=0): `grep -q "token-discipline" .claude/skills/design/reference.md && grep -qi "script, not a spec" .claude/skills/design/reference.md`
8. R6 (scoped) — PASS (rc=0): `grep -qi "code-vs-LLM ladder" docs/external-playbooks.md && sed -n '/[Cc]ode-vs-LLM ladder/,/^## /p' docs/external-playbooks.md | grep -qi "4×\|4x"`
9. R7 — PASS (rc=0): `grep -q "code-vs-LLM" antigravity/.agents/skills/design/SKILL.md && test -f antigravity/.agents/skills/design/reference.md && grep -q "which parts are code" antigravity/.agents/skills/idea/SKILL.md`

## Non-command criteria (content inspection)

- R1 completeness — PASS. reference.md carries: five rungs each with an
  explicit escalation trigger; rung 2 names all five patterns
  (prompt-chaining, routing, parallelization, orchestrator-workers,
  evaluator-optimizer) each with its own trigger; rung 3 states OpenAI's
  three criteria (complex decision-making beyond rules, brittle/
  unmaintainable ruleset, heavy reliance on unstructured data); rung 4 is
  breadth-first-parallelizable-only with the ~15×/~4× cost note. Per-part
  tests cover all seven, including eval-ability with "escalate only when
  evals show the lower rung actually failing". Seam rules record the
  OpenAI-vs-Gemini structured-output disagreement and side with
  validation in application code; side effects and loop exits in code;
  model emits arguments only.
- R5 scope separation — PASS. Intro cross-references
  `.claude/rules/token-discipline.md` and /idea's "a script, not a spec"
  gate as pointers only; no content from either is restated.
- R6 entry completeness — PASS. docs/external-playbooks.md "Code-vs-LLM
  ladder" entry has: three-vendor agreement bullet (default
  deterministic, incremental escalation, code owns orchestration/loop
  exits/side effects, structured output at seams, smallest capable
  model); named disagreements (Google's multi-agent lean — rejected,
  rung 4 breadth-first-only; OpenAI schema-sufficient vs Gemini
  validate-anyway — sided with validation); ≈4×/≈15× anchors attributed
  to Anthropic's multi-agent research post; four source links; Agents
  Companion marked "secondary-verified — Kaggle mirror, not a Google
  primary".
- R7 mirrors near-identical — PASS.
  `diff .claude/skills/design/reference.md antigravity/.agents/skills/design/reference.md`
  shows only the expected port adaptation (intro cross-reference paths:
  AGENTS.md instead of .claude/rules/token-discipline.md; note that
  external-playbooks.md is not shipped with installs); ladder, per-part
  tests, and seam rules bodies are identical. The R2/R3/R4 diff hunks in
  the antigravity SKILL.md files are line-identical to the .claude ones
  (compared added/removed lines of both diffs: no difference).
- R8 note — PASS. `git diff main --exit-code -- .claude-plugin/plugin.json`
  → unchanged. Pre-implementation version (main and branch identical):
  **0.6.2**. The combined bump is owned by specs/review-fixes global
  task 99 and must land as 0.7.x (minor) relative to 0.6.2.
- Manual post-merge dry-read (/design on email-triage feature) —
  DEFERRED TO POST-MERGE per verification instructions; not exercised.

## Standard gates

- No build/lint for this repo. Per CLAUDE.md, /evals applies only to
  skills with a stored evalset; `evals/` contains only `breakdown` — no
  design or idea evalset exists, so no eval gate applies to this change.

## Scope creep

- None. `git diff main --stat` + untracked files = exactly the seven
  paths in the task's Touch list (5 modified, 2 new). plugin.json
  untouched as required.
