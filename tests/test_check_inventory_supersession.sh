#!/usr/bin/env bash
# Supersession: a numbered fragment may re-declare a BASELINE classification,
# and only that direction. tests/test_check_inventory.sh is a frozen retain
# surface, so this coverage lands additively rather than by editing it.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SURFACE="$ROOT/scripts/inventory-core-surface.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

assert_success() {
  local name="$1"
  shift
  if "$@" >"$TMP/out" 2>&1; then
    pass=$((pass + 1))
    printf 'ok   - %s\n' "$name"
  else
    fail=$((fail + 1))
    printf 'FAIL - %s\n' "$name"
    sed 's/^/       /' "$TMP/out"
  fi
}

assert_failure() {
  local name="$1" expected="$2"
  shift 2
  if "$@" >"$TMP/out" 2>&1; then
    fail=$((fail + 1))
    printf 'FAIL - %s (unexpected success)\n' "$name"
  elif grep -q "$expected" "$TMP/out"; then
    pass=$((pass + 1))
    printf 'ok   - %s\n' "$name"
  else
    fail=$((fail + 1))
    printf 'FAIL - %s (missing diagnostic: %s)\n' "$name" "$expected"
    sed 's/^/       /' "$TMP/out"
  fi
}

new_fixture() { # new_fixture <name> — a tree whose demo skill has drifted
  local fixture="$TMP/$1"
  mkdir -p \
    "$fixture/.claude/skills/demo" \
    "$fixture/specs/toolkit-core-simplification/surface-inventory" \
    "$fixture/tests"
  printf '%s\n' 'demo skill' >"$fixture/.claude/skills/demo/SKILL.md"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'assert_demo_skill_exists() {' \
    '  test -f ".claude/skills/demo/SKILL.md"' \
    '}' \
    'assert_demo_skill_exists' >"$fixture/tests/test_demo.sh"
  chmod 755 "$fixture/tests/test_demo.sh"
  python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
anchor = hashlib.sha256(
    'test -f ".claude/skills/demo/SKILL.md"'.encode()
).hexdigest()


def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


manifest = {
    "$schema": "surface.schema.json",
    "git_blob_pin": 1,
    "manifest_type": "baseline",
    "schema_version": 2,
    "surfaces": [
        {
            "behavioral_tests": [f"tests/test_demo.sh#assert:{anchor}"],
            "content_sha256": digest(".claude/skills/demo/SKILL.md"),
            "dependents": [],
            "disposition": "retain",
            "identity": "skill:demo",
            "path": ".claude/skills/demo/SKILL.md",
            "rationale": "Fixture capability.",
            "replacement": None,
            "surface_type": "skill",
        },
        {
            "behavioral_tests": [f"tests/test_demo.sh#assert:{anchor}"],
            "content_sha256": digest("tests/test_demo.sh"),
            "dependents": ["skill:demo"],
            "disposition": "retain",
            "identity": "test:tests/test_demo.sh",
            "path": "tests/test_demo.sh",
            "rationale": "Fixture behavioral test.",
            "replacement": None,
            "surface_type": "test",
        },
    ],
}
payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
manifest["frozen_sha256"] = hashlib.sha256(payload).hexdigest()
(root / "specs/toolkit-core-simplification/BASELINE.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n"
)
PY
  # The drift the supersession has to answer for.
  printf '%s\n' 'demo skill, since revised' >"$fixture/.claude/skills/demo/SKILL.md"
  printf '%s' "$fixture"
}

write_fragment() { # write_fragment <fixture> <name> <identity> <disposition>
  python3 - "$@" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
name, identity, disposition = sys.argv[2], sys.argv[3], sys.argv[4]
anchor = hashlib.sha256(
    'test -f ".claude/skills/demo/SKILL.md"'.encode()
).hexdigest()
manifest = {
    "$schema": "../surface.schema.json",
    "fragment": name,
    "git_blob_pin": 1,
    "manifest_type": "fragment",
    "schema_version": 2,
    "surfaces": [
        {
            "behavioral_tests": [f"tests/test_demo.sh#assert:{anchor}"],
            "content_sha256": hashlib.sha256(
                (root / ".claude/skills/demo/SKILL.md").read_bytes()
            ).hexdigest(),
            "dependents": [],
            "disposition": disposition,
            "identity": identity,
            "path": ".claude/skills/demo/SKILL.md",
            "rationale": "Fixture supersession.",
            "replacement": None,
            "surface_type": "skill",
        }
    ],
}
payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
manifest["frozen_sha256"] = hashlib.sha256(payload).hexdigest()
target = (
    root / "specs/toolkit-core-simplification/surface-inventory" / f"{name}.json"
)
target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY
}

run_surface() {
  python3 "$SURFACE" \
    --root "$1" \
    --check "$1/specs/toolkit-core-simplification/BASELINE.json"
}

fixture="$(new_fixture drifted)"
assert_failure "a drifted retain surface fails without a superseding fragment" \
  "frozen content hash drift" run_surface "$fixture"

fixture="$(new_fixture superseded)"
write_fragment "$fixture" 01-repair skill:demo repair
assert_success "a fragment supersedes the baseline classification" \
  run_surface "$fixture"

fixture="$(new_fixture two-fragments)"
write_fragment "$fixture" 01-repair skill:demo repair
write_fragment "$fixture" 02-repair-again skill:demo repair
assert_failure "a fragment may not override another fragment" \
  "duplicate surface identity" run_surface "$fixture"

fixture="$(new_fixture same-manifest)"
python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

path = (
    pathlib.Path(sys.argv[1]) / "specs/toolkit-core-simplification/BASELINE.json"
)
data = json.loads(path.read_text())
data["surfaces"].append(json.loads(json.dumps(data["surfaces"][0])))
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure "one manifest may not declare an identity twice" \
  "duplicate surface identity" run_surface "$fixture"

printf '\n%s: %d passed, %d failed\n' \
  "$(basename "${BASH_SOURCE[0]}")" "$pass" "$fail"
[ "$fail" -eq 0 ]
