# Task 04: VCS-agnostic prose rewrite — verifier, critic, scout agents

Status: done
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirements R3, R4, R6; decisions 1, 2)
Touch: .claude/agents/verifier.md, .claude/agents/critic.md, .claude/agents/scout.md, antigravity/.agents/skills/verifier/SKILL.md, antigravity/.agents/skills/critic/SKILL.md, antigravity/.agents/skills/scout/SKILL.md

## Goal

`.claude/agents/verifier.md`'s prose no longer assumes git as the only VCS
for its "restoring a path reverts the file" caution (R3). `critic.md` and
`scout.md` each carry a one-line note, outside their unchanged `tools:`
frontmatter, stating the Bash grant is git-specific and jj equivalents are a
deferred follow-up (R4, decision 2 — frontmatter values themselves are not
touched). Mirrors updated in the same commit: `skills/verifier/SKILL.md`
gets the same R3 treatment; `skills/critic/SKILL.md` gets ordinary
decision-1 rewriting of its one prose mention ("use git blame/log for
context") — R4's frontmatter-note does not apply there, it has no
`tools:`-frontmatter restriction to annotate; `skills/scout/SKILL.md` has 0
current git hits — verify and leave untouched unless the rewrite elsewhere
introduces one.

## Touch

This task owns exactly these three `.claude/agents/*.md` files and their
three mirrors. Do not touch any skill's SKILL.md/reference.md — those
belong to sibling tasks. Do not widen any `tools:` frontmatter grant (out of
scope, decision 2).

## Steps

1. Read `.claude/agents/verifier.md`, `.claude/agents/critic.md`,
   `.claude/agents/scout.md`.
2. `verifier.md` (R3): reword the "restoring a path reverts the file"
   caution (and any other git-only prose, per decision 1) to be VCS-agnostic
   intent, keeping git as a labeled example where useful.
3. `critic.md` and `scout.md` (R4): add a one-line note near (not inside)
   the `tools:` frontmatter block stating the `Bash(git ...)` grant is
   git-specific and that jj equivalents are an intentionally deferred
   follow-up. Do not change the `tools:` frontmatter values themselves.
4. Edit `antigravity/.agents/skills/verifier/SKILL.md` with the same R3
   rewrite.
5. Edit `antigravity/.agents/skills/critic/SKILL.md`: apply ordinary
   decision-1 rewriting to its "use git blame/log for context" prose mention
   — do not add an R4-style frontmatter note here (it doesn't have the
   frontmatter restriction to annotate).
6. Check `antigravity/.agents/skills/scout/SKILL.md` for git hits; verified
   0 in the spec's inventory — leave untouched unless a hit is found.

## Acceptance

- [x] `grep -n 'jj\|git-specific' .claude/agents/critic.md .claude/agents/scout.md` —
      at least one hit each.
- [x] `git diff --stat .claude/agents/verifier.md antigravity/.agents/skills/verifier/SKILL.md` —
      both show non-empty diffs.
- [x] `grep -n 'tools:' .claude/agents/critic.md .claude/agents/scout.md` —
      frontmatter values are unchanged from the pre-task version (`git show
      <base-commit>:.claude/agents/critic.md | grep 'tools:'` compared
      against the current line).
