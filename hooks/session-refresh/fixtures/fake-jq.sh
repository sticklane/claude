#!/usr/bin/env bash
# Test double for `jq`, scoped to the single filter the session-refresh hook
# runs before its agentprof branch: `jq -r '.session_id // empty'` over the
# UserPromptSubmit payload on stdin. Placed (as `jq`) first on the restricted
# PATH of test.sh's test 5 so the hook's `command -v jq` guard resolves
# machine-independently — real jq may live outside /usr/bin:/bin — letting the
# hook reach its agentprof-binary-absent path instead of short-circuiting at
# the jq guard. Uses only bash builtins so it needs no PATH beyond itself.
# Only the .session_id filter is emulated; any other filter exits nonzero.
set -u

filter=""
for arg in "$@"; do
  case "$arg" in
  -r) ;;
  .session_id*) filter="session_id" ;;
  esac
done

[ "$filter" = "session_id" ] || exit 1

# Slurp all of stdin with a builtin (read returns nonzero at EOF; ignore it).
IFS= read -r -d '' payload || true

# Emulate `.session_id // empty`: print the value if present, nothing if not.
if [[ "$payload" =~ \"session_id\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
  printf '%s\n' "${BASH_REMATCH[1]}"
fi
exit 0
