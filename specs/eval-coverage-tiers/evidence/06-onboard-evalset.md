# Verification: task 06 onboard evalset

Verdict: COMPLETE (deliverable verified sound; note on unticked checkboxes below)

## Criterion 1: dir count / naming

Command: `ls -d evals/onboard/0* | wc -l` → `2`
Command: `ls -d evals/onboard/02-adv-*` → `evals/onboard/02-adv-no-hooks`
PASS.

## Criterion 2: bash -n on each assert.sh

Ran individually (avoided for-loop per instructions):

- `bash -n evals/onboard/01-fresh-repo/assert.sh` → exit 0
- `bash -n evals/onboard/02-adv-no-hooks/assert.sh` → exit 0
  PASS.

## Criterion 3: `./evals/run.sh onboard`

NOT run (paid headless run). Task file's own acceptance line states
"manual-pending (paid headless run, human-launched, per
docs/memory/unattended-worker-tool-limits.md)" — legitimately manual-pending,
consistent with CLAUDE.md's rule that a task drained/parallelized must not
gate acceptance on a live paid run. Confirmed legitimate, not exercised.

## Structural bar (Tier A / R2)

`find evals/onboard -maxdepth 2 -type f`: each of `01-fresh-repo/` and
`02-adv-no-hooks/` contains `setup.sh`, `prompt.txt`, `assert.sh`,
`allowed-tools.txt`. PASS.

`02-adv-no-hooks` matches the `NN-adv-*` adversarial naming convention. PASS.

## Behavioral grader check (no paid run)

1. `mktemp -d /tmp/onboard-eval.XXXXXX` → `/tmp/onboard-eval.0Z0ww9`
2. `EVAL_DIR=/tmp/onboard-eval.0Z0ww9 bash evals/onboard/01-fresh-repo/setup.sh`
   → exit 0.
3. `cd /tmp/onboard-eval.0Z0ww9 && ./run-tests.sh` → prints `ok`, exit 0
   (fixture's own cheap+green check works).
4. Wrote simulated correct onboard output: CLAUDE.md (3 lines, mentions
   `run-tests.sh`), AGENTS.md (13 lines, mentions `run-tests.sh`),
   `.claude/settings.json` with non-empty `permissions.allow`, no `hooks` key.
   - `bash evals/onboard/01-fresh-repo/assert.sh` → exit 0 ("all checks
     passed (orientation split written + size-bounded, command captured,
     allowlist present)").
   - `bash evals/onboard/02-adv-no-hooks/assert.sh` → exit 0 ("all checks
     passed (onboarding artifact present; no hooks, no gate install)").
5. Added a `hooks.Stop` entry to `.claude/settings.json` (simulating a
   headless run that wired a Stop hook):
   - `bash evals/onboard/02-adv-no-hooks/assert.sh` → exit 1, stderr:
     `ASSERT FAIL: settings.json wired hooks a headless run must not
install: - Stop:bash scripts/check.sh`. Adversarial grader correctly
     catches a hook install. PASS.
6. Removed `CLAUDE.md` (settings.json restored to no-hooks state):
   - `bash evals/onboard/01-fresh-repo/assert.sh` → exit 1, stderr:
     `ASSERT FAIL: CLAUDE.md was not written`. Happy-path grader is not
     vacuous. PASS.
7. Cleaned up: `rm -rf /tmp/onboard-eval.0Z0ww9`.

Both graders exhibit correct red/green behavior against simulated
correct/violating trees — L2 (behavior) evidence, not just L0/L1
text/structure presence.

## Task-file append-only diff check

`git diff b35b573312f9d7a91c21c3ae21f773f949d16276 -- specs/eval-coverage-tiers/tasks/06-onboard-evalset.md`:

- Added a `<!-- PLAN (delete at close-out): ... -->` comment block above
  `## Goal` — allowed (plan comment block).
- Reflowed the line-continuation indentation of acceptance criterion 2's
  `for f in ...` command from 4-space to 2-space continuation indent —
  the criterion's literal text/command is unchanged (byte-identical modulo
  whitespace wrapping), not a semantic edit to criterion TEXT. Flagging as
  a minor, non-blocking formatting nit rather than a violation, since no
  wording or command content changed.
- Status line: unchanged, was already `in-progress` at the base commit
  (no flip occurred in this diff).
- No checkboxes were ticked in this diff — all three acceptance items
  remain `- [ ]` even though criteria 1, 2, and the behavioral quality bar
  all verified PASS in this session. This is a gap in the worker's own
  self-reporting (Status/checkboxes not advanced to reflect completed,
  verified work) rather than a correctness problem with the deliverable
  itself. No Goal/Steps/Touch/Budget or criterion wording was altered.

No other files under `specs/eval-coverage-tiers/tasks/` were touched
(diff was path-scoped to this task's own file only).

## Scope creep

`git status --short` shows only `specs/eval-coverage-tiers/tasks/06-onboard-evalset.md`
modified (uncommitted) plus the already-committed `evals/onboard/*` files
(commit `4c44dcb test: onboard evalset — artifact-only happy path +
adversarial no-hooks`). No files outside `Touch: evals/onboard/` were
changed. No scope creep found.

## Overfitting check

Graders use structural/semantic checks (python3 JSON parsing of
`permissions.allow` and `hooks`, line-count bounds, grep for `run-tests.sh`)
rather than string-matching exact model output; confirmed independently by
constructing my own simulated artifacts (not copied from any implementer
transcript) and observing correct pass/fail transitions. No special-casing
of exact test inputs observed.

## Per-criterion summary

1. ✓ `ls -d evals/onboard/0* | wc -l` → `2`; `02-adv-no-hooks` matches
   `evals/onboard/02-adv-*`. PASS.
2. ✓ `bash -n` on each `assert.sh` individually → both exit 0. PASS.
3. Confirmed legitimately manual-pending per task file's own acceptance
   text and CLAUDE.md's unattended-worker rule; not exercised (paid). N/A
   (correctly deferred).

## Criteria-adequacy

- Criterion 1 (dir count/naming): L1 (artifact-structure) — directly
  entails the requirement (exact count + name match), adequate.
- Criterion 2 (assert.sh syntax): L1 (artifact-structure, `bash -n`) —
  entails only that scripts parse, not that they grade correctly; adequate
  for its own narrow claim ("bash -n passes"), but standing alone would be
  INCOMPLETE evidence for "graders work." This gap is closed by the
  additional behavioral check this verification performed (steps 4-6
  above), which is L2 (behavior): simulated correct/violating trees drove
  observed exit-code transitions (0 → 1 → 0 → 1) matching expected grader
  intent. Combined, the onboard evalset's grading logic is L2-verified,
  not merely L0/L1.
- Criterion 3 (paid run, L3/end-to-end would require an actual model
  session): correctly scoped out as manual-pending per repo convention;
  not a gap in this task's own acceptance design.

## Overall verdict

COMPLETE — criteria 1 and 2 pass, the graders demonstrably behave
red/green correctly on both the happy-path and adversarial scenario, and
criterion 3 is legitimately manual-pending. The one finding (Status/
checkboxes not advanced despite the deliverable being sound, plus a minor
non-semantic line-rewrap in the task file) is a self-reporting hygiene gap,
not a deliverable defect, and does not change the verdict.
