# Task 14: Audit codex drain's real-content skill for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R6)
Touch: codex/.agents/skills/drain/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

`codex/.agents/skills/drain/SKILL.md` (one of Codex's four real-content
skills, not a symlink) is read in a three-way comparison against its Claude
Code source (`.claude/skills/drain/SKILL.md` and `reference.md`) AND its
Antigravity counterpart (`antigravity/.agents/workflows/drain.md`, already
reconciled against the Claude Code source this session — commits `e742cb6`,
`4d1edcc`) and reconciled per
`.claude/rules/mirror-procedure-discipline.md`'s load-bearing-vs-incidental
classification (read that rule first — task 01 must be done before this one
starts). A prior scout pass this session already flagged two specific
concerns worth re-checking closely: the tournament rank-step is spelled out
in full in Claude and Antigravity ("most PASS votes → fewest gate findings
→ smallest diff → lowest angle index") but the Codex version compresses it
to "rank their results" with no tie-break stated — confirm whether that's
still true and, if so, whether it's a real gap (a Codex worker following
"rank their results" alone could tie-break arbitrarily, producing
inconsistent tournament outcomes) or an intentional compression. Also
re-check the `max(2, 6−W)` baton formula and push-guard rules, which the
same scout pass noted are "restated near-verbatim across all three bodies"
— confirm they're still consistent post this session's baton-trigger fix
(commit `d35fc9e`, which changed step 3's closing line and step 3a's
opening in the Claude Code source only so far).

## Touch

Only the two files listed in the header. Do not touch
`.claude/skills/drain/` (SKILL.md or reference.md) or
`antigravity/.agents/workflows/drain.md` (both sources here — reconcile the
Codex mirror TO them, never edit either), any other skill's mirror files,
or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/drain/SKILL.md` and `reference.md` in full as the
   primary source of truth, and `antigravity/.agents/workflows/drain.md`
   as a second reference point.
3. Read `codex/.agents/skills/drain/SKILL.md` in full.
4. Compare procedure, not prose, with particular attention to: (a) the
   tournament rank-step tie-break (see note above), (b) the baton formula
   and step-3/3a loop-back gate language post commit `d35fc9e` (see note
   above), (c) the push-guard rules. Confirm the mirror expresses the same
   behavior unless the divergence is load-bearing (Codex's launch-gating,
   dispatch primitive, or sandboxing guards — already-identified,
   legitimate differences, not bugs).
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: codex-drain — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` otherwise (or if zero divergence
   was found).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (verifier-confirmed)
- [x] `grep -c "checked: codex-drain" tests/mirror-procedure-manifest.txt` → 1 (≥1); also four new `.claude/skills/drain/{SKILL.md,reference.md}|codex/.agents/skills/drain/SKILL.md|<phrase>` seed lines
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines (15 test files, verifier-confirmed)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 ("all ultra mentions gated in 4 files")
