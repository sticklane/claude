#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SURFACE="$ROOT/scripts/inventory-core-surface.py"
CHECK="$ROOT/scripts/check.sh"
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

new_surface_fixture() {
  local name="$1" fixture="$TMP/$1"
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

def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()

assertion = 'test -f ".claude/skills/demo/SKILL.md"'
anchor = hashlib.sha256(assertion.encode()).hexdigest()
surfaces = [
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
]
manifest = {
    "$schema": "surface.schema.json",
    "git_blob_pin": 1,
    "manifest_type": "baseline",
    "schema_version": 2,
    "surfaces": surfaces,
}
payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
manifest["frozen_sha256"] = hashlib.sha256(payload).hexdigest()
target = root / "specs/toolkit-core-simplification/BASELINE.json"
target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY
  printf '%s' "$fixture"
}

run_surface() {
  local fixture="$1"
  python3 "$SURFACE" \
    --root "$fixture" \
    --check "$fixture/specs/toolkit-core-simplification/BASELINE.json"
}

mark_demo_measure_before_decision() {
  local fixture="$1"
  python3 - "$fixture/specs/toolkit-core-simplification/BASELINE.json" <<'PY'
import hashlib
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
surface = next(
    row for row in data["surfaces"] if row["identity"] == "skill:demo"
)
surface["disposition"] = "measure-before-decision"
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
}

assert_success \
  "real tree surface baseline passes" \
  python3 "$SURFACE" \
  --root "$ROOT" \
  --check "$ROOT/specs/toolkit-core-simplification/BASELINE.json"

fixture="$(new_surface_fixture surface-green)"
assert_success "complete surface baseline passes" run_surface "$fixture"

fixture="$(new_surface_fixture surface-unclassified)"
mkdir -p "$fixture/.claude/rules"
printf '%s\n' 'new rule' >"$fixture/.claude/rules/new.md"
assert_failure "unclassified surface fails" "unclassified surface" run_surface "$fixture"

fixture="$(new_surface_fixture surface-missing)"
rm "$fixture/.claude/skills/demo/SKILL.md"
assert_failure "missing retained surface fails" "missing non-retired surface" run_surface "$fixture"

fixture="$(new_surface_fixture surface-evidence)"
rm "$fixture/tests/test_demo.sh"
assert_failure "missing retained test evidence fails" "behavioral test missing" run_surface "$fixture"

fixture="$(new_surface_fixture surface-hash)"
printf '%s\n' 'changed demo skill' >"$fixture/.claude/skills/demo/SKILL.md"
assert_failure "altered frozen hash fails" "frozen content hash drift" run_surface "$fixture"

fixture="$(new_surface_fixture surface-measure-edit)"
mark_demo_measure_before_decision "$fixture"
printf '%s\n' 'changed measured demo skill' >"$fixture/.claude/skills/demo/SKILL.md"
assert_success \
  "measure-before-decision permits content edits" \
  run_surface "$fixture"
rm "$fixture/.claude/skills/demo/SKILL.md"
assert_failure \
  "measure-before-decision still rejects deletion" \
  "missing non-retired surface" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-measure-move)"
mark_demo_measure_before_decision "$fixture"
mv "$fixture/.claude/skills/demo" "$fixture/.claude/skills/relocated-demo"
assert_failure \
  "measure-before-decision still rejects relocation" \
  "missing non-retired surface" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-duplicate)"
python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
baseline = json.loads(
    (root / "specs/toolkit-core-simplification/BASELINE.json").read_text()
)
fragment = {
    "$schema": "../surface.schema.json",
    "fragment": "duplicate",
    "git_blob_pin": 1,
    "manifest_type": "fragment",
    "schema_version": 2,
    "surfaces": [baseline["surfaces"][0]],
}
payload = json.dumps(fragment, sort_keys=True, separators=(",", ":")).encode()
fragment["frozen_sha256"] = hashlib.sha256(payload).hexdigest()
target = (
    root
    / "specs/toolkit-core-simplification/surface-inventory/duplicate.json"
)
target.write_text(json.dumps(fragment, indent=2, sort_keys=True) + "\n")
PY
assert_failure "duplicate additive identity fails" "duplicate surface identity" run_surface "$fixture"

