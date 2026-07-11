# Task 07: End-to-end verification sweep and plugin.json version bump

Status: pending
Depends on: 01, 02, 03, 04, 05, 06
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (all requirements — acceptance criteria; CLAUDE.md authoring conventions on plugin.json version bumps)
Touch: .claude-plugin/plugin.json

## Goal

All six preceding tasks are merged. This task runs the full spec-level
acceptance sweep (every checkbox in `../SPEC.md`'s Acceptance criteria
section) against the merged state, fixes any gap it finds, and bumps
`.claude-plugin/plugin.json`'s `version` once — per this repo's CLAUDE.md
authoring convention that a spec touching `.claude/skills/` files carries
the mirror + plugin.json bump in one closing task's `Touch:`, rather than
in every task that touches a mirror.

## Touch

This task's only content edit is the `version` field bump in
`.claude-plugin/plugin.json`. It may read (not edit) any other file in the
repo while running the verification sweep; if the sweep finds a genuine gap
in a prior task's work, fix it in the file that task owns, not here — flag
it in Progress instead if the fix is nontrivial.

## Steps

1. Confirm tasks 01-06 are all merged (Status: done) before starting.
2. Run each acceptance-criteria command from `../SPEC.md`'s Acceptance
   criteria section against the current repo state:
   - The `rg -Un --pcre2` git-command-span detector across every R1-scope
     file.
   - The evals/reference.md untouched-diff check (decision 6).
   - The concurrent-sessions.md, gate/SKILL.md, gate/reference.md,
     critic.md/scout.md grep checks (R2, R4, R5).
   - The R6 mirror-mapping check (each listed counterpart has a non-empty
     diff; each "no counterpart" row has no mirror file created) —
     **except** the three rows verified in the spec's own inventory to be
     correctly unchanged: `workflows/critique.md` (0 git hits, no edit
     needed unless the Claude-side edit introduced a mismatch — verify
     still 0, don't require a diff), `antigravity/.agents/skills/gate/SKILL.md`
     (decision 3: no git-hook callout needed there, different mechanism),
     and `skills/scout/SKILL.md` (0 git hits, R4's frontmatter-note doesn't
     apply). For these three, a non-empty diff is not required — confirm
     "still correctly 0 hits" instead of "diff is non-empty".
   - `python3 antigravity/.agents/skills/workboard/test_workboard.py` (R7).
   - The global-file and antigravity/README.md grep checks (R8, R9).
3. If any check fails, note it in Progress rather than silently patching
   another task's Touch scope — this task's own edit budget is the
   version bump only.
4. Bump `.claude-plugin/plugin.json`'s `version` field (patch or minor bump,
   matching this repo's existing versioning convention).

## Acceptance

- [ ] All Acceptance-criteria commands from `../SPEC.md` pass against the
      merged repo state (paste each command's pass/fail into Progress).
- [ ] `git show <base-commit>:.claude-plugin/plugin.json | grep version`
      differs from the current `version` value in
      `.claude-plugin/plugin.json` (version was bumped from this task's own
      base commit, not compared to a hard-coded literal).
