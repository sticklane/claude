#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR: a git repo whose only reorderable row is a
# single pending task, plus a `done` task the scanner excludes. Both changes
# the inline reply asks for are invalid, so the correct /prioritize run makes
# NO edit and NO commit (see this scenario's assert.sh).
#
# The prioritize scanner's dependency tree (_shared, runtimes/, and the
# workboard sibling skill) is provisioned centrally by run.sh — _shared and
# runtimes/ unconditionally, workboard via this scenario's skill-deps.txt —
# so this fixture only builds the specs/ tree under test.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/gamma/tasks

cat > specs/gamma/SPEC.md <<'EOF'
# Gamma: migration

## Goal

Migrate the store, then verify.
EOF

# A `done` task: outside the scanner's pending/blocked/deferred/draft scope,
# so its Ref never appears in the presented table. The reply names it anyway.
cat > specs/gamma/tasks/01-done-task.md <<'EOF'
# Migrate the store

Status: done
Priority: P2

## Goal

Move the data to the new schema.
EOF

# The one open, reorderable task. The reply asks to set it to P5 — outside the
# toolkit's P0-P3 range, so the target is invalid and must not be applied.
cat > specs/gamma/tasks/02-open-task.md <<'EOF'
# Verify the migration

Status: pending
Priority: P2

## Goal

Confirm every record survived the move.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: one open task plus a done task"
