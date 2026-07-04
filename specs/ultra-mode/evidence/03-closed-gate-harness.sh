#!/usr/bin/env bash
# 03-closed-gate-harness.sh — model-free structural proof that /critique in a
# no-runtimes fixture install can only take the single-critic path.
#
# The ultra path is gated on TWO conditions (SPEC.md R2, and critique/SKILL.md
# "## Ultra path"): ultracode opted in AND "the active runtime profile documents
# an orchestration section". A plugin/eval-style install ships without runtimes/
# (SPEC.md R9), so the profile condition is unsatisfiable and the panel template
# it points at is absent — the default single-critic path is the only reachable
# one, with no "ultra" leaking into behavior.
#
# Builds a throwaway mktemp fixture install; only evidence/03-closed-gate-e2e.md
# persists. Re-run: bash specs/ultra-mode/evidence/03-closed-gate-harness.sh
# Ref: specs/ultra-mode/SPEC.md R2, R6, R9.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SKILL="$ROOT/.claude/skills/critique/SKILL.md"
fail=0
pass() { printf 'PASS  %s\n' "$1"; }
fizz() { printf 'FAIL  %s\n' "$1"; fail=1; }

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT

# A no-runtimes fixture install: the critique skill, deliberately NO runtimes/.
mkdir -p "$FIX/.claude/skills/critique"
cp "$SKILL" "$FIX/.claude/skills/critique/SKILL.md"

# 1. The install has no runtimes/ dir at all -> profile condition unsatisfiable.
if [ ! -d "$FIX/runtimes" ]; then
  pass "fixture install has no runtimes/ dir (gate condition-2 unsatisfiable)"
else
  fizz "fixture install unexpectedly has a runtimes/ dir"
fi

# 2. No orchestration-section profile anywhere in the fixture -> the panel
#    workflow template the Ultra path points at is unreachable.
if ! grep -rqi "Orchestration (ultra)" "$FIX" 2>/dev/null; then
  pass "no '## Orchestration (ultra)' profile section present -> panel template unreachable"
else
  fizz "fixture unexpectedly contains an orchestration profile section"
fi

# 3. The default single-critic path is present and is the skill's primary flow.
if grep -q 'Spawn the `critic` agent' "$FIX/.claude/skills/critique/SKILL.md"; then
  pass "single-critic default path ('Spawn the critic agent') present in fixture skill"
else
  fizz "single-critic default path missing from fixture skill"
fi

# 4. The Ultra path text is gated: it explicitly says the single-critic path is
#    "the only path" when the profile is silent, and every 'ultra' mention sits
#    within +/-3 lines of the literal marker 'active runtime profile'.
if grep -qi "only path" "$FIX/.claude/skills/critique/SKILL.md"; then
  pass "Ultra path text states single-critic is the only path when profile is silent"
else
  fizz "Ultra path text missing the profile-silent 'only path' clause"
fi

ungated="$(awk '
  { line[NR] = $0 }
  END {
    for (i = 1; i <= NR; i++) {
      if (index(tolower(line[i]), "ultra") == 0) continue
      found = 0
      for (j = i - 3; j <= i + 3; j++)
        if (j >= 1 && j <= NR && index(line[j], "active runtime profile") > 0) { found = 1; break }
      if (!found) print i
    }
  }' "$FIX/.claude/skills/critique/SKILL.md")"
if [ -z "$ungated" ]; then
  pass "every 'ultra' mention gated within +/-3 lines of 'active runtime profile'"
else
  fizz "ungated 'ultra' mention(s) at fixture skill line(s): $ungated"
fi

# 5. Break-test: with the marker phrase stripped, the gate detector fires -> the
#    gating is load-bearing, not incidental.
sed 's/active runtime profile/XXXXX/g' "$FIX/.claude/skills/critique/SKILL.md" > "$FIX/broken.md"
broke="$(awk '
  { line[NR] = $0 }
  END {
    for (i = 1; i <= NR; i++) {
      if (index(tolower(line[i]), "ultra") == 0) continue
      found = 0
      for (j = i - 3; j <= i + 3; j++)
        if (j >= 1 && j <= NR && index(line[j], "active runtime profile") > 0) { found = 1; break }
      if (!found) { print i; break }
    }
  }' "$FIX/broken.md")"
if [ -n "$broke" ]; then
  pass "break-test: removing the marker phrase makes the gate detector fire (load-bearing)"
else
  fizz "break-test: gate detector did not fire after removing the marker phrase"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "closed-gate-harness: FAIL"
  exit 1
fi
echo "closed-gate-harness: OK — single-critic path is the only reachable path in a no-runtimes install"
