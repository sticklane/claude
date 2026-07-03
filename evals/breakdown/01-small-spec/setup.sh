#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a two-requirement spec and no open questions.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p src specs/demo

cat > src/greet.sh <<'EOF'
#!/usr/bin/env bash
echo "hello"
EOF
chmod +x src/greet.sh

cat > specs/demo/SPEC.md <<'EOF'
# Demo: greeting CLI pair

## Problem

`src/greet.sh` always prints a bare "hello" — it cannot greet a named
person — and the repo has no farewell counterpart at all.

## Solution

Two independent, dependency-free bash deliverables: extend the existing
greeting script in place, and add a sibling farewell script. They share
no files, so they can land in any order.

## Requirements

- R1: `src/greet.sh` accepts an optional name argument: `./src/greet.sh`
  prints `hello`, and `./src/greet.sh Ada` prints `hello Ada`.
- R2: a new executable `src/farewell.sh` prints `bye`, and
  `./src/farewell.sh Ada` prints `bye Ada`.

## Out of scope

- Any language other than bash; flags, help text, or i18n.

## Acceptance criteria

- [ ] `./src/greet.sh Ada` prints `hello Ada` (R1)
- [ ] `./src/greet.sh` still prints `hello` (R1)
- [ ] `test -x src/farewell.sh && ./src/farewell.sh Ada` prints `bye Ada` (R2)

## Open questions

(none)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo spec"
