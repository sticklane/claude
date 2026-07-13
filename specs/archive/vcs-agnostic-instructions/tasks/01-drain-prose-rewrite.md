# Task 01: VCS-agnostic prose rewrite — drain skill

Status: done
Depends on: none
Priority: P1
Budget: 35 turns
Spec: ../SPEC.md (requirements R1, R6; decisions 1, 4, 5)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

`.claude/skills/drain/SKILL.md` and `.claude/skills/drain/reference.md`
describe VCS actions in intent-level language per decision 1, with exactly
two named exceptions left untouched: `drain/reference.md:158`'s
`git update-ref refs/remotes/origin/main <default-branch>` line (decision 4,
labeled as a git-specific mechanic) and `drain/reference.md:732`'s
`--allowedTools` permission-grant string (decision 5). The matching edit
lands in `antigravity/.agents/workflows/drain.md` in the same commit,
preserving its own equivalent exempt lines.

## Touch

This task owns the drain skill and its single antigravity mirror file only.
Do not touch any other skill's SKILL.md/reference.md, any agents/*.md file,
or `.claude-plugin/plugin.json` (the version bump is the closing task's job,
not this one's).

## Steps

1. Read `.claude/skills/drain/SKILL.md` and `.claude/skills/drain/reference.md`
   in full.
2. Identify every backtick-wrapped `` `git <subcommand> ...` `` span. For
   each, apply decision 1: replace git-command syntax with intent-level
   phrasing (e.g. "isolate a worktree for this task" instead of `git
   worktree add -b task/NN-<slug>`), keeping VCS nouns (worktree, branch,
   commit, diff, log, rebase, push, pull, merge) as vocabulary. Where a
   concrete example materially helps, keep it but label it explicitly, e.g.
   "e.g., under git: `git push` fails with a rejection".
3. Leave `drain/reference.md:158`'s `git update-ref
   refs/remotes/origin/main <default-branch>` line exactly as-is, but confirm
   it is labeled as a git-specific mechanic (add the label if the current
   text doesn't already carry one) — decision 4.
4. Leave `drain/reference.md:732`'s `--allowedTools` template's literal
   `Bash(git add *)`/`Bash(git commit *)` strings unchanged — decision 5.
   Surrounding prose may note the grant is git-specific.
5. Read `antigravity/.agents/workflows/drain.md` and apply the same
   intent-level rewrite, preserving its own carve-out lines (the same
   plumbing line and permission-grant block, per R6's mapping row).
6. Re-run the detector command below and fix any remaining unlabeled hits.

## Acceptance

- [x] `rg -Un --pcre2 '`git[^`]*`' .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` — every
      hit's starting line either contains the literal substring "e.g., under
      git:" or is one of the two named exempt lines (the `git update-ref`
      line and the `--allowedTools` line); no other hit remains.
      Evidence: only two hits remain — reference.md:161 (the `git update-ref`
      exempt line, decision 4) and SKILL.md:236 (starting line carries
      "e.g., under git:"). All other backtick-wrapped git spans rewritten to
      intent-level phrasing.
- [x] `grep -n 'git update-ref' .claude/skills/drain/reference.md` still
      returns the line unchanged, now carrying a git-specific-mechanic label.
      Evidence: line 161 unchanged (`git update-ref refs/remotes/origin/main
      <default-branch>`) now labeled "— a git-specific mechanic, kept literal
      on purpose; a jj-based drain would need an equivalent
      tracking-ref/force-sync step, not yet designed".
- [x] `git diff --stat antigravity/.agents/workflows/drain.md` shows a
      non-empty diff (the mirror was updated in this same commit).
      Evidence: 35 insertions / 32 deletions; same intent-level rewrite
      applied, no exempt carve-out lines present in the mirror to preserve
      (no `git update-ref` plumbing line, no `--allowedTools` block).
