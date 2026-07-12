#!/usr/bin/env bash
# Test double for the `agentprof` binary. Emulates
# `agentprof claude --since <t> --summary <path> -o /dev/null` by copying the
# fixture named in $FAKE_SUMMARY_SRC to the path given after --summary.
# With $FAKE_AGENTPROF_FAIL set, exits non-zero without writing (the
# adapter-error path). Ignores every other flag.
set -euo pipefail

if [ -n "${FAKE_AGENTPROF_FAIL:-}" ]; then
  echo "agentprof: simulated failure" >&2
  exit 1
fi

summary_path=""
prev=""
for arg in "$@"; do
  [ "$prev" = "--summary" ] && summary_path="$arg"
  prev="$arg"
done

if [ -n "$summary_path" ] && [ -n "${FAKE_SUMMARY_SRC:-}" ]; then
  cat "$FAKE_SUMMARY_SRC" >"$summary_path"
fi
exit 0
