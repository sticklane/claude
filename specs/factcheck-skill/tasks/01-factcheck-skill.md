# Task 01: author the /factcheck skill (+ reference, antigravity mirror, version bump)

Status: pending
Depends on: none
Priority: P2
Budget: 35 turns
Spec: ../SPEC.md (requirements R1–R8)
Touch: .claude/skills/factcheck/SKILL.md, .claude/skills/factcheck/reference.md, antigravity/.agents/skills/factcheck/SKILL.md, antigravity/.agents/skills/factcheck/reference.md, .claude-plugin/plugin.json

## Goal

A git-tracked, model-invocable `/factcheck` skill exists that packages the
targeted "one general-purpose web worker per source cluster, each claim backed
by a verbatim quote + URL or marked UNVERIFIED" pattern, with its routing
`description` steering known-source/verification questions here and leaving
open-ended synthesis to `deep-research`. The worker-prompt template and the
primary-vs-secondary rubric live in a loaded-on-demand `reference.md`; a
near-identical antigravity mirror and a `.claude-plugin/plugin.json` version
bump land in the same commit.

## Touch

This is deliberately ONE task, not several: CLAUDE.md requires the
`antigravity/` mirror to change in the SAME commit as the `.claude/` skill,
and R7 requires the mirror + version bump to land together — so the skill,
its reference, the mirror, and the version bump are one reviewable unit. Do
NOT edit `deep-research` (harness built-in, out of scope), add any
`.claude/agents/*` definition, or touch the `plugin.json` skills manifest
(directory glob auto-discovers; `bin/sync-skills` is retired).

## Steps

1. Read `.claude/rules/token-discipline.md` "Match the research tool to the
   question" (the routing split this skill packages) and an existing
   model-invocable skill (e.g. `.claude/skills/onboard/SKILL.md`) for the
   frontmatter + `Next stage:` conventions. Read one existing antigravity
   mirror to match its port style.
2. Write `.claude/skills/factcheck/reference.md` FIRST (R8): the exact
   general-purpose worker-prompt template (stating tier + output cap +
   structured per-item return of verdict/URL/verbatim-quote/confidence) and
   the full primary-vs-secondary source rubric. TOC if >100 lines.
3. Write `.claude/skills/factcheck/SKILL.md` (R1–R6): frontmatter
   (`name: factcheck`, routing `description` with both trigger framings + the
   "not for open-ended synthesis → deep-research" clause, `argument-hint`, NO
   `disable-model-invocation`); first ≤30 lines encode the execution contract
   (primary-sources-only rubric; every claim = verbatim quote ≤30 words + URL
   or UNVERIFIED; never guess/substitute); dispatch step names
   `general-purpose`, an explicit tier, and an output cap; UNVERIFIED items
   surfaced as a distinct section; ends with a `Next stage:` line. Body <500
   lines; the worker template stays in reference.md, not inlined.
4. Port the near-identical mirror to
   `antigravity/.agents/skills/factcheck/` (SKILL.md + reference.md),
   adapting agent→skill and runtime/tier wording (not byte-identical).
5. Bump `.claude-plugin/plugin.json` minor version by exactly one (skill
   behavior added); combine with any other bump landing in the same commit-set.
6. Commit all of the above together.

## Acceptance

All commands run from the repo root. These mirror SPEC.md's acceptance list:

- [ ] `test -f .claude/skills/factcheck/SKILL.md && ! grep -q disable-model-invocation .claude/skills/factcheck/SKILL.md` (R1)
- [ ] `grep -q '^name: factcheck' .claude/skills/factcheck/SKILL.md && grep -q '^description:' .claude/skills/factcheck/SKILL.md` (R1)
- [ ] `awk 'END{exit NR>=500}' .claude/skills/factcheck/SKILL.md` (body <500 lines) (R1)
- [ ] `description` line carries a claim-verification trigger, a known-source-lookup trigger, AND a "not for open-ended synthesis / deep-research" clause (read the line; grep `fact-check` / `official docs` / `deep-research`) (R2)
- [ ] `head -30 .claude/skills/factcheck/SKILL.md | grep -qi UNVERIFIED && head -30 .claude/skills/factcheck/SKILL.md | grep -qi primary` (R3)
- [ ] `grep -q general-purpose .claude/skills/factcheck/SKILL.md`, and a tier token (`haiku`/`effort`/`session model`/`opts.model`) + an output cap (`words`/`tokens`/`≤`) appear near the dispatch step (R4)
- [ ] `grep -qi UNVERIFIED .claude/skills/factcheck/SKILL.md` and the body instructs surfacing UNVERIFIED items as a distinct section (R5)
- [ ] `grep -q 'Next stage:' .claude/skills/factcheck/SKILL.md` (R6)
- [ ] `test -f .claude/skills/factcheck/reference.md` and it contains the worker-prompt template; the SKILL.md body does NOT inline that template (R8)
- [ ] `test -f antigravity/.agents/skills/factcheck/SKILL.md` and its frontmatter `name:` matches; NOT byte-identical to the Claude SKILL.md (R7)
- [ ] `test "$(node -p "require('./.claude-plugin/plugin.json').version")" != "$(git show origin/main:.claude-plugin/plugin.json | node -pe "JSON.parse(require('fs').readFileSync(0)).version")"` (version bumped) (R7)
- [ ] E2E in a FRESH session: `/factcheck` on a known-source question (one obviously-checkable part + one with no published answer) → dispatches ≥1 general-purpose web worker, returns findings each carrying a verbatim quote + URL, and surfaces the unbackable part in a distinct UNVERIFIED list; then an open-ended "survey the landscape of X" prompt does NOT trigger `/factcheck` (R2 routing + R5 distinctness)