fixture="$(new_surface_fixture surface-unrelated-evidence)"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'assert_unrelated_behavior() {' \
  '  test -n "unrelated"' \
  '}' \
  'assert_unrelated_behavior' >"$fixture/tests/test_unrelated.sh"
chmod 755 "$fixture/tests/test_unrelated.sh"
python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
path = root / "specs/toolkit-core-simplification/BASELINE.json"
data = json.loads(path.read_text())
statement = 'test -n "unrelated"'
anchor = hashlib.sha256(statement.encode()).hexdigest()
data["surfaces"][0]["behavioral_tests"] = [
    f"tests/test_unrelated.sh#assert:{anchor}"
]
data["surfaces"].append(
    {
        "behavioral_tests": [
            f"tests/test_unrelated.sh#assert:{anchor}"
        ],
        "content_sha256": hashlib.sha256(
            (root / "tests/test_unrelated.sh").read_bytes()
        ).hexdigest(),
        "dependents": [],
        "disposition": "retain",
        "identity": "test:tests/test_unrelated.sh",
        "path": "tests/test_unrelated.sh",
        "rationale": "Unrelated fixture test.",
        "replacement": None,
        "surface_type": "test",
    }
)
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure \
  "unrelated classified evidence fails" \
  "does not reference surface" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-python-anchor-scope)"
printf '%s\n' \
  'from pathlib import Path' \
  'def test_linked_case():' \
  '    assert Path(".claude/skills/demo/SKILL.md").is_file()' \
  'def test_unrelated_case():' \
  '    assert True' >"$fixture/tests/test_linkage.py"
python3 - "$fixture" <<'PY'
import ast
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
path = root / "specs/toolkit-core-simplification/BASELINE.json"
data = json.loads(path.read_text())
data["surfaces"][0]["behavioral_tests"] = [
    "tests/test_linkage.py::test_unrelated_case"
]
data["surfaces"].append(
    {
        "behavioral_tests": ["tests/test_linkage.py::test_linked_case"],
        "content_sha256": hashlib.sha256(
            (root / "tests/test_linkage.py").read_bytes()
        ).hexdigest(),
        "dependents": [],
        "disposition": "retain",
        "identity": "test:tests/test_linkage.py",
        "path": "tests/test_linkage.py",
        "rationale": "Python anchor scope fixture.",
        "replacement": None,
        "surface_type": "test",
    }
)
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure \
  "Python evidence is scoped to named test body" \
  "does not reference surface" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-shell-comment-bypass)"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  '# .claude/skills/demo/SKILL.md' \
  'test -n "unrelated"' >"$fixture/tests/test_comment.sh"
chmod 755 "$fixture/tests/test_comment.sh"
python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
path = root / "specs/toolkit-core-simplification/BASELINE.json"
data = json.loads(path.read_text())
statement = 'test -n "unrelated"'
anchor = hashlib.sha256(statement.encode()).hexdigest()
data["surfaces"][0]["behavioral_tests"] = [
    f"tests/test_comment.sh#assert:{anchor}"
]
data["surfaces"].append(
    {
        "behavioral_tests": [f"tests/test_comment.sh#assert:{anchor}"],
        "content_sha256": hashlib.sha256(
            (root / "tests/test_comment.sh").read_bytes()
        ).hexdigest(),
        "dependents": [],
        "disposition": "retain",
        "identity": "test:tests/test_comment.sh",
        "path": "tests/test_comment.sh",
        "rationale": "Shell comment bypass fixture.",
        "replacement": None,
        "surface_type": "test",
    }
)
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure \
  "shell comment cannot link unrelated assertion" \
  "does not reference surface" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-shell-statement-scope)"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'test -f ".claude/skills/demo/SKILL.md"' \
  'test -n "unrelated"' >"$fixture/tests/test_statements.sh"
