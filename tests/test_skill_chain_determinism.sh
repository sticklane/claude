#!/usr/bin/env bash
# test_skill_chain_determinism.sh — RED test for the not-yet-built
# evals/lint-skill-chain-determinism.sh gate (specs/deterministic-skill-chaining).
#
# Fixtures below are SYNTHETIC and ANONYMIZED, not raw transcript excerpts —
# each generalizes a real historical failure pattern found by mining this
# repo's own session logs (specs/deterministic-skill-chaining/SPEC.md
# "Problem" section), with every skill-specific/personal detail stripped to
# a generic stage-a/stage-b/stage-c shape. Two are POSITIVE controls
# (should PASS) drawn from patterns that were already correct.
#
# Expected gate CLI contract (defined here, implemented by the eventual
# fix): `evals/lint-skill-chain-determinism.sh <manifest-file>` where each
# manifest line is `<skill-md-path>|<condition-substring>|<required-
# imperative-substring>|<window-lines>`. For each line: if
# condition-substring appears in skill-md-path, required-imperative-
# substring must appear within window-lines of it, else the gate flags
# file:line and exits non-zero. A skill with no manifest line is skipped
# (opt-in heuristic, not exhaustive — same documented-blind-spot shape as
# tests/test_mirror_procedure_coverage.sh; see
# .claude/rules/mirror-procedure-discipline.md's "heuristic with blind
# spots" section for the precedent this mirrors).
#
# This test currently fails at the "gate script exists" assertion below —
# that failure IS the RED step; evals/lint-skill-chain-determinism.sh does
# not exist yet. The fix makes this pass without editing this file.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE="$ROOT/evals/lint-skill-chain-determinism.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
assert_exit() {
  local desc="$1" expect="$2" manifest="$3"
  "$GATE" "$manifest" >"$TMP/out" 2>&1
  local got=$?
  if [ "$got" -ne "$expect" ]; then
    echo "FAIL: $desc (expected exit $expect, got $got)"
    sed 's/^/    /' "$TMP/out"
    fail=1
  else
    echo "ok: $desc"
  fi
}

if [ ! -x "$GATE" ] && [ ! -f "$GATE" ]; then
  echo "FAIL: $GATE does not exist yet — this is the expected RED state"
  echo "      (specs/deterministic-skill-chaining/SPEC.md builds it)"
  exit 1
fi

# --- Fixture 1: invented-gate via a marker-only mention (finding 1 shape) ---
# Generalizes the real critique/breakdown bug: a skill documents that a
# completion marker is "the token another stage reads to auto-invoke
# itself," but never issues its OWN imperative to invoke the next stage —
# a session reading only this skill's text has no unambiguous instruction
# to act on.
cat >"$TMP/skill-marker-only.md" <<'EOF'
---
name: stage-a
---

1. On success, write `Ready: true` as a marker — this is the token
   stage-b reads to auto-invoke itself on specs with the marker set.
EOF
cat >"$TMP/manifest-1.txt" <<EOF
$TMP/skill-marker-only.md|Ready: true|invoke stage-b via the Skill tool|5
EOF
assert_exit "flags a marker-only mention with no self-chain imperative" 1 "$TMP/manifest-1.txt"

# --- Fixture 2: invented-gate via ambiguous multi-stage grouping (finding 2 shape) ---
# Generalizes the real "Running X, then Y + Z — none of these are
# auto-launched per this repo's gating rules" pattern: lumping a genuinely
# gated stage together with ungated stages in one sentence, so a reader
# can't tell which stage the gate actually binds.
cat >"$TMP/skill-grouped.md" <<'EOF'
---
name: stage-a
---

Running stage-b, then stage-c + stage-gated — none of these are
auto-launched per this repo's gating rules.
EOF
cat >"$TMP/manifest-2.txt" <<EOF
$TMP/skill-grouped.md|stage-c|invoke stage-c via the Skill tool|3
EOF
assert_exit "flags ambiguous multi-stage grouping with no per-stage imperative" 1 "$TMP/manifest-2.txt"

# --- Fixture 3: explicit self-chain imperative (positive control) ---
# Generalizes a real correct instance found in this repo's own logs: a
# session that reasoned "isn't gated so I'll continue straight into it" —
# an unambiguous, close-proximity imperative next to its trigger condition.
cat >"$TMP/skill-explicit.md" <<'EOF'
---
name: stage-a
---

1. On a READY verdict, invoke stage-b via the Skill tool now — announce
   the invocation in one line first.
EOF
cat >"$TMP/manifest-3.txt" <<EOF
$TMP/skill-explicit.md|READY verdict|invoke stage-b via the Skill tool|3
EOF
assert_exit "passes an explicit, close-proximity self-chain imperative" 0 "$TMP/manifest-3.txt"

# --- Fixture 4: machine-checkable gate declaration (positive control) ---
# Generalizes a real correct instance: a stage genuinely meant to be
# human-launched, declared via a literal checkable key rather than prose —
# the manifest simply has no self-chain line for it, so the gate is silent.
cat >"$TMP/skill-gated.md" <<'EOF'
---
name: stage-gated
disable-model-invocation: true
---

Human-launched only.
EOF
cat >"$TMP/manifest-4.txt" <<EOF
# stage-gated intentionally has no self-chain line — genuinely gated,
# declared via the literal disable-model-invocation key, not prose.
EOF
assert_exit "a skill absent from the manifest is skipped, not flagged" 0 "$TMP/manifest-4.txt"

exit $fail
