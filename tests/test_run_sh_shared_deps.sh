#!/usr/bin/env bash
# Self-test for run.sh's shared-dependency provisioning.
#
# run.sh copies the skill under test into the fixture, but several skills'
# scripts import sibling shared assets — .claude/skills/_shared and the
# top-level runtimes/ — and some load a sibling *skill* as a library
# (prioritize_scan.py loads workboard.py). This test proves run.sh
# provisions those centrally so scenarios no longer hand-copy them:
#
#   - _shared and runtimes/ land in every fixture unconditionally.
#   - a scenario's optional skill-deps.txt names extra sibling skills that
#     also get provisioned (one skill dir name per line).
#
# Pattern mirrors runner-selftest.sh: throwaway scenario trees under
# mktemp -d (never discoverable by a plain ./evals/run.sh) naming a real
# toolkit skill, driven with the no-model stub CLI; the scenario asserts run
# inside the fixture, so they inspect the provisioned tree directly.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL=handoff
DEP_SKILL=workboard
RUNNER_CMD="$ROOT/evals/stub-cli.sh"

TMP="$(mktemp -d)"
kept_fixtures=""
trap 'rm -rf "$TMP" $kept_fixtures' EXIT

mkdir -p "$TMP/$SKILL/01-shared-deps" "$TMP/$SKILL/02-skill-dep"

# Scenario 01: no skill-deps.txt — _shared and runtimes/ must still appear,
# alongside the skill under test itself.
printf '%s\n' "exit 0" > "$TMP/$SKILL/01-shared-deps/setup.sh"
printf '%s\n' "provision check" > "$TMP/$SKILL/01-shared-deps/prompt.txt"
cat > "$TMP/$SKILL/01-shared-deps/assert.sh" <<'EOF'
set -eu
[ -f .claude/skills/_shared/headers.py ] || { echo "missing _shared/headers.py" >&2; exit 1; }
[ -f runtimes/parse_headless.py ]       || { echo "missing runtimes/parse_headless.py" >&2; exit 1; }
[ -d .claude/skills/handoff ]           || { echo "skill under test not provisioned" >&2; exit 1; }
EOF

# Scenario 02: skill-deps.txt naming a sibling skill (with a comment + blank
# line to prove they are ignored) — that skill must be provisioned too.
printf '%s\n' "exit 0" > "$TMP/$SKILL/02-skill-dep/setup.sh"
printf '%s\n' "provision check" > "$TMP/$SKILL/02-skill-dep/prompt.txt"
printf '%s\n' "# sibling library dep" "" "$DEP_SKILL" > "$TMP/$SKILL/02-skill-dep/skill-deps.txt"
cat > "$TMP/$SKILL/02-skill-dep/assert.sh" <<EOF
set -eu
[ -f .claude/skills/$DEP_SKILL/workboard.py ] || { echo "declared skill-dep not provisioned" >&2; exit 1; }
[ -f .claude/skills/_shared/headers.py ]      || { echo "missing _shared alongside skill-dep" >&2; exit 1; }
EOF

rc=0
out="$(EVALS_ROOT="$TMP" RUNNER_CMD="$RUNNER_CMD" "$ROOT/evals/run.sh" "$SKILL" 2>&1)" || rc=$?
# run.sh keeps FAIL fixtures; reclaim any so a regression doesn't leak tmp dirs.
kept_fixtures="$(printf '%s\n' "$out" | sed -n 's/.*fixture kept: //p' | tr '\n' ' ')"

if [ "$rc" -ne 0 ]; then
  echo "SELFTEST FAIL: expected exit 0 (shared deps provisioned); got $rc. Output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
fi
printf '%s\n' "$out" | grep -q "^PASS  $SKILL/01-shared-deps" || {
  echo "SELFTEST FAIL: _shared/runtimes not provisioned centrally. Output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
}
printf '%s\n' "$out" | grep -q "^PASS  $SKILL/02-skill-dep" || {
  echo "SELFTEST FAIL: skill-deps.txt sibling not provisioned. Output:" >&2
  printf '%s\n' "$out" >&2
  exit 1
}

echo "run.sh shared-deps selftest: OK (_shared, runtimes/, and skill-deps.txt provisioning verified)"
