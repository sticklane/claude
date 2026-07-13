# Task 13: Audit codex build's real-content skill for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R6)
Touch: codex/.agents/skills/build/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

`codex/.agents/skills/build/SKILL.md` (one of Codex's four real-content
skills, not a symlink) is read in a three-way comparison against its Claude
Code source (`.claude/skills/build/SKILL.md`) AND its Antigravity
counterpart (`antigravity/.agents/workflows/build.md`, already reconciled
against the Claude Code source this session — commit `4d1edcc`) and
reconciled per `.claude/rules/mirror-procedure-discipline.md`'s
load-bearing-vs-incidental classification (read that rule first — task 01
must be done before this one starts). A prior scout pass this session
already noted build's procedure (steps 0-4: load, plan, implement, verify,
close-out) is "copied nearly verbatim across Claude/Antigravity/Codex —
currently in sync" but flagged it as the textbook shape of incidental
duplication even with zero drift found; this task's job is to confirm that
still holds with a full fresh read, not assume it.

## Touch

Only the two files listed in the header. Do not touch
`.claude/skills/build/SKILL.md` or `antigravity/.agents/workflows/build.md`
(both sources here — reconcile the Codex mirror TO them, never edit either),
any other skill's mirror files, or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/build/SKILL.md` in full as the primary source of
   truth, and `antigravity/.agents/workflows/build.md` as a second
   reference point (both should already agree with each other post-
   commit-`4d1edcc`).
3. Read `codex/.agents/skills/build/SKILL.md` in full.
4. Compare procedure, not prose: for each step/decision point in the
   sources, confirm the Codex mirror expresses the same behavior unless
   the divergence is load-bearing (Codex's launch-gating via
   `allow_implicit_invocation: false`, its worktree/Bash-retry guards from
   sandboxing differences, or the absence of a `reference.md` to cite —
   these are real, already-identified load-bearing differences, not bugs).
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: codex-build — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (verifier-confirmed; evidence/13-audit-codex-build.md)
- [x] `grep -c "checked: codex-build" tests/mirror-procedure-manifest.txt` → 1 (verifier-confirmed; evidence/13-audit-codex-build.md)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines (verifier-confirmed; evidence/13-audit-codex-build.md)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 (verifier-confirmed; evidence/13-audit-codex-build.md)
