#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a small, unambiguous two-requirement spec — clear
# enough that a competent critic should reach READY, giving critique's
# only documented artifact mutation (the Breakdown-ready: true header) a
# deterministic-ish outcome to check.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/demo

cat > specs/demo/SPEC.md <<'EOF'
# Demo: greeting CLI pair

## Problem

The repo has no `src/` scripts yet, and needs two independent greeting
utilities.

## Solution

Two independent, dependency-free bash deliverables that share no files, so
they can land in any order.

## Requirements

- R1: a new executable `src/hello.sh` prints `hello`.
- R2: a new executable `src/goodbye.sh` prints `goodbye`.

## Out of scope

- Any language other than bash; arguments, flags, help text, or i18n.

## Acceptance criteria

- [ ] `test -x src/hello.sh && [ "$(./src/hello.sh)" = hello ]` (R1)
- [ ] `test -x src/goodbye.sh && [ "$(./src/goodbye.sh)" = goodbye ]` (R2)

## Open questions

(none)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo clean spec"
