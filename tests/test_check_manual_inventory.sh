#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/scripts" "$TMP/tests/inventory"
cp "$ROOT/scripts/check.sh" "$TMP/scripts/check.sh"
chmod 755 "$TMP/scripts/check.sh"
printf '%s\n' '#!/usr/bin/env bash' 'exit 97' >"$TMP/tests/test_networked.sh"
chmod 755 "$TMP/tests/test_networked.sh"

python3 - "$TMP/tests/inventory/core.json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text(
    json.dumps(
        {
            "fragment": "core",
            "schema_version": 1,
            "tests": [
                {
                    "disposition": "manual",
                    "path": "tests/test_networked.sh",
                    "reason": "Requires an explicit networked smoke run.",
                    "runner": "bash",
                    "serial": False,
                }
            ],
        }
    )
)
PY

output="$(cd "$TMP" && bash scripts/check.sh)" || {
  printf '%s\n' "$output"
  exit 1
}
grep -q \
  'tests/test_networked.sh — Requires an explicit networked smoke run.' \
  <<<"$output"

python3 - "$TMP/tests/inventory/core.json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
del data["tests"][0]["reason"]
path.write_text(json.dumps(data))
PY

if (cd "$TMP" && bash scripts/check.sh) >"$TMP/out" 2>&1; then
  echo "manual inventory without a reason unexpectedly passed" >&2
  exit 1
fi
grep -q 'manual requires reason' "$TMP/out"

echo "CHECK MANUAL INVENTORY OK"
