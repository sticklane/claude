#!/usr/bin/env bash
# Acceptance fixture for task 06 criterion 6: each query verb's `--json` output
# parses as JSON (piped through `jq`) with exit 0 and carries the asserted key
# for that verb. Run from the repo root:  bash context-tree/tests/fixtures/query/json_smoke.sh
set -euo pipefail

crate_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
export PATH="$HOME/.cargo/bin:$PATH"

# Build the release binary the acceptance line invokes.
cargo build --release --manifest-path "$crate_dir/Cargo.toml" >/dev/null
ctx="$crate_dir/target/release/ctx"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cat >"$work/app.py" <<'PY'
def solo():
    """A solo function."""
    return 1


def caller():
    return solo()
PY

( cd "$work" && "$ctx" init >/dev/null )

# Each verb's exact --json invocation and the key jq must find (jq -e fails when
# the key is null/absent). Kept a case, not an associative array, so the script
# runs under macOS's stock bash 3.2.
for v in tree sig map; do
  case "$v" in
    tree) args="tree app.py --json"; key=".symbols" ;;
    sig)  args="sig solo --json";     key=".signature" ;;
    map)  args="map --json";          key=".symbols" ;;
  esac
  # shellcheck disable=SC2086
  out="$( cd "$work" && "$ctx" $args )"
  echo "$out" | jq -e "$key" >/dev/null
  echo "ok: ctx $args -> exit 0, has $key"
done

echo "json_smoke: all verbs passed"
