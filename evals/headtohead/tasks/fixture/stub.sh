#!/usr/bin/env bash
# Stub session for the `fixture` selftest task. Stands in for a real headless
# arm session: it does the "work" (writes solution.txt into the produced
# worktree so the hidden assert scores pass) and records deterministic cost via
# the shared stub-session helper — a ROOT session PLUS one spawned CHILD
# session, so the runner's summed `tokens` (1000 + 500 = 1500) exceeds the root
# transcript's own 1000. Exits 0: a clean, non-crashing run.
#
# Args (contract with run.sh): <workdir> <transcripts-dir> <arm> <seed>
set -eu

WORKDIR="$1"
TRANSCRIPTS="$2"
# arm ($3) and seed ($4) are accepted for contract parity; the stub is
# deterministic and ignores them, exactly as evals/stub-cli.sh ignores its
# tool allowlist.

LIB="$(cd "$(dirname "$0")/../../lib" && pwd)"

# Simulate the agent's edit.
printf 'fixed\n' > "$WORKDIR/solution.txt"

# Root session cost, then one spawned child session's cost.
"$LIB/stub-session.sh" emit-root  "$TRANSCRIPTS" 0.10 1000 5
"$LIB/stub-session.sh" emit-child "$TRANSCRIPTS" 1 0.05 500 2
