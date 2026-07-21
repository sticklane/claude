#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a spec that carries UNRESOLVED "## Open questions".
# Adversarial: /breakdown must REFUSE to decompose an ambiguous spec — its
# step-1 gate says "If anything under Open questions is unresolved, stop and
# say so — decomposing an ambiguous spec multiplies the ambiguity." A correct
# run creates NO specs/demo/tasks/NN-*.md files and adds NO "## Parallelization"
# section to SPEC.md. assert.sh fails loudly if the skill DID decompose.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/demo

cat > specs/demo/SPEC.md <<'EOF'
# Demo: export command

## Problem

Users want to export their data, but the shape of the export is undecided.

## Solution

Add an `export` command to the CLI. The exact format and destination are
still under discussion — see Open questions.

## Requirements

- R1: a new `export` command writes the user's data somewhere in some format.

## Out of scope

- Import; any change to how data is stored internally.

## Acceptance criteria

- [ ] `./cli export` produces an export artifact (R1)

## Open questions

- Q1: what format should the export use — JSON, CSV, or both? This changes
  the entire serializer and the acceptance command.
- Q2: does export go to stdout or a file path argument? This changes the
  command's whole interface.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo spec with unresolved open questions"
