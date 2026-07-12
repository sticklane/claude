# Task 02: Fix the toolkit-owned dispatch sources

Status: in-progress
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/, .claude/agents/, antigravity/, codex/.agents/skills/, .claude-plugin/plugin.json, specs/untyped-agent-fanout/EVIDENCE.md

## Goal

Every toolkit-owned dispatch site EVIDENCE.md names has a landed text
fix — a typed pinned agent named, or an explicit model/effort override —
referenced by commit in EVIDENCE.md; every non-toolkit site (harness
default, one-off human prompt) has a written no-fix disposition there
instead.

## Touch

Skill/agent text and mirrors only, driven by EVIDENCE.md's list. Do NOT
edit `.claude/rules/token-discipline.md` — task 03 owns the doctrine, and
this task's fixes are site-local text changes. If a fix edits any
`.claude/skills/*` or `.claude/agents/*` file, the same commit carries
the `antigravity/` mirror and the plugin version bump (CLAUDE.md mirror
rule); prose-skill mirrors get paraphrased ports with content-coverage
checks, never byte-diffs.

## Steps

1. Read EVIDENCE.md; list the toolkit-owned sites.
2. Per site: apply the tier-appropriate fix per token-discipline's
   "Freehand fan-out" and "Model and effort matching" rungs; mirror; note
   the commit hash back in EVIDENCE.md's row.
3. For non-toolkit sites, write the disposition rows.
4. If any `.claude/agents/*.md` changed, remember agents are enumerated
   in plugin.json (schema requirement).

## Acceptance

- [ ] Every EVIDENCE.md toolkit-owned row carries a commit hash; every other row a disposition (`grep -c 'unresolved\|no-fix\|[0-9a-f]\{7\}' specs/untyped-agent-fanout/EVIDENCE.md` covers all rows — verify by reading, cite the count)
- [ ] If `.claude/skills/*` or `.claude/agents/*` changed: mirrors updated (content-coverage grep per changed artifact, stated in EVIDENCE.md), `git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'` differs from the working-tree value, and `claude plugin validate .` → passes
- [ ] If any of `.claude/skills/{drain,build,autopilot,evals}/SKILL.md` changed: the matching `codex/.agents/skills/<name>/SKILL.md` (real content, not a symlink) updated in the same commit (CLAUDE.md codex leg)
- [ ] `bash evals/lint-ultra-gate.sh` → passes if any of the four ultra-path skills (critique, drain, build, idea) were among the fixed sites
