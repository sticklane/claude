# Task 01: build/dist prerequisite stage in install-gates + check.sh.tmpl

Status: in-progress
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirement R1)
Touch: bin/install-gates, templates/check.sh.tmpl, tests/test_install_gates.sh

<!-- PLAN (build)
- tests first (tests/test_install_gates.sh): (1) node .scripts.build → build
  stage before lint/tests; (2) .claude/build-prereq marker (python fixture) →
  literal cmd as build stage before other stages; (3) neither signal → no
  build stage. Confirm 1+2 red.
- impl (bin/install-gates): unified post-detection block after the
  detect_* dispatch (~line 334). BUILD_CMD from node .scripts.build (recompute
  pm) else .claude/build-prereq head -1; prepend `run_stage "build" $cmd` to
  CHECK_STAGES + STAGE_DESC. Comment carries literal "build/dist prerequisite".
- template unchanged (@STAGES@ already ordered). No tier change: generic repos
  still get no check.sh (marker only visible where check.sh is rendered).
- gates: bash tests/test_install_gates.sh green; bash scripts/check.sh.
-->

## Goal

`bin/install-gates` detects a repo-declared build/install prerequisite stage
and renders it as a `run_stage` line in the generated `scripts/check.sh`,
running BEFORE the existing lint/typecheck/test stages. Two detection paths,
per the decision recorded in SPEC.md's R1 "Decision" paragraph:

1. **Node stack**: if `package.json` has a `.scripts.build` entry, add a
   `run_stage "build" $pm run build` line (mirroring how `detect_node`
   already reads `.scripts.check`/`.scripts.typecheck`/`.scripts.lint`).
2. **Any other detected stack** (python, generic): an explicit opt-in marker
   file at the repo root, `.claude/build-prereq`, whose single-line contents
   are the literal shell command to run as the build stage. Presence of the
   file is the opt-in signal; absence adds no build stage.

When neither signal is present, `scripts/check.sh` is generated exactly as
today (no behavior change for the vast majority of repos this toolkit
installs into).

## Touch

Read (don't modify) `templates/check.sh.tmpl` if unclear — its `@STAGES@`
placeholder and `run_stage` helper already support an arbitrary ordered list
of stages; this task supplies an additional stage line ahead of the existing
ones, it should not need to change the template's shape itself unless the
ordering mechanism requires it. Do not touch `templates/stop-gate.sh` — that
belongs to Task 04 (R4), which depends on this task landing first because it
also edits `bin/install-gates`.

## Steps

1. Read `bin/install-gates`'s detection section (`detect_python`,
   `detect_node`, the `add_check_stage` helper around lines 115-270) and
   `tests/test_install_gates.sh` to understand the existing test harness
   shape (fixture repos, assertion helpers).
2. Write a failing test first in `tests/test_install_gates.sh`: a scratch
   Node fixture repo with a `package.json` `.scripts.build` entry, asserting
   the generated `scripts/check.sh` contains a `run_stage "build"` line
   ordered before the lint/typecheck/test stage lines. Confirm it fails
   (the stage doesn't exist yet).
3. Add a second failing test: a scratch repo (any stack) with a root
   `.claude/build-prereq` file containing a literal command, asserting the
   generated `check.sh` runs that literal command as a `run_stage` line
   before the other stages.
4. Add a third test: a repo with neither signal — assert no build stage
   line appears (regression guard against false positives).
5. Implement the two detection paths in `bin/install-gates`, using
   `add_check_stage` (or equivalent) to prepend the build stage ahead of
   whatever stages `detect_python`/`detect_node`/generic detection already
   add. The literal phrase `build/dist prerequisite` must appear somewhere
   in `bin/install-gates` (a comment near the new detection code is
   sufficient) — this is this repo's own acceptance-grep anchor.
6. Run the tests; make them green. Run the full test suite
   (`bash tests/test_install_gates.sh` at minimum) to confirm no
   regression in existing detection paths.
7. Run `bash scripts/check.sh` (this repo's own gate) if present, else the
   repo's lint/test commands, before committing.

## Acceptance

- [ ] `grep -c "build/dist prerequisite" bin/install-gates` → greater than 0
- [ ] `bash tests/test_install_gates.sh` exits 0, including the three new
      cases (Node `.scripts.build`, `.claude/build-prereq` marker, neither
      signal present)
- [ ] MANUAL: run `bin/install-gates --dry-run <scratch-repo>` (or install
      for real into a scratch git repo) with a Node `.scripts.build` entry
      and confirm the rendered `scripts/check.sh` runs the build stage
      before lint/typecheck/test
- [ ] MANUAL: repeat with a `.claude/build-prereq` marker file and confirm
      its literal command runs as the build stage
- [ ] MANUAL: repeat with neither signal and confirm no build stage is added
