#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a spec whose single acceptance criterion is
# anchored-but-GAMEABLE. The grep phrase (`verbose`) is absent from the
# fixture, so the criterion satisfies the mechanical anchored-criteria check
# (grep -c -> 0); yet it is trivially satisfiable by its own requirement's
# literal — an implementer can write the word `verbose` into README.md
# without ever documenting the flag's behavior, and the grep passes. A
# competent critic (task 03's acceptance-criteria attack checklist) should
# reach NOT READY and name this criterion in critique-findings.md.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/demo

cat > specs/demo/SPEC.md <<'EOF'
# Demo: document the --verbose flag

## Problem

The CLI recently gained a `--verbose` flag, but the README never explains
what it does or when to use it.

## Solution

Add a documentation entry for the flag to `README.md` so a new user learns
what `--verbose` turns on and its trade-offs.

## Requirements

- R1: `README.md` documents the `--verbose` flag — what it enables and the
  performance cost of using it.

## Out of scope

- Any change to the flag's runtime behavior; other undocumented flags.

## Acceptance criteria

- [ ] `grep -q 'verbose' README.md` (R1)

## Open questions

(none)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo gameable-criterion spec"
