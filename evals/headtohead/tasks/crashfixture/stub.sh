#!/usr/bin/env bash
# Stub session for the `crashfixture` selftest task. Stands in for an arm
# session that dies mid-run (crash / session-cap trip). It emits a PARTIAL
# cost transcript (root only, no child) and starts an edit, then exits
# non-zero WITHOUT finishing — modelling a run that accrued cost before dying.
# run.sh must still record a schema-valid row: pass:false, non-null partial
# usd/tokens (acceptance criterion 6). Exits 137 (a SIGKILL-style cap trip).
#
# Args (contract with run.sh): <workdir> <transcripts-dir> <arm> <seed>
set -eu

WORKDIR="$1"
TRANSCRIPTS="$2"

LIB="$(cd "$(dirname "$0")/../../lib" && pwd)"

# Partial cost accrued before the session died — root only, no child spawned.
"$LIB/stub-session.sh" emit-root "$TRANSCRIPTS" 0.03 300 2

# A half-finished edit: the marker word is never written, so even if the
# grader ran it would fail — but run.sh forces pass:false on the crash anyway.
printf 'partial\n' > "$WORKDIR/solution.txt"

echo "stub-cli: session hit the cap and was terminated mid-run" >&2
exit 137
