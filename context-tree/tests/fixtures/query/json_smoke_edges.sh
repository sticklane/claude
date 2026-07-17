#!/usr/bin/env bash
# Acceptance fixture for task 07 criterion 6: each edge/reference/position query
# verb's `--json` output parses as JSON (piped through `jq`) with exit 0 and
# carries the asserted key for that verb.
# Run from the repo root:  bash context-tree/tests/fixtures/query/json_smoke_edges.sh
set -euo pipefail

crate_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
export PATH="$HOME/.cargo/bin:$PATH"

# Build the release binary the acceptance line invokes.
cargo build --release --manifest-path "$crate_dir/Cargo.toml" >/dev/null
ctx="$crate_dir/target/release/ctx"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/pkg"
cat >"$work/pkg/util.py" <<'PY'
def helper():
    return 1
PY
cat >"$work/app.py" <<'PY'
from pkg.util import helper


def solo():
    return helper()
PY

( cd "$work" && "$ctx" init >/dev/null )

# Each verb's exact --json invocation and the key jq must find (jq -e fails when
# the key is null/absent). Kept a case, not an associative array, so the script
# runs under macOS's stock bash 3.2.
for v in deps refs at; do
  case "$v" in
    deps) args="deps app.py --json";      key=".edges" ;;
    refs) args="refs helper --json";      key=".references" ;;
    at)   args="at app.py:5 --json";      key=".chain" ;;
  esac
  # shellcheck disable=SC2086
  out="$( cd "$work" && "$ctx" $args )"
  echo "$out" | jq -e "$key" >/dev/null
  echo "ok: ctx $args -> exit 0, has $key"
done

echo "json_smoke_edges: all verbs passed"
