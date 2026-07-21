# Task 02: docs, parent-spec supersession, mirror + plugin bump

Status: pending
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirements R6, R7)
Touch: context-tree/README.md, .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md, .claude-plugin/plugin.json, specs/codebase-context-tree/SPEC.md

## Goal

The shipped overlay behavior is documented and the canonical contracts
stop contradicting it: `context-tree/README.md` documents `.ctxignore` as
an overlay honored in both modes (committed-build-output motivation);
the `/ctx` skill and its antigravity mirror each gain one line naming
`.ctxignore` for excluding committed-but-derived paths; the plugin
version is bumped; and `specs/codebase-context-tree/SPEC.md` R4/R5 plus
its `ignore_rules` acceptance line are amended to "honored in both
modes" with a one-line supersession pointer to `ctxignore-git-overlay`.

## Touch

Doc-and-metadata only — no Rust changes (task 01's charter). The
antigravity SKILL.md is a paraphrased port, not a byte-identical copy
(docs/memory/workboard-mirror-verbatim.md): carry the concept in the
mirror's own voice, never diff-sync the files. In
`specs/codebase-context-tree/SPEC.md`, amend only the R4/R5 bullet text
and the matching acceptance line — no other requirement or task file of
the parent spec.

## Steps

1. Read `../SPEC.md` R6/R7 and the current `.ctxignore` prose in
   `context-tree/README.md` (if any), `.claude/skills/ctx/SKILL.md`, and
   `specs/codebase-context-tree/SPEC.md` lines ~155-163 (R4/R5) plus its
   `ignore_rules` acceptance line.
2. Make the four doc edits and the parent-spec amendment; bump
   `"version"` in `.claude-plugin/plugin.json` (skill behavior changed —
   CLAUDE.md's port-chain convention).
3. Verify with the acceptance greps.

## Acceptance

Depth ceiling: L0 greps — every artifact here is prose/metadata; the
behavioral complement is task 01's cargo suite, plus a human read of the
README paragraph at review.

- [ ] `grep -c 'ctxignore' context-tree/README.md` → ≥ 2
- [ ] `grep -ci 'ctxignore' .claude/skills/ctx/SKILL.md` → ≥ 1
- [ ] `grep -ci 'ctxignore' antigravity/.agents/skills/ctx/SKILL.md` → ≥ 1
- [ ] `grep -c 'ctxignore-git-overlay' specs/codebase-context-tree/SPEC.md`
      → ≥ 1, and its R4 no longer reads "in the no-VCS baseline" as the
      only `.ctxignore` mode
- [ ] `git show <task-base-commit>:.claude-plugin/plugin.json | grep '"version"'`
      differs from `grep '"version"' .claude-plugin/plugin.json` — the
      version moved from this task's own base commit (base-relative, NOT
      the spec's authoring-time `0.9.23` literal: sibling specs also bump
      this file, so a pinned literal can pass vacuously)
