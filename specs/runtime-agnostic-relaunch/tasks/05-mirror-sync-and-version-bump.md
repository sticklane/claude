# Task 05: Antigravity workboard mirror sync + plugin version bump

Status: pending
Depends on: 02, 03
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (closing task — no new requirement, ships CLAUDE.md's mirror/version-bump convention for this generation of `.claude/skills/` changes)
Touch: antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, .claude-plugin/plugin.json

## Goal

This is the single closing commit for this spec's `.claude/skills/` changes.
Per CLAUDE.md's authoring conventions ("`.claude/` is the source of truth;
`antigravity/` is a mirrored port... A spec whose tasks change
`.claude/skills/` files must carry the mirror + plugin.json bump in some
task's `Touch:` — typically one closing task"), this task copies task 02's
finished `workboard.py`/`test_workboard.py` verbatim to
`antigravity/.agents/skills/workboard/` and bumps `.claude-plugin/plugin.json`'s
`version` once, after both skills-touching tasks (02: workboard.py, 03:
drain/reference.md) have landed — so the version bump reflects the whole
generation of skill changes, not a partial one, and neither task 02 nor 03
races the other for the same file.

## Touch

Only the antigravity workboard mirror files and `plugin.json`. Do not touch
`.claude/skills/workboard/workboard.py`, `.claude/skills/workboard/test_workboard.py`,
or `.claude/skills/drain/reference.md` — those are already finished by
tasks 02 and 03; this task only copies and bumps.
`antigravity/.agents/workflows/drain.md` is out of scope — task 03's change
has no antigravity counterpart (confirmed: Antigravity's baton section is a
deliberate paraphrase, not a mirror).

## Steps

1. Confirm tasks 02 and 03 are both merged (their Status is not `pending`).
2. Copy `.claude/skills/workboard/workboard.py` to
   `antigravity/.agents/skills/workboard/workboard.py`, byte-for-byte.
3. Copy `.claude/skills/workboard/test_workboard.py` to
   `antigravity/.agents/skills/workboard/test_workboard.py`, byte-for-byte.
4. Bump the `version` field in `.claude-plugin/plugin.json` (patch or minor
   bump — this spec changes skill behavior in two skills, workboard and
   drain).

## Acceptance

- [ ] `diff -q .claude/skills/workboard/workboard.py antigravity/.agents/skills/workboard/workboard.py` → no output (identical)
- [ ] `diff -q .claude/skills/workboard/test_workboard.py antigravity/.agents/skills/workboard/test_workboard.py` → no output (identical)
- [ ] `git show <base-commit>:.claude-plugin/plugin.json | grep '"version"'` (where `<base-commit>` is this task's starting commit) differs from `grep '"version"' .claude-plugin/plugin.json` on the current tree (version bumped from its value at task start, not a hard-coded literal)
- [ ] `python3 -m unittest discover -s antigravity/.agents/skills/workboard` → passes (mirrored tests run clean in place)