chmod 755 "$fixture/tests/test_statements.sh"
python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
path = root / "specs/toolkit-core-simplification/BASELINE.json"
data = json.loads(path.read_text())
statement = 'test -n "unrelated"'
anchor = hashlib.sha256(statement.encode()).hexdigest()
data["surfaces"][0]["behavioral_tests"] = [
    f"tests/test_statements.sh#assert:{anchor}"
]
data["surfaces"].append(
    {
        "behavioral_tests": [f"tests/test_statements.sh#assert:{anchor}"],
        "content_sha256": hashlib.sha256(
            (root / "tests/test_statements.sh").read_bytes()
        ).hexdigest(),
        "dependents": [],
        "disposition": "retain",
        "identity": "test:tests/test_statements.sh",
        "path": "tests/test_statements.sh",
        "rationale": "Shell statement scope fixture.",
        "replacement": None,
        "surface_type": "test",
    }
)
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure \
  "shell evidence is scoped to anchored statement" \
  "does not reference surface" \
  run_surface "$fixture"

commit_fixture() {
  local fixture="$1"
  git -C "$fixture" init -q
  git -C "$fixture" config user.email fixture@example.invalid
  git -C "$fixture" config user.name "Inventory Fixture"
  git -C "$fixture" config core.hooksPath /dev/null
  git -C "$fixture" add .
  git -C "$fixture" commit -qm "add frozen inventory"
}

fixture="$(new_surface_fixture surface-git-edit)"
commit_fixture "$fixture"
python3 - "$fixture/specs/toolkit-core-simplification/BASELINE.json" <<'PY'
import hashlib
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
data["surfaces"][0]["rationale"] = "Recomputed but no longer first Git blob."
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure \
  "Git-pinned manifest rejects edit with recomputed digest" \
  "differs from first Git blob" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-shallow-history)"
commit_fixture "$fixture"
python3 - "$fixture/specs/toolkit-core-simplification/BASELINE.json" <<'PY'
import hashlib
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
data["surfaces"][0]["rationale"] = "Newest shallow commit rewrites history."
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
git -C "$fixture" add specs/toolkit-core-simplification/BASELINE.json
git -C "$fixture" commit -qm "rewrite frozen inventory"
shallow="$TMP/surface-shallow-clone"
git clone -q --depth 1 "file://$fixture" "$shallow"
assert_failure \
  "shallow history cannot establish manifest trust" \
  "deepen Git history" \
  run_surface "$shallow"

