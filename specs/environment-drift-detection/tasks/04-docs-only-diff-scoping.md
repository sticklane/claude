# Task 04: docs-only diff detection in the local Stop-hook gate

Status: in-progress
Depends on: 01
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (requirement R4)
Touch: templates/stop-gate.sh, bin/install-gates, tests/test_hook_templates.sh, tests/test_install_gates.sh

## Goal

`templates/stop-gate.sh` (and `bin/install-gates`'s generation of it)
detects a docs-only diff — every changed file since the last commit (or
`HEAD`) matches CLAUDE.md's existing `paths-ignore` glob set (`**.md`,
`docs/**`, `specs/**`, `.claude/**`) — and skips or narrows
`scripts/check.sh` accordingly, applying the same convention CLAUDE.md
already states for push-triggered CI to the LOCAL Stop-hook gate. A
non-docs-only diff (any file outside those globs changed) must still run
`scripts/check.sh` in full — this requirement is a scoping optimization,
never a blanket skip.

## Touch

This task depends on Task 01 because both tasks edit `bin/install-gates` —
rebase onto Task 01's merged change before starting so there is no merge
collision; do not start this task until Task 01's branch has merged. Do not
touch `templates/check.sh.tmpl`'s stage-ordering content beyond what Task
01 already landed (Task 05 separately owns any change to check.sh.tmpl's
failure-reporting order).

## Steps

1. Read `templates/stop-gate.sh` in full (short, ~55 lines) and
   `tests/test_hook_templates.sh`'s existing stop-gate test cases (green
   check, failing check, exit-127 case) to learn the test harness's fixture
   shape (how it stages a fake repo, what hook JSON it feeds on stdin).
2. Read `bin/install-gates`'s generation of `stop-gate.sh` (the part of the
   script that copies/renders `templates/stop-gate.sh` into an installed
   repo — grep for `stop-gate` or `STOP_GATE` in `bin/install-gates` for the
   exact spot) to understand whether any per-repo templating already
   happens there, or the file is installed verbatim.
3. Write a failing test first in `tests/test_hook_templates.sh`: a fixture
   repo whose only diff since the last commit is a `.md` file, asserting
   the Stop hook exits 0 WITHOUT running the full `scripts/check.sh` (e.g.
   by pointing `scripts/check.sh` at a script that would fail if invoked,
   or a marker file it would create, and asserting it wasn't created/run).
4. Write a second failing test: a fixture repo whose diff includes a
   non-docs file (e.g. a `.js` or `.py` change alongside a `.md` change),
   asserting the full `scripts/check.sh` still runs (its marker/side effect
   IS observed) — this is the anti-regression case for "must not become a
   blanket skip."
5. Implement the docs-only diff detection in `templates/stop-gate.sh`:
   compute the changed-file set since the last commit (or `HEAD`), test
   every path against the glob set `**.md`, `docs/**`, `specs/**`,
   `.claude/**`, and skip or narrow the `scripts/check.sh` invocation when
   all changed files match. The literal phrase `docs-only diff` must appear
   in `templates/stop-gate.sh` (or `bin/install-gates`, whichever actually
   hosts the detection logic).
6. If `bin/install-gates` needs any change to correctly generate/wire the
   updated `stop-gate.sh` (e.g. if it currently patches placeholders into
   the template), update it and extend `tests/test_install_gates.sh`
   accordingly; otherwise leave `bin/install-gates` untouched beyond what
   Task 01 already landed.
7. Run both test files green; run this repo's own check command before
   committing.

## Acceptance

- [ ] `grep -c "docs-only diff" templates/stop-gate.sh bin/install-gates | awk -F: '{sum+=$2} END {print sum}'` → greater than 0
- [ ] `bash tests/test_hook_templates.sh` exits 0, including the new
      docs-only-skip and non-docs-still-runs cases
- [ ] `bash tests/test_install_gates.sh` exits 0 (no regression from Task 01)
- [ ] MANUAL: trigger the updated Stop hook on a repo with gates installed
      via a docs-only edit (e.g. a one-line HUMAN.md change) and confirm
      the full `scripts/check.sh` run is skipped or narrowed, not run in
      full
- [ ] MANUAL: trigger the updated Stop hook on the same repo via a
      product-code edit and confirm `scripts/check.sh` still runs in full
