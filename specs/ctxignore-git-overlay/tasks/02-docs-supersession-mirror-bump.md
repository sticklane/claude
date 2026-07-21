# Task 02: docs, parent-spec supersession, mirror + plugin bump

Status: done
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

- [x] `grep -c 'ctxignore' context-tree/README.md` → ≥ 2 — got 4 (new
      "Excluding paths with `.ctxignore`" subsection).
- [x] `grep -ci 'ctxignore' .claude/skills/ctx/SKILL.md` → ≥ 1 — got 1
      (Optional wiring bullet naming `.ctxignore` for committed-but-derived
      paths).
- [x] `grep -ci 'ctxignore' antigravity/.agents/skills/ctx/SKILL.md` → ≥ 1
      — got 1 (mirror bullet, same concept in the mirror's voice).
- [x] `grep -c 'ctxignore-git-overlay' specs/codebase-context-tree/SPEC.md`
      → ≥ 1 — got 2; R4 now reads "`.ctxignore` as an exclusion overlay
      honored in both modes" with a supersession pointer, no longer
      no-VCS-baseline-only.
- [x] `git show <task-base-commit>:.claude-plugin/plugin.json | grep '"version"'`
      differs from current — base 7800c94 `0.9.28` → `0.9.29`.
      (Evidence: specs/ctxignore-git-overlay/evidence/02-docs-supersession-mirror-bump.md)
