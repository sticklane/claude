#!/usr/bin/env bash
# Pins the prose-pack routing boundary between the writing pack
# (anti-ai-slop-writing + grounding + humanizer) and doc-coauthoring
# (bd agentic-9mo): the two claimed the "proposal" document type at once —
# CLAUDE.md's Authoring-conventions routing bullet listed "proposals" under
# the writing pack while doc-coauthoring's own description claims
# "draft a proposal" / position papers as its charter.
#
# Asserts, structurally anchored (never by line number):
#   1. CLAUDE.md's writing-pack routing bullet no longer claims "proposals".
#   2. doc-coauthoring cross-references the writing pack, completing the
#      prose pack's mutual do-NOT-use mesh.
#   3. plugin.json's version is bumped past 0.18.0 (skill behavior changed).
#   4. doc-coauthoring keeps its own proposal/position-paper trigger.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_MD="$ROOT/CLAUDE.md"
DOC_COAUTHORING="$ROOT/.claude/skills/doc-coauthoring/SKILL.md"
PLUGIN_JSON="$ROOT/.claude-plugin/plugin.json"

pass=0
fail=0

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
    echo "PASS: $desc"
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

# The routing bullet as a structural range: from the sentence naming the
# external-audience pack to the clause that closes the bullet.
writing_pack_bullet() {
  awk '/External-audience/,/claims-and-register rules/' "$CLAUDE_MD"
}

count_matches() { # count_matches <extended-regex> <file>
  grep -c -E "$1" "$2" || true
}

# --- 1. writing pack no longer claims the proposal document type ---------
bullet="$(writing_pack_bullet)"
assert_eq "writing-pack routing bullet is non-empty (anchor still matches)" \
  "yes" "$([ -n "$bullet" ] && echo yes || echo no)"
proposals_in_bullet="$(printf '%s\n' "$bullet" | grep -c 'proposals' || true)"
assert_eq "writing-pack routing bullet does not claim 'proposals'" \
  "0" "$proposals_in_bullet"

# --- 2. doc-coauthoring cross-references the writing pack ----------------
writing_pack_refs="$(count_matches 'anti-ai-slop-writing|grounding' "$DOC_COAUTHORING")"
assert_eq "doc-coauthoring cross-references the writing pack" \
  "yes" "$([ "$writing_pack_refs" -ge 1 ] && echo yes || echo no)"

# --- 3. plugin version bumped past the pre-change 0.18.0 -----------------
version="$(sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' "$PLUGIN_JSON" | head -n 1)"
newest="$(printf '%s\n%s\n' "0.18.0" "$version" | sort -V | tail -n 1)"
assert_eq "plugin.json version is greater than 0.18.0 (got '$version')" \
  "yes" "$([ "$version" != "0.18.0" ] && [ "$newest" = "$version" ] && echo yes || echo no)"

# --- 4. doc-coauthoring keeps its own proposal trigger -------------------
proposal_trigger="$(count_matches 'draft a proposal' "$DOC_COAUTHORING")"
assert_eq "doc-coauthoring keeps its 'draft a proposal' trigger" \
  "yes" "$([ "$proposal_trigger" -ge 1 ] && echo yes || echo no)"

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
