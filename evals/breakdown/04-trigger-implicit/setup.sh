#!/usr/bin/env bash
# Builds a fixture holding a spec already marked ready for decomposition, so
# the only routing question is whether "split this into tasks" reaches
# breakdown.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/notes
cat > specs/notes/SPEC.md <<'SPEC'
Breakdown-ready: true

# Notes: capture and list

## Requirements

- R1: `src/add.sh` appends a note line to notes.txt.
- R2: `src/list.sh` prints notes.txt.
- R3: `src/search.sh` greps notes.txt for a term.
SPEC
git add -A && git commit -qm "spec: notes"
