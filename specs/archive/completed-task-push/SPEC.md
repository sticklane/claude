# Push completed tasks on the attended execution stages

## Problem

The attended execution skills merge a completed, verifier-PASSED task to the
integration branch (`main`) but never push it. Concretely (scout 2026-07-04):

- **drain** — `drain/SKILL.md:148–149` commits immediately after the DONE
  merge; `drain/reference.md:132` tells workers "do not push"; there is **no
  `git push` anywhere** in drain. Merges land locally only.
- **build** — `build/SKILL.md:81–84` commits on completion; `:84` gates push
  behind "only if the user asked".
- **parallel** — `parallel/SKILL.md:63–66` merges DONE branches in task order;
  no push logic.

Result: finished work sits on local `main` invisibly until a human pushes by
hand, and the workboard's "unpushed commits" flag fires on routine drain lag
rather than on genuinely-stuck work. (This is the source-side companion to the
workboard `active`-group reclassification task — once completion pushes, the
unpushed flag becomes a real signal.)

**autopilot is deliberately excluded.** `autopilot/SKILL.md:28` scopes its
permissions to "build/test/commit but NOT push"; `:53` lists push among the
high-risk actions an unattended run "must never take on its own." Autopilot is
unattended, so it keeps escalating push to the human — this spec does not touch
that invariant.

## Solution

Add a **push-on-completion** step to the three *attended* stages
(drain, build, parallel) only, at the orchestrator/session level (never the
worker — workers still never push). The push is upstream-guarded and
non-fatal, mirrored to the antigravity workflow counterparts in the same
commit, with a `plugin.json` version bump.

Decided (interview 2026-07-04): **per completed task, not batched at run end**
(work is backed up the moment it lands); **attended stages only** (autopilot
excluded).

## Requirements

- R1: **drain** — after the orchestrator merges a DONE task to `main` and
  writes its bookkeeping/status-flip commit (`drain/SKILL.md:148–149`), it
  pushes `main`. Per completed task. Worker prompt (`reference.md:132`)
  unchanged — workers still never push.
- R2: **build** — replace the conditional at `build/SKILL.md:84` ("push only
  if the user asked") with an unconditional push-after-commit on task
  completion, subject to the R4 guard.
- R3: **parallel** — after each DONE branch is merged and its gates pass
  (`parallel/SKILL.md:63–66`), push `main`. Per merged task.
- R4: **Push guard (all three).** Push only when the integration branch has a
  configured upstream/remote; if none, skip silently (no failure). Never
  `--force`. A push that fails (non-fast-forward, offline, rejected hook)
  emits a warning and continues — the merge already landed locally, so a
  failed push never fails the task or aborts the run. State this guard once in
  each skill and cite it, don't restate.
- R5: **autopilot unchanged** — its push prohibition (`SKILL.md:28`, `:53`)
  stays. Add one line making the *attended-only* scope explicit so the
  divergence is intentional on the record, not an omission.
- R6: **Mirror + bump.** Each changed skill's antigravity counterpart
  (`antigravity/.agents/workflows/{drain,build,parallel}.md`) carries the same
  change in the same commit; `.claude-plugin/plugin.json` `version` bumped once
  (currently `0.7.3`).

## Out of scope

- Any change to what gets committed, the merge order, worktree isolation, or
  verifier gating — only the push step is added.
- Pushing from workers or from autopilot.
- Branch/PR flows (open-a-PR-instead) — this spec pushes the integration
  branch directly, matching how these repos already operate on `main`.
- Repo-specific "never auto-push" opt-outs — deferred; R4's upstream guard is
  the only gate in v1. (Add a follow-up task if a repo needs to suppress.)

## Acceptance criteria

- [ ] `grep -n 'git push' .claude/skills/drain/SKILL.md
      .claude/skills/build/SKILL.md .claude/skills/parallel/SKILL.md` shows a
      push step in each, each within ±3 lines of the R4 upstream-guard wording.
- [ ] `.claude/skills/autopilot/SKILL.md` still contains its push prohibition
      AND a new one-line attended-only-scope note.
- [ ] `git show --stat HEAD` includes both `.claude/skills/` and
      `antigravity/.agents/workflows/` paths for each changed skill;
      `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a version bump.
- [ ] End-to-end: a `/build` on a toy task in a repo WITH an upstream pushes on
      completion; the same in a repo with NO upstream completes cleanly and
      does not error (R2, R4).

## Open questions

(none)
