# Task 06: /evals drain scenario for the window semantics

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirement R7)
Touch: evals/drain/

## Goal

A new eval scenario, `evals/drain/01-rolling-window/` (setup.sh,
prompt.txt, assert.sh, allowed-tools.txt — the same four files as the
reference `evals/breakdown/01-small-spec/` scenario), exercises the
rewritten `/drain` skill against a small fixture spec that carries a
`Parallel-window:` header and a `Group:` line over 2–3 trivial,
Touch-disjoint bash-script tasks, and asserts (mechanically, on the
resulting git history and task-file statuses) that more than one task
landed without a strict all-in-one-commit barrier. `bash evals/run.sh
drain` passes. There is currently no `evals/drain/` directory at all —
this task creates the scenario, it does not "update" a pre-existing one
(the SPEC's ship-gates line assumed one existed; it doesn't, per a repo
check during this spec's breakdown).

## Touch

In scope: the new `evals/drain/01-rolling-window/` directory and its
four files only.

Out of scope: `evals/run.sh` itself (the runner already discovers any
`evals/<skill>/NN-*/` directory without code changes — confirm this
before assuming a runner edit is needed) and `evals/breakdown/`.

## Steps

1. Read `evals/run.sh` and the reference scenario documented verbatim in
   `.claude/skills/evals/reference.md` (setup.sh / prompt.txt / assert.sh
   / allowed-tools.txt for `evals/breakdown/01-small-spec/`) to match
   conventions.
2. Write `setup.sh`: a tiny git repo fixture with a
   `specs/demo/SPEC.md` carrying a `Parallel-window: 2` (or `3`) header
   and a `## Parallelization` section with one `- Group:` line naming
   two-to-three pending, dependency-free, Touch-disjoint task files
   under `specs/demo/tasks/` (each a trivial bash-script edit, sized so
   a real worker session finishes in a couple of turns — keep the eval's
   wall-clock cost low).
3. Write `prompt.txt`: `/drain specs/demo`.
4. Write `allowed-tools.txt` including `Task` (drain fans out to
   `implementation-worker` agents, which the runner provisions).
5. Write `assert.sh` (CWD is `$EVAL_DIR`, exit 0 = pass): check that
   every task file in `specs/demo/tasks/` ended `Status: done`, that the
   git log shows more than one merge commit (proving the tasks didn't
   land in one all-in-one-commit barrier flip), and that no commit's
   changed paths violated its task's `Touch:` list. Keep failure output
   under ~10 lines, one `ASSERT FAIL:` per broken check, per the
   reference scenario's convention.
6. Run `bash evals/run.sh drain` locally and iterate until it passes —
   this scenario invokes a real headless `claude` session per
   `evals/run.sh`'s design, so expect it to take real wall-clock time;
   budget your turns accordingly and don't loop indefinitely on a flaky
   run — three consecutive failures with no clear fixable cause is this
   task's stop line, reported as evidence rather than ground away at.

## Acceptance

- [x] `bash evals/run.sh drain` → exit 0, one pass line printed for
      `drain/01-rolling-window` — **OR**, if three consecutive runs fail
      with no clear fixable cause (Step 6's stop line): mark this
      criterion MANUAL-PENDING in this task file with the failure
      evidence (the runner's kept fixture path and its last output),
      rather than looping further or leaving the task file silent. The
      other two criteria below still apply regardless.
      Evidence: `bash evals/run.sh drain` → `PASS  drain/01-rolling-window`,
      `1/1 scenarios passed`, exit 0 (verifier PASS; re-run green after the
      pre-commit assert fix — see evidence/06-drain-eval-scenario.md and
      evidence/06-run.log). Passed on both attempts; MANUAL-PENDING path
      not needed.
- [x] `ls evals/drain/01-rolling-window/` → contains `setup.sh`,
      `prompt.txt`, `assert.sh`, `allowed-tools.txt`
      Evidence: `ls` → `allowed-tools.txt assert.sh prompt.txt setup.sh`.
- [x] `grep -q 'Parallel-window' evals/drain/01-rolling-window/setup.sh`
      → match
      Evidence: grep exit 0 (setup.sh writes `Parallel-window: 2` into
      specs/demo/SPEC.md).