fixture="$(new_surface_fixture surface-git-fragment-delete)"
python3 - "$fixture" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
baseline_path = root / "specs/toolkit-core-simplification/BASELINE.json"
baseline = json.loads(baseline_path.read_text())
skill = next(
    row for row in baseline["surfaces"] if row["identity"] == "skill:demo"
)
baseline["surfaces"] = [
    row for row in baseline["surfaces"] if row["identity"] != "skill:demo"
]
payload = {
    key: value for key, value in baseline.items() if key != "frozen_sha256"
}
baseline["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
baseline_path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")

fragment = {
    "$schema": "../surface.schema.json",
    "fragment": "demo",
    "git_blob_pin": 1,
    "manifest_type": "fragment",
    "schema_version": 2,
    "surfaces": [skill],
}
payload = json.dumps(fragment, sort_keys=True, separators=(",", ":")).encode()
fragment["frozen_sha256"] = hashlib.sha256(payload).hexdigest()
fragment_path = (
    root / "specs/toolkit-core-simplification/surface-inventory/demo.json"
)
fragment_path.write_text(json.dumps(fragment, indent=2, sort_keys=True) + "\n")
PY
commit_fixture "$fixture"
rm \
  "$fixture/.claude/skills/demo/SKILL.md" \
  "$fixture/specs/toolkit-core-simplification/surface-inventory/demo.json"
assert_failure \
  "deleting retained surface and its fragment fails" \
  "historical fragment missing" \
  run_surface "$fixture"

fixture="$(new_surface_fixture surface-cli-isolation)"
mkdir -p "$fixture/agentic"
printf '%s\n' \
  'import argparse' \
  'def run_alpha(_args): return 0' \
  'def build_parser():' \
  '    parser = argparse.ArgumentParser()' \
  '    sub = parser.add_subparsers(dest="command")' \
  '    alpha = sub.add_parser("alpha", help="alpha help")' \
  '    alpha.set_defaults(func=run_alpha)' \
  '    return parser' >"$fixture/agentic/cli.py"
python3 - "$fixture" "$SURFACE" <<'PY'
import hashlib
import json
import pathlib
import runpy
import sys

root = pathlib.Path(sys.argv[1])
module = runpy.run_path(sys.argv[2])
live, errors = module["discover_surfaces"](root)
if errors:
    raise SystemExit("\n".join(errors))
path = root / "specs/toolkit-core-simplification/BASELINE.json"
data = json.loads(path.read_text())
surface = live["cli-command:alpha"]
data["surfaces"].append(
    {
        "behavioral_tests": [],
        "content_sha256": surface.content_sha256,
        "dependents": [],
        "disposition": "measure-before-decision",
        "identity": surface.identity,
        "path": surface.path,
        "rationale": "Command-specific hash fixture.",
        "replacement": None,
        "surface_type": surface.surface_type,
    }
)
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_success "command-specific hash fixture starts valid" run_surface "$fixture"
python3 - "$fixture/agentic/cli.py" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text()
path.write_text(
    text.replace(
        "    return parser\n",
        '    beta = sub.add_parser("beta", help="beta help")\n'
        "    beta.set_defaults(func=run_alpha)\n"
        "    return parser\n",
    )
)
PY
python3 - "$fixture" "$SURFACE" <<'PY'
import hashlib
import json
import pathlib
import runpy
import sys

root = pathlib.Path(sys.argv[1])
module = runpy.run_path(sys.argv[2])
live, errors = module["discover_surfaces"](root)
if errors:
    raise SystemExit("\n".join(errors))
surface = live["cli-command:beta"]
fragment = {
    "$schema": "../surface.schema.json",
    "fragment": "beta",
    "git_blob_pin": 1,
    "manifest_type": "fragment",
    "schema_version": 2,
    "surfaces": [
        {
            "behavioral_tests": [],
            "content_sha256": surface.content_sha256,
            "dependents": [],
            "disposition": "measure-before-decision",
            "identity": surface.identity,
            "path": surface.path,
            "rationale": "Unrelated command classification.",
            "replacement": None,
            "surface_type": surface.surface_type,
        }
    ],
}
payload = json.dumps(fragment, sort_keys=True, separators=(",", ":")).encode()
fragment["frozen_sha256"] = hashlib.sha256(payload).hexdigest()
path = root / "specs/toolkit-core-simplification/surface-inventory/beta.json"
path.write_text(json.dumps(fragment, indent=2, sort_keys=True) + "\n")
PY
assert_success \
  "adding classified command does not drift retained command" \
  run_surface "$fixture"

new_check_fixture() {
  local name="$1" fixture="$TMP/$1"
  mkdir -p "$fixture/scripts" "$fixture/tests/inventory"
  cp "$CHECK" "$fixture/scripts/check.sh"
  chmod 755 "$fixture/scripts/check.sh"
  printf '%s' "$fixture"
}

write_test_inventory() {
  local fixture="$1" tests_json="$2"
  python3 - "$fixture/tests/inventory/core.json" "$tests_json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
tests = json.loads(sys.argv[2])
data = {
    "fragment": "core",
    "schema_version": 1,
    "tests": tests,
}
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
}

run_check() {
  bash "$1/scripts/check.sh"
}

fixture="$(new_check_fixture check-green)"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  "printf x >> '$fixture/count'" \
  'exit 0' >"$fixture/tests/test_a.sh"
chmod 755 "$fixture/tests/test_a.sh"
write_test_inventory "$fixture" \
  '[{"disposition":"retain","path":"tests/test_a.sh","runner":"bash","serial":false}]'
assert_success "inventoried retained test runs" run_check "$fixture"
if [ "$(wc -c <"$fixture/count")" -eq 1 ]; then
  pass=$((pass + 1))
  printf 'ok   - inventoried retained test runs exactly once\n'
else
  fail=$((fail + 1))
  printf 'FAIL - inventoried retained test runs exactly once\n'
fi

fixture="$(new_check_fixture check-missing)"
write_test_inventory "$fixture" \
  '[{"disposition":"retain","path":"tests/test_missing.sh","runner":"bash","serial":false}]'
assert_failure "missing inventoried test fails" "inventoried test missing" run_check "$fixture"

fixture="$(new_check_fixture check-unclassified)"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$fixture/tests/test_a.sh"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$fixture/tests/test_new.sh"
chmod 755 "$fixture/tests/test_a.sh" "$fixture/tests/test_new.sh"
write_test_inventory "$fixture" \
  '[{"disposition":"retain","path":"tests/test_a.sh","runner":"bash","serial":false}]'
assert_failure "unclassified executable test fails" "unclassified test" run_check "$fixture"

fixture="$(new_check_fixture check-duplicate)"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$fixture/tests/test_a.sh"
chmod 755 "$fixture/tests/test_a.sh"
write_test_inventory "$fixture" \
  '[{"disposition":"retain","path":"tests/test_a.sh","runner":"bash","serial":false},{"disposition":"retain","path":"tests/test_a.sh","runner":"bash","serial":false}]'
assert_failure "duplicate inventoried test fails" "duplicate inventoried test" run_check "$fixture"

fixture="$(new_check_fixture check-quarantine)"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$fixture/tests/test_a.sh"
printf '%s\n' '#!/usr/bin/env bash' 'exit 1' >"$fixture/tests/test_known_red.sh"
chmod 755 "$fixture/tests/test_a.sh" "$fixture/tests/test_known_red.sh"
write_test_inventory "$fixture" \
  '[{"disposition":"retain","path":"tests/test_a.sh","runner":"bash","serial":false},{"disposition":"quarantine","path":"tests/test_known_red.sh","reason":"Owned by fixture issue 17.","runner":"bash","serial":false}]'
if run_check "$fixture" >"$TMP/out" 2>&1 \
  && grep -q '\[quarantined:FAIL\] tests/test_known_red.sh' "$TMP/out" \
  && grep -q 'Owned by fixture issue 17.' "$TMP/out"; then
  pass=$((pass + 1))
  printf 'ok   - reasoned quarantine runs and is reported\n'
else
  fail=$((fail + 1))
  printf 'FAIL - reasoned quarantine runs and is reported\n'
  sed 's/^/       /' "$TMP/out"
fi

fixture="$(new_check_fixture check-unreasoned)"
printf '%s\n' '#!/usr/bin/env bash' 'exit 1' >"$fixture/tests/test_known_red.sh"
chmod 755 "$fixture/tests/test_known_red.sh"
write_test_inventory "$fixture" \
  '[{"disposition":"quarantine","path":"tests/test_known_red.sh","runner":"bash","serial":false}]'
assert_failure "quarantine without reason fails" "quarantine requires reason" run_check "$fixture"

fixture="$(new_check_fixture check-no-inventory)"
rm "$fixture/tests/inventory/core.json" 2>/dev/null || true
mkdir -p "$fixture/.claude-plugin"
printf '%s\n' '{}' >"$fixture/.claude-plugin/plugin.json"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$fixture/tests/test_a.sh"
chmod 755 "$fixture/tests/test_a.sh"
assert_failure \
  "toolkit marker without baseline fails" \
  "surface baseline missing" \
  run_check "$fixture"

fixture="$(new_surface_fixture check-surface-gate)"
mkdir -p "$fixture/scripts" "$fixture/tests/inventory"
cp "$CHECK" "$fixture/scripts/check.sh"
cp "$SURFACE" "$fixture/scripts/inventory-core-surface.py"
chmod 755 \
  "$fixture/scripts/check.sh" \
  "$fixture/scripts/inventory-core-surface.py"
write_test_inventory "$fixture" \
  '[{"disposition":"retain","path":"tests/test_demo.sh","runner":"bash","serial":false}]'
python3 - "$fixture/specs/toolkit-core-simplification/BASELINE.json" <<'PY'
import hashlib
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
data["surfaces"] = [
    row for row in data["surfaces"] if row["identity"] != "skill:demo"
]
payload = {key: value for key, value in data.items() if key != "frozen_sha256"}
data["frozen_sha256"] = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
assert_failure \
  "check runner directly rejects reduced surface baseline" \
  "unclassified surface" \
  run_check "$fixture"

printf '\npassed: %d, failed: %d\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
