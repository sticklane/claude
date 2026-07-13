# Task 06: Audit gate's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/skills/gate/SKILL.md, antigravity/.agents/skills/gate/reference.md, antigravity/.agents/workflows/gate.md, tests/mirror-procedure-manifest.txt

## Goal

`gate`'s Antigravity mirror is read side-by-side against its source
(`.claude/skills/gate/SKILL.md` and its `reference.md`) and reconciled per
`.claude/rules/mirror-procedure-discipline.md`'s load-bearing-vs-incidental
classification (read that rule first — task 01 must be done before this one
starts).

Note: an earlier scout pass this session mistakenly compared the wrong
file (`antigravity/.agents/workflows/gate.md`, a thin pointer) and
concluded "no installer script" was a bug. A closer read of the REAL
content file, `antigravity/.agents/skills/gate/SKILL.md`, found it
correctly defers install specifics to its own `reference.md` rather than
citing `bin/install-gates` (which has no Antigravity equivalent, since
Antigravity uses `hooks.json` + `.agents/hooks/*.sh`, a different config
format with no shared installer possible) — this looked load-bearing on
that quick read, not a bug. This task's job is to do the FULL side-by-side
read this deserves (both `SKILL.md` and `reference.md` in both trees, not
just the top-level file) and confirm or correct that preliminary read.

## Touch

Only the files listed in the header. Do not touch any other skill's mirror
files, `.claude/skills/gate/` (the source — reconcile the mirror TO it,
never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/gate/SKILL.md` and `.claude/skills/gate/reference.md`
   in full as the source of truth.
3. Read `antigravity/.agents/skills/gate/SKILL.md` and its `reference.md`
   in full, plus `antigravity/.agents/workflows/gate.md` (confirm whether
   it's a pointer or real content).
4. Compare procedure, not prose: for each step/decision point in the
   source, confirm the mirror expresses the same behavior unless the
   divergence is load-bearing (Antigravity's `hooks.json`/`hooks/*.sh`
   format vs. Claude Code's settings.json hooks is a real, inherent
   difference — don't force parity where the underlying config format
   differs).
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: gate — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found — this must be written regardless of outcome, confirming or
   correcting the preliminary note above).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (verified: exit=0)
- [x] `grep -c "checked: gate" tests/mirror-procedure-manifest.txt` → ≥1 (verified: 1; plus a new manifest phrase line `...|delegate the run to a subagent`)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines (verified: none)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 (verified: "OK — all ultra mentions gated in 4 files")
