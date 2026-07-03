#!/usr/bin/env bash
# No-model stand-in for a headless runner, used by runner-selftest.sh.
# Implements the RUNNER_CMD contract: invoked inside the fixture dir
# with the scenario prompt as its final argument. Writes the prompt to
# stub-output.txt in the current directory so the scenario's assert.sh
# can grade the run without any model access. run.sh exports the
# scenario allowlist as ALLOWED_TOOLS; this stub ignores it.
set -eu

[ "$#" -ge 1 ] || { echo "stub-cli: expected the prompt as final argument" >&2; exit 1; }
printf '%s\n' "${*: -1}" > stub-output.txt
