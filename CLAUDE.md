# Agentic development toolkit

This repo IS the toolkit: skills in `.claude/skills/`, subagents in
`.claude/agents/`, always-on rules in `.claude/rules/`. The research it
encodes is in `docs/anthropic-playbook.md` — read it before changing what a
skill teaches, and cite it rather than restating it.

## Authoring conventions

- Skill descriptions: third person, state what it does AND concrete trigger
  phrases (trigger phrases not required for `disable-model-invocation: true`
  skills — Claude never auto-triggers those); command name comes from the
  directory name.
- Side-effectful pipeline steps (`/build`, `/parallel`, `/autopilot`) keep
  `disable-model-invocation: true` — only humans launch them.
- SKILL.md bodies stay well under 500 lines; procedures as numbered steps or
  checklists; heavy reference goes in a separate file, loaded on demand.
- Every skill that produces an artifact must say where the file goes and what
  the next pipeline step is.
- Exact config JSON (hooks, permissions, headless flags) lives in a skill's
  `reference.md`, loaded on demand — never in the SKILL.md body.
- Agents keep hard output budgets (scout ≤300 words) — they exist to protect
  the caller's context; a verbose agent defeats its purpose.
- `.claude/` is the source of truth; `antigravity/` is a mirrored port
  (skills near-identical, agents→skills, human-only skills→workflows,
  hooks in Antigravity's JSON shape). When a skill changes here, mirror the
  change there in the same commit.

## Testing changes

Test a skill by running it in a fresh session against a real repo and
watching where it stalls or over-reads — not by rereading the prose. For
description changes, check both that it triggers on its listed phrases and
does NOT trigger on neighbors' phrases.
