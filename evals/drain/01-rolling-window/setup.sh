#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a two-task demo spec that opts the queue into a
# rolling window of 2 (Parallel-window: 2) and names both tasks on one
# Group: line, so /drain runs them concurrently and merges each on its own.
# The two tasks are dependency-free and Touch-disjoint (src/alpha.sh vs
# src/beta.sh), each a trivial bash-script deliverable a worker finishes in
# a couple of turns.
#
# Dual baton trigger: with Parallel-window: 2 the size-adaptive baton budget
# is max(2, 6-W) = max(2, 4) = 4 recorded verdicts, so this 2-task (2-verdict)
# run must complete within a SINGLE generation — no baton pass, no relaunch.
# assert.sh's check 5 enforces exactly that (no DRAIN-BATON.md ever written,
# clean lease/baton end state), exercising the dual trigger's threshold.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/demo/tasks

cat > specs/demo/SPEC.md <<'SPEC_EOF'
# Demo: two independent greeting scripts

Parallel-window: 2

## Problem

The repo has no `src/` scripts yet. We want two tiny, independent bash
deliverables that share no files, so a rolling-window drain can run them
concurrently and land each on its own merge.

## Solution

Two dependency-free, Touch-disjoint bash scripts: `src/alpha.sh` prints
`alpha`, `src/beta.sh` prints `beta`. They share no files and can land in
any order.

## Requirements

- R1: a new executable `src/alpha.sh` prints `alpha`.
- R2: a new executable `src/beta.sh` prints `beta`.

## Out of scope

- Any language other than bash; arguments, flags, or help text.

## Parallelization

- Group: 01, 02
SPEC_EOF

cat > specs/demo/tasks/01-alpha-script.md <<'T01_EOF'
Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: src/alpha.sh

# Task 01: alpha script

## Goal

Add a new executable `src/alpha.sh` that prints `alpha`.

## Steps

1. Create `src/alpha.sh` with a bash shebang that echoes `alpha`.
2. Make it executable (`chmod +x`).

## Acceptance

- [ ] `test -x src/alpha.sh && [ "$(./src/alpha.sh)" = alpha ]` exits 0 (R1)
T01_EOF

cat > specs/demo/tasks/02-beta-script.md <<'T02_EOF'
Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R2)
Touch: src/beta.sh

# Task 02: beta script

## Goal

Add a new executable `src/beta.sh` that prints `beta`.

## Steps

1. Create `src/beta.sh` with a bash shebang that echoes `beta`.
2. Make it executable (`chmod +x`).

## Acceptance

- [ ] `test -x src/beta.sh && [ "$(./src/beta.sh)" = beta ]` exits 0 (R2)
T02_EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo two-task rolling-window spec"
