#!/usr/bin/env bash
# Builds a fixture holding a README rather than a spec: the neighbouring
# request critique must decline, since human-facing prose is prose-review's
# charter (CLAUDE.md, Authoring conventions).
set -eu

cd "$EVAL_DIR"
git init -q

cat > README.md <<'DOC'
# Importer

This tool is a robust, best-in-class solution that leverages a powerful
pipeline to seamlessly handle your data needs. It's not just an importer,
it's a complete ingestion experience.

## Usage

Run it with a file. Click here for more.
DOC
git add -A && git commit -qm "docs: readme"
