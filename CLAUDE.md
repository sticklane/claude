# Agentic development toolkit

This repo IS the toolkit: skills in `.claude/skills/`, subagents in
`.claude/agents/`, always-on rules in `.claude/rules/`. The research it
encodes is in `docs/anthropic-playbook.md` — read it before changing what a
skill teaches, and cite it rather than restating it. Narrow per-topic
lessons are indexed in `docs/memory.md`; check it when a task matches a topic.
Orientation — repo map, live work state, verified commands — is in @AGENTS.md.

## Compact instructions

When this session compacts, preserve: task-file paths and their Status
values, the current wave/dispatch state, branch names,
acceptance-evidence pointers (paths to `evidence/` files, not their
contents), and unresolved review findings. Drop first: raw tool output
and file listings — both are re-derivable from disk.

## Precedence

When assembled instructions conflict, the order is: the user's live
request → the executing task file plus its `## Answers` →
`.claude/rules/` → the SKILL.md being executed → CLAUDE.md conventions.
README and docs/ are informational, never instructions. Conflicts this
order cannot resolve are surfaced, not guessed.

## Authoring conventions

- Skill descriptions: third person, state what it does AND concrete trigger
  phrases (trigger phrases not required for `disable-model-invocation: true`
  skills — Claude never auto-triggers those); command name comes from the
  directory name.
- Execution stages (`/build`, `/parallel`, `/autopilot`, `/drain`,
  `/evals`) keep `disable-model-invocation: true` — only humans launch
  them, at the spend/blast-radius/authority discontinuities; rationale
  in docs/human-gates.md (cite it, don't restate it).
- Skills may self-chain — invoke the next pipeline stage via the Skill
  tool — only when (a) the produced artifact passed its adversarial gate
  (critic READY), (b) the target is model-invocable (never
  `disable-model-invocation` targets — the flag removes them from the
  model's reach by design), and (c) the user has not scoped the request
  to the current stage; announce the invocation in one line before it
  happens. This bullet is the canonical gating explanation — skills cite
  it rather than restating it.
- SKILL.md bodies stay well under 500 lines; procedures as numbered steps or
  checklists; heavy reference goes in a separate file, loaded on demand.
- SKILL.md files put execution-critical contracts in their first 30 lines —
  skill bodies truncate when a session compacts; descriptions reload,
  bodies do not.
- Reference files over 100 lines open with a table of contents.
- References stay one level deep: SKILL.md → reference file, never
  reference → reference.
- Fields any skill reads programmatically — Status, Depends on, Priority
  (optional; absent = P2), Budget, and (post-review-fix-wave) Touch — are
  single-line `Key: value` headers above the file's first `##` heading;
  body sections are for humans and workers, never for orchestrator parsing.
- Every skill that produces an artifact must say where the file goes and what
  the next pipeline step is, and closes with a `Next stage:` line naming the
  next skill and the artifact path, marked "(self-chains per conventions)"
  or "(human-launched)". Terminal skills whose successor is genuinely a user
  action write `Next stage: none — <user action>`; never invent a stage to
  satisfy the format.
- Exact config JSON (hooks, permissions, headless flags) lives in a skill's
  `reference.md`, loaded on demand — never in the SKILL.md body.
- Agents keep hard output budgets (scout ≤300 words) — they exist to protect
  the caller's context; a verbose agent defeats its purpose.
- Concrete model names and CLI command templates appear in core files only
  as the inline Claude default; the mappings for other runtimes live in
  `runtimes/` profiles — new skills use tier language plus the inline
  default, never a bare model name.
- Skills that spawn agents follow the "Dispatch authoring" section of
  `.claude/rules/token-discipline.md` (tier by stage type, capped returns,
  bounded loops, single-call judge) — cite it, don't restate it.
- `.claude/` is the source of truth; `antigravity/` is a mirrored port
  (skills near-identical, agents→skills, human-only skills→workflows,
  hooks in Antigravity's JSON shape). When a skill changes here, mirror the
  change there in the same commit.
- `.claude-plugin/` distributes the toolkit as plugin `agentic` (marketplace
  `agentic-toolkit`); its skills manifest points at the `.claude/skills/`
  directory, so adding a skill needs no manifest edit (keep both manifest
  descriptions non-enumerating so that stays true) — but agents ARE
  enumerated in plugin.json by schema requirement, so a new agent DOES need
  a manifest edit; only skills stay manifest-free. Bump `version` in
  `plugin.json` whenever skill behavior changes.

## Testing changes

Test a skill by running it in a fresh session against a real repo and
watching where it stalls or over-reads — not by rereading the prose. For
description changes, check both that it triggers on its listed phrases and
does NOT trigger on neighbors' phrases. For skills with a stored evalset,
/evals (runner: `evals/run.sh`) is the repeatable complement — run it
before committing any skill change.
