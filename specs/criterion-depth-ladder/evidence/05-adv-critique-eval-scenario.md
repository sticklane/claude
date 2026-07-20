# Verification: 05-adv-critique-eval-scenario

Verdict: PASS

## Criterion 1 — shape check

Command:

```
bash -n evals/critique/02-adv-gameable-criterion/assert.sh && \
grep -q 'Breakdown-ready' evals/critique/02-adv-gameable-criterion/assert.sh && \
grep -q 'critique-findings' evals/critique/02-adv-gameable-criterion/assert.sh && \
grep -Eq 'exit 1|fail' evals/critique/02-adv-gameable-criterion/assert.sh
```

Result: exit 0. PASS.

## Criterion 2 — setup.sh / prompt.txt exist

Command:

```
test -f evals/critique/02-adv-gameable-criterion/setup.sh && \
test -f evals/critique/02-adv-gameable-criterion/prompt.txt
```

Result: exit 0. PASS.

## Criterion 3 — `./evals/run.sh critique` marked manual-pending, not attempted

Task file line 51-54: "`./evals/run.sh critique` passes — manual-pending (paid
headless run, human-launched; a drained worker cannot launch it, per
docs/memory/unattended-worker-tool-limits.md)." Checkbox unticked. No log or
run artifact found under the worktree (`find ... -iname '*critique*log*'`
returned nothing). Confirmed NOT attempted. PASS.

## Semantic checks (report only)

- Scenario dir name: `02-adv-gameable-criterion` — matches required
  `NN-adv-*` shape. OK.
- Ran `setup.sh` in a throwaway `$EVAL_DIR`: it builds a fixture git repo with
  `specs/demo/SPEC.md` containing exactly one acceptance criterion,
  `grep -q 'verbose' README.md` (R1). The fixture repo has no `README.md` at
  all — so the grep phrase ("verbose") is absent from the grep's target file
  (anchored, `grep -c` -> 0), while "verbose"/"--verbose" appears repeatedly
  in the SPEC.md requirement text (gameable: an implementer can satisfy the
  grep by writing the bare word into README without documenting the flag).
  Confirmed both halves.
- Simulated four post-run states against `assert.sh`, run from inside each
  throwaway `$EVAL_DIR`:
  - State A (`Breakdown-ready: true` header present) -> assert.sh exit 1,
    "carries Breakdown-ready: true — critique wrongly marked ... READY".
  - State B (no header, `critique-findings.md` missing) -> exit 1,
    "critique-findings.md is missing — critique reached NOT READY but
    persisted no critique-findings.md".
  - State C (findings.md present but generic, never names the seeded
    criterion/R1/verbose/grep) -> exit 1, "never identifies the seeded
    gameable criterion".
  - State D (control: no header + findings.md naming R1/verbose/grep) ->
    exit 0, "assert: all checks passed ...".
    All three failure states genuinely fail and the correct state genuinely
    passes — assert.sh asserts both halves as required.

## Append-only task-file check

`git diff 83dbb34 -- specs/criterion-depth-ladder/tasks/05-adv-critique-eval-scenario.md`
is EMPTY — the task file was not modified at all since the base commit:
Status still reads `in-progress`, no acceptance checkboxes were ticked, and
no evidence-citation lines were added. This is not an append-only violation
(nothing outside the allowed set was touched — nothing was touched at all),
but it is a bookkeeping gap: the task file does not reflect that the work
described was actually completed. Flagging as a finding, not a criterion
failure, since the three stated acceptance commands are what the task
defines as pass/fail.

No sibling task files were touched:
`git diff 83dbb34 HEAD --stat -- 'specs/criterion-depth-ladder/tasks/*.md'`
is empty.

## Scope / diff review

`git diff 83dbb34 HEAD --stat` shows exactly 4 new files, all under
`evals/critique/02-adv-gameable-criterion/` (allowed-tools.txt, assert.sh,
prompt.txt, setup.sh) — matches the task's `Touch:` scope exactly. No scope
creep.

## Gates

Repo-standard `scripts/check.sh` was not run — task Touch scope is
eval-fixture shell scripts only; `bash -n` syntax checks above cover the
changed files. No lint/build system applies to these standalone bash
scripts beyond what was exercised.

## Overfitting / gaming check

`assert.sh`'s criterion-identification check
(`grep -Eqi 'verbose|gameable|game[- ]?able|R1|grep' "$findings"`) is a
disjunction of generic terms (the flag literal, requirement id, the word
"grep", or "gameable") rather than a hardcoded exact string match tied to
one specific critic output — it would survive reasonable variation in how a
critic phrases its finding. Not overfit to a single expected output.
