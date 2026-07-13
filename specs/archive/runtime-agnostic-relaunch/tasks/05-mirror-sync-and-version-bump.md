# Task 05: Antigravity workboard mirror sync + plugin version bump

Status: done
Depends on: 02, 03
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (closing task — no new requirement, ships CLAUDE.md's mirror/version-bump convention for this generation of `.claude/skills/` changes)
Touch: antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, antigravity/runtimes, .claude-plugin/plugin.json

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
4. Create `antigravity/runtimes` as a **relative symlink** to `../runtimes`
   (i.e. `ln -s ../runtimes antigravity/runtimes`). Do NOT copy the
   `runtimes/` subtree — this repo's established pattern (see the `codex/`
   overlay, which symlinks into `antigravity/.agents/skills/*` rather than
   copying) is reuse-via-symlink for exactly this situation, and it keeps
   `runtimes/parse_headless.py` and the `.md` profiles single-sourced. This
   symlink is what makes the byte-for-byte `workboard.py` copy actually
   importable in place: its `SCRIPT.parents[3] / "runtimes"` resolution
   (workboard.py:52) counts up from the mirror's own path
   (`antigravity/.agents/skills/workboard/workboard.py` → `parents[3]` =
   `antigravity/`), so it needs `antigravity/runtimes/parse_headless.py` to
   exist — the symlink satisfies that without duplicating the file.
5. Bump the `version` field in `.claude-plugin/plugin.json` (patch or minor
   bump — this spec changes skill behavior in two skills, workboard and
   drain).

## Acceptance

- [x] `diff -q .claude/skills/workboard/workboard.py antigravity/.agents/skills/workboard/workboard.py` → no output (identical)
- [x] `diff -q .claude/skills/workboard/test_workboard.py antigravity/.agents/skills/workboard/test_workboard.py` → no output (identical)
- [x] `test -L antigravity/runtimes && readlink antigravity/runtimes` → prints `../runtimes` (a symlink, not a copied directory)
- [x] `git show <base-commit>:.claude-plugin/plugin.json | grep '"version"'` (where `<base-commit>` is this task's starting commit) differs from `grep '"version"' .claude-plugin/plugin.json` on the current tree (version bumped from its value at task start, not a hard-coded literal)
- [x] `python3 -m unittest discover -s antigravity/.agents/skills/workboard` → passes (mirrored tests run clean in place)

## Progress

- 2026-07-11: First attempt returned DEFERRED — the byte-for-byte
  `workboard.py` copy imports `parse_headless` via a path computed relative
  to its own location, which resolves to `antigravity/runtimes/` when
  mirrored, and that directory didn't exist (`ModuleNotFoundError` broke
  all 110 mirrored tests). Resolved by the orchestrator: added a symlink
  step (`antigravity/runtimes -> ../runtimes`) rather than copying the
  `runtimes/` subtree, matching this repo's established symlink-for-reuse
  pattern (the `codex/` overlay). Re-dispatching with the expanded `Touch`
  and the new step/acceptance criterion above.
