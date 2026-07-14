# Verification: Task 02 — critique-rerun-skip

Verdict: **FAIL**

## Mechanical acceptance criteria

| #   | Command                                                                                                                       | Expected                                                  | Actual                                                              | Result                                 |
| --- | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------- |
| 1   | `grep -c "hash" .claude/skills/critique/SKILL.md`                                                                             | ≥1                                                        | 9                                                                   | ✓                                      |
| 2   | `grep -c "Cheap-before-expensive short-circuit" .claude/skills/drain/reference.md`                                            | 0                                                         | 0                                                                   | ✓                                      |
| 3   | `grep -c "mechanized in /critique" docs/memory/drain-dispatch-lessons.md`                                                     | ≥1                                                        | 2                                                                   | ✓                                      |
| 4   | Literal grep `"NOT-READY specs (critique intake) \| \`decide\` \| §4"`                                                        | pre-known to fail (BRE `\|` literal) at both base and now | exit 1 (as expected, pre-existing mis-spec)                         | ✓ (per task note)                      |
| 4b  | Intent check: `diff <(git show 5fdbedb:...reference.md \| grep 'NOT-READY specs (critique intake)') <(grep ... reference.md)` | no diff                                                   | no diff (exit 0)                                                    | ✓ row byte-identical, survives removal |
| 5   | `bash evals/lint-ultra-gate.sh`                                                                                               | exit 0                                                    | `lint-ultra-gate: OK — all ultra mentions gated in 4 files`, exit 0 | ✓                                      |

All 5 mechanical criteria pass.

## Substance review

1. **critique/SKILL.md**: new bold paragraph before step 1 implements the
   content-hash re-run skip — computes SPEC.md's hash, compares to
   `critique-findings.md`'s recorded header, treats missing/unparseable hash
   as "run the critic" (never a false match), scoped to SPEC.md targets
   only. New step 6 persists the findings file (header hash + verdict +
   dated findings) atomically on settled NOT READY / READY WITH NITS,
   explicitly skipped when the re-run gate already relayed a recorded
   verdict, and names `/critique` as sole owner of the file. Matches Goal
   and Steps 2–3. Ultra section untouched (confirmed lint-ultra-gate green).

2. **drain/reference.md Critique intake**: the whole
   "Cheap-before-expensive short-circuit" bullet (git-log-based, ~30 lines)
   is removed; the `/critique` invocation bullet is now unconditional and
   explains the skip now lives inside `/critique`, keyed on content hash.
   NOT-READY bullet re-attributed to `/critique`. Worker-prompt DEFERRED
   text (~line 590) and the routing-table row (~line 1685,
   `NOT-READY specs (critique intake) | \`decide\` | §4`) are confirmed
   untouched (byte-identical diff above; separately viewed at line 590,
   present and unrelated to this change).

3. **docs/memory/drain-dispatch-lessons.md**: the "Critique intake" entry
   is rewritten to read "mechanized in /critique" and correctly explains
   content-hash vs. the old `git log -1 --format=%ct`/`%H` recipe, citing
   `specs/critique-findings-loop-closure` R5. Matches Step 5.

## Scope-creep finding (FAIL basis)

The task's `Touch` line is explicit: `docs/memory/drain-dispatch-lessons.md
(update the one entry named above only)`. The actual diff
(`git diff 5fdbedb -- docs/memory/drain-dispatch-lessons.md`) touches **two
unrelated entries** that have nothing to do with Critique intake:

- "Multi-spec concurrent drain: Touch-disjointness is per-spec, not global"
  — italic markdown converted from `*within*`/`*different*` to
  `_within_`/`_different_`.
- The "followed by an 's'" grep-pattern entry — same asterisk→underscore
  conversion for `*first*`/`*only*`.

These are pure markdown-emphasis-style edits (asterisk to underscore),
unrelated to R5/R6 and outside the Touch list's "only" instruction. Per
verification protocol, convention-driven edits outside the Touch list are
scope creep even when a repo linter/formatter motivated them — this should
have been reported as a convention gap, not silently applied.

## Task-file bookkeeping gap (secondary finding)

`Status:` on the task file is still `in-progress` (not flipped to done/
review), and none of the six acceptance checkboxes are ticked, despite all
implementation commits (`0cc0f56`, `5216abe`, `f323a4f`) already existing on
the branch and all 5 mechanical criteria passing. The append-only task-file
diff (`git diff 5fdbedb -- specs/critique-findings-loop-closure/tasks/02-critique-rerun-skip.md`)
shows only the PLAN comment block added — no Status flip, no checkbox
ticks, no evidence-citation lines — which is compliant with the append-only
rule as far as it goes, but leaves the task file understating completion.

## MANUAL criteria (not exercised)

The two MANUAL acceptance items (end-to-end drain critique-intake exercise;
double `/critique` invocation confirming skip-then-real-dispatch) require
live model/agent invocation of `/critique` and, for the first, a real drain
run against a NOT-READY spec — genuinely interactive verification outside
this verifier's mechanical-check scope and tool budget. Not exercised;
flagged as still-open per the task's own MANUAL labeling.

## Verdict

**FAIL** — all 5 mechanical acceptance criteria pass and the substance
(critique SKILL.md hash-skip + persist step, drain reference.md short-circuit
removal, memory entry rewrite) is correct and matches Goal/Steps. However,
the diff to `docs/memory/drain-dispatch-lessons.md` includes edits to two
entries outside the Touch list's "update the one entry named above only"
scope (unrelated markdown emphasis-style changes), which is scope creep per
verification protocol. Additionally the task file's Status/checkboxes were
never flipped despite the work being substantively complete on this branch.
