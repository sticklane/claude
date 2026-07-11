# Task 05: workboard skill detects `.jj/` repo roots + VCS-agnostic reference.md

Status: in-progress
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirement R7, amended; decision 1) — plus a breakdown-time addendum: the original survey's inventory never listed `.claude/skills/workboard/` at all, only its antigravity mirror. Per `docs/memory/workboard-mirror-verbatim.md`, workboard's two `.py` files are kept byte-for-byte identical across `.claude/` and `antigravity/.agents/`, and `.claude/` is the source of truth (CLAUDE.md convention) — so the jj-detection fix belongs in the `.claude/` copy first, then ported verbatim, not the reverse. `workboard/reference.md` (both copies) also carries git-command hits missed by the original inventory; this task folds in their ordinary decision-1 rewrite since it's the same skill directory.
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, .claude/skills/workboard/reference.md, antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, antigravity/.agents/skills/workboard/reference.md

## Goal

`.claude/skills/workboard/workboard.py`'s repo-root detection (the source of
truth) treats a directory containing `.jj/` the same as one containing
`.git/` — today it misdetects jj-only repos as "not a repo". A new test in
`.claude/skills/workboard/test_workboard.py` covers this. The fix is ported
verbatim to the antigravity mirror (byte-identical, per
`docs/memory/workboard-mirror-verbatim.md` — copy, don't re-implement).
`workboard/reference.md`'s git-command-syntax hits (e.g. `` `git -C <repo>
…` ``, `` `git rev-parse --show-toplevel` ``) get the same decision-1
intent-level rewrite as any other R1 file, in both copies; its bare
`gitBranch`/`git` JSON-field-name mentions are not command syntax and are
untouched.

## Touch

This task owns exactly these six files (three files × two trees). Do not
touch any other skill.

## Steps

1. Read `.claude/skills/workboard/workboard.py`'s repo-root detection logic
   (the `if (Path(dirpath) / ".git").exists()` check).
2. Write a failing test first in `.claude/skills/workboard/test_workboard.py`:
   a directory containing only a `.jj/` subdirectory (no `.git/`) should be
   detected as a repo root. Run it and confirm it fails for the right
   reason.
3. Update `.claude/skills/workboard/workboard.py`'s detection logic to also
   treat `.jj/` as a valid repo-root marker.
4. Re-run the test suite and confirm the new test passes and no existing
   test regresses.
5. Port the change verbatim: `cp .claude/skills/workboard/workboard.py
   antigravity/.agents/skills/workboard/workboard.py` and the same test
   addition into `antigravity/.agents/skills/workboard/test_workboard.py`
   (its module-invocation docstring path differs by design — see the
   existing one-line diff between the two test files — keep that line
   as-is, don't force full byte-identity on it). Confirm `diff -q` on the
   two `workboard.py` copies reports no difference.
6. Read `.claude/skills/workboard/reference.md` and
   `antigravity/.agents/skills/workboard/reference.md`. Apply decision 1's
   rewrite to backtick-wrapped git-command spans only (not bare field-name
   mentions like `gitBranch`).
7. Run both test suites (`.claude/` and `antigravity/`) to confirm green.

## Acceptance

- [ ] `python3 -m unittest discover -s .claude/skills/workboard` passes,
      including the new `.jj/`-detection test.
- [ ] `python3 -m unittest discover -s antigravity/.agents/skills/workboard`
      passes, including the same test.
- [ ] `diff -q .claude/skills/workboard/workboard.py antigravity/.agents/skills/workboard/workboard.py`
      reports no difference.
- [ ] `rg -Un --pcre2 '`git[^`]*`' .claude/skills/workboard/reference.md antigravity/.agents/skills/workboard/reference.md` —
      every remaining hit is a bare field-name mention, not shell-executable
      command syntax.
