#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR: a git repo with a specs/ tree of open,
# reorderable work across two specs, plus the prioritize scanner's sibling
# script dependencies. The /prioritize run must rewrite the two named
# Priority headers per the inline reply and commit; the third task is a
# distractor that must keep its P2.
#
# run.sh provisions ONLY the skill under test, but prioritize_scan.py imports
# .claude/skills/_shared/headers.py and loads .claude/skills/workboard/
# workboard.py, which itself imports runtimes/parse_headless.py. So this
# fixture provisions that dependency tree from the source checkout (reached
# via BASH_SOURCE, since run.sh invokes setup.sh by its in-repo path).
set -eu

SRC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$EVAL_DIR"
git init -q

mkdir -p .claude/skills
cp -R "$SRC_ROOT/.claude/skills/_shared" .claude/skills/_shared
cp -R "$SRC_ROOT/.claude/skills/workboard" .claude/skills/workboard
cp -R "$SRC_ROOT/runtimes" runtimes

mkdir -p specs/alpha/tasks specs/beta/tasks

cat > specs/alpha/SPEC.md <<'EOF'
# Alpha: input pipeline

## Goal

Parse and format the incoming feed.
EOF

cat > specs/alpha/tasks/01-parser.md <<'EOF'
# Parse the feed

Status: pending
Priority: P2

## Goal

Read the raw feed and emit structured records.
EOF

cat > specs/alpha/tasks/02-formatter.md <<'EOF'
# Format the records

Status: pending
Priority: P2

## Goal

Render structured records as the output table.
EOF

cat > specs/beta/SPEC.md <<'EOF'
# Beta: loader

## Goal

Load the formatted output into the store.
EOF

cat > specs/beta/tasks/01-loader.md <<'EOF'
# Load into the store

Status: blocked
Priority: P1

## Goal

Persist the formatted output.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: open tasks across two specs"
