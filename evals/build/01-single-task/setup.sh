#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with one standalone task file with runnable acceptance
# criteria — small enough for a full explore/plan/implement/verify/commit
# cycle to fit the runner's fixed 40-turn cap.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/demo/tasks

cat > specs/demo/SPEC.md <<'EOF'
# Demo: double script

## Problem

The repo has no `src/` scripts yet.

## Solution

One tiny, dependency-free bash deliverable: `src/double.sh` prints double
its integer argument.

## Requirements

- R1: a new executable `src/double.sh` prints double its integer argument
  (`./src/double.sh 21` prints `42`).

## Out of scope

- Any language other than bash; negative numbers, non-integer input,
  flags, or help text.
EOF

cat > specs/demo/tasks/01-double-script.md <<'EOF'
Status: pending
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirement R1)
Touch: src/double.sh

# Task 01: double script

## Goal

Add a new executable `src/double.sh` that takes one integer argument and
prints double its value.

## Steps

1. Create `src/double.sh` with a bash shebang.
2. Make it executable (`chmod +x`).

## Acceptance

- [ ] `test -x src/double.sh && [ "$(./src/double.sh 21)" = 42 ]` exits 0 (R1)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo double-script task"
