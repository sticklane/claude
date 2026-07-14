# Task 04: Worktree-removal-before-branch-deletion ordering (R4)

Status: done
Depends on: 03
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md

## Goal

Every drain cleanup step that deletes a branch (survivor-branch cleanup
after a tournament merge, `rescue/NN-<slug>-*` branch deletion after a DONE
merge, or any other branch-deletion path) states the VCS-neutral rule
first — remove the checkout/worktree before deleting the branch it was
checked out on — then gives the git-specific command sequence as an "e.g."
illustration only. This applies to BOTH the Tournament "Merge" step's
survivor cleanup (reference.md) and SKILL.md step 3's DONE-merge
rescue-branch deletion, both currently silent on ordering.

## Touch

Edit `.claude/skills/drain/reference.md`'s Tournament "Merge" step and
`.claude/skills/drain/SKILL.md` step 3's rescue-branch deletion — these are
the only two locations R4 names. Do NOT touch R1/R2/R3's already-landed
text (tasks 01–03) or `reference.md`'s rescue-RENAME procedure (the
`rescue/…` renaming path, which already gets this ordering right and needs
no change — use it as your model, don't edit it).

## Steps

1. Read `../SPEC.md`'s R4 requirement and Problem-section incident #4 in
   full.
2. Confirm the "failing test":
   `grep -c "remove the worktree before deleting the branch\|remove the checkout/worktree before deleting the branch" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
   currently returns 0 in both files.
3. Read `.claude/skills/drain/reference.md`'s Tournament "Merge" section
   (currently: "Delete survivor branches and worktrees only after some
   merge passes gates" — no sequence stated) and the rescue-RENAME
   procedure elsewhere in the same file (which already says "force-remove
   each worktree FIRST — a checked-out branch cannot be renamed away
   safely — then rename") to match its existing phrasing pattern.
4. Edit the Tournament "Merge" step's survivor-branch cleanup to state the
   VCS-neutral rule using this exact structure: "remove the worktree before
   deleting the branch" (or "remove the checkout/worktree before deleting
   the branch") — this exact wording is required, the acceptance grep below
   is not lenient to paraphrase — then give the git-specific command
   sequence as an "e.g." illustration.
5. Edit `.claude/skills/drain/SKILL.md` step 3's DONE-merge rescue-branch
   deletion the same way, using the same exact structure.
6. Run `bash evals/lint-ultra-gate.sh` and fix any drift.
7. Confirm the "green test": re-run the grep from step 2 on each file
   separately and check both now return ≥ 1.

## Acceptance

- [x] `grep -c "remove the worktree before deleting the branch\|remove the checkout/worktree before deleting the branch" .claude/skills/drain/reference.md` → ≥ 1 — returns 1 (Tournament "Merge" survivor cleanup)
- [x] `grep -c "remove the worktree before deleting the branch\|remove the checkout/worktree before deleting the branch" .claude/skills/drain/SKILL.md` → ≥ 1 — returns 1 (step 3 rescue-branch deletion)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 — "OK — all ultra mentions gated in 4 files", exit 0
