# Task 02: Antigravity mirror and plugin version bump

Status: in-progress
Depends on: 01
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/harness-audit/SKILL.md, antigravity/.agents/skills/harness-audit/reference.md, codex/.agents/skills/harness-audit, .claude-plugin/plugin.json

## Goal

The new harness-audit skill has an antigravity mirror at
`antigravity/.agents/skills/harness-audit/` (SKILL.md + reference.md) per
CLAUDE.md's mirror-procedure-discipline (a port, not a copy -- same
procedure, prose may diverge where antigravity's own mechanism forces it),
a codex symlink at `codex/.agents/skills/harness-audit` pointing at the
antigravity mirror (per CLAUDE.md's port-chain convention: "codex/.agents/skills/
symlinks the ~15 already-working antigravity/.agents/skills/* directories"),
and `.claude-plugin/plugin.json`'s `version` is bumped above its value as of
this task's own base commit.

## Touch

Only the antigravity mirror files, the codex symlink, and plugin.json's
version field. Do not re-edit `.claude/skills/harness-audit/SKILL.md` or
`reference.md` (task 01's files) beyond reading them as the mirror source.

## Steps

1. Read the merged `.claude/skills/harness-audit/SKILL.md` and
   `reference.md` from task 01.
2. Port them to `antigravity/.agents/skills/harness-audit/SKILL.md` and
   `reference.md`, following this repo's existing mirror pattern for a
   comparable two-file skill (e.g. `antigravity/.agents/skills/gate/`) --
   same procedure, same steps, same order, same stated conditions
   (`.claude/rules/mirror-procedure-discipline.md`: classify any divergence
   as load-bearing (antigravity's own mechanism forces it) or incidental
   (fix it) before leaving it). Per `docs/memory/workboard-mirror-verbatim.md`,
   this is a paraphrased port, not a byte-identical copy -- do not write or
   rely on a `diff -q` style check for this file.
3. Symlink `codex/.agents/skills/harness-audit` to the antigravity mirror,
   matching the existing pattern (e.g. `ln -s ../../../antigravity/.agents/skills/harness-audit codex/.agents/skills/harness-audit`
   -- confirm the exact relative depth against an existing symlink such as
   `codex/.agents/skills/gate` before creating it, since a wrong relative
   path creates a dangling link that `tests/test_codex_parity.sh` treats as
   uncovered).
4. Per CLAUDE.md's authoring conventions, a new skill needs no
   `.claude-plugin/plugin.json` skills-manifest edit (the manifest points at
   the `.claude/skills/` directory generically) -- only bump the `version`
   field since this task's changes constitute a skill-behavior change.

## Acceptance

- [ ] `test -f antigravity/.agents/skills/harness-audit/SKILL.md`
- [ ] Content-coverage check (not byte-diff, per workboard-mirror-verbatim):
      `F=antigravity/.agents/skills/harness-audit/SKILL.md; grep -qi "read-only" $F && grep -qi "command currency" $F && grep -qi "gate coverage" $F && grep -qi "evalset" $F && grep -qi "memory hygiene" $F && grep -qi "allowlist" $F`
- [ ] `bash tests/test_antigravity_parity.sh` -> exit 0, no "harness-audit" line
- [ ] `bash tests/test_codex_parity.sh` -> exit 0, no "harness-audit" line
- [ ] Version bumped from this task's own base commit:
      `BASE=$(git merge-base main HEAD); OLD=$(git show $BASE:.claude-plugin/plugin.json | grep '"version"'); NEW=$(grep '"version"' .claude-plugin/plugin.json); [ "$OLD" != "$NEW" ]`
