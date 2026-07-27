#!/usr/bin/env bash
# Builds a fixture whose only interesting artifact is an unreviewed spec, so
# the model's routing decision is the thing under test rather than its ability
# to find a target.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p specs/importer
cat > specs/importer/SPEC.md <<'SPEC'
# Importer: CSV ingest

## Problem

Users hand-enter rows that already exist in exported CSVs.

## Solution

A CLI that reads a CSV and writes rows to the store.

## Requirements

- R1: the importer accepts a file path and loads it.
- R2: bad rows are handled sensibly.
- R3: the import should be fast.
SPEC
git add -A && git commit -qm "spec: importer"
