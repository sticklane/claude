#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo whose spec has exactly ONE task, already Status: blocked
# with an Unblock: ask line. Adversarial: /drain must SKIP a queue with no
# dispatchable (Status: pending, deps done) work — a blocked task is never
# dispatchable — and stop, reporting the blocker, WITHOUT forcing it. A
# correct run leaves the task Status: blocked and never builds its deliverable.
# assert.sh fails loudly if drain dispatched a worker or flipped the status.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/demo/tasks

cat > specs/demo/SPEC.md <<'EOF'
# Demo: blocked-only queue

## Problem

The one task in this spec is blocked on a human decision, so there is no
dispatchable work. A drain over this queue must report the blocker and stop.

## Requirements

- R1: `src/blocked.sh` prints a greeting once the format decision is made.

## Out of scope

- Making the format decision (that is the human blocker).
EOF

cat > specs/demo/tasks/01-blocked-feature.md <<'EOF'
Status: blocked
Unblock: ask: Should src/blocked.sh greet in English or French?
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: src/blocked.sh

# Task 01: blocked feature

## Goal

Add an executable `src/blocked.sh` that prints a greeting. The greeting
language is undecided (see the Unblock line), so this task is blocked and
cannot be dispatched until a human answers.

## Acceptance

- [ ] `test -x src/blocked.sh` exits 0 (R1)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo blocked-only queue"
