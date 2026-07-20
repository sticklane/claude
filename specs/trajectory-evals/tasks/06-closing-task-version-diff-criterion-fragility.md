Status: draft
Discovered-from: specs/trajectory-evals/tasks/04-closing-antigravity-and-version.md
Spec: ../SPEC.md
Blocking: no

# closing-task version-diff acceptance criteria should not anchor on a bare HEAD~1

A closing task's acceptance criterion checking a plugin.json version bump
via `git show HEAD~1:...` silently degrades to a false negative if any
commit lands after the version-bump commit. /breakdown's authoring
convention for closing tasks should anchor version-diff criteria to the
bump commit explicitly (or require the bump to be the branch's last
commit) instead of a bare `HEAD~1`.

## Acceptance

- [ ] `.claude/skills/breakdown/SKILL.md`'s version-bump criterion
      paragraph (currently the differs-from-base shape,
      `git show <base-commit>:<path>`) is rewritten to prescribe
      asserting the bump commit's own diff:
      `grep -c 'bump commit' .claude/skills/breakdown/SKILL.md` ≥ 1 and
      `grep -c 'anchored-acceptance-criteria' .claude/skills/breakdown/SKILL.md`
      ≥ 1 (both 0 today, verified 2026-07-19 — the paragraph cites
      `docs/memory/anchored-acceptance-criteria.md`'s
      `git show <closing-commit> -- <file> | grep -q '^+.*"version"'`
      pattern rather than restating it, and warns that a bare `HEAD~1`
      anchor degrades to a false negative once any commit lands after
      the bump).
- [ ] Per-file mirror anchors (multi-file rule in the memory doc): the
      same two greps each ≥ 1 on
      `antigravity/.agents/skills/breakdown/SKILL.md` (both 0 today,
      verified 2026-07-19).
- [ ] Skill behavior changed, so `.claude-plugin/plugin.json` is bumped,
      asserted with the very pattern this task mandates:
      `git show <task-commit> -- .claude-plugin/plugin.json | grep -q '^+.*"version"'`
      where `<task-commit>` is the commit that lands this task — never a
      bare `HEAD~1`.

Depth ceiling: the convention edit is authoring prose (L0 anchors) — the
behavioral complement is a `/breakdown` eval scenario under
`evals/breakdown/` asserting a generated closing task's version-diff
criterion names the bump commit rather than `HEAD~1` (human-launched,
paid; manual-pending for a drained worker per
docs/memory/unattended-worker-tool-limits.md).
