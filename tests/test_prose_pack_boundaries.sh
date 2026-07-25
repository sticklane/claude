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
#
# Also pins the review-cluster routing boundary (bd agentic-z5y): the skills
# in this repo that a bare "review this" could route to — /critique and
# /prose-review; /code-review and /review are harness-level, not editable
# here — claim disjoint trigger phrases, and each names a redirect to a
# sibling review skill. Substring overlap counts as a collision: "review
# this" claimed by one skill and "review this doc" by another is exactly the
# ambiguity this pins shut.
#   5. no review-cluster trigger phrase is claimed by two skills.
#   6. each review-cluster description carries a "not this skill, use X"
#      redirect naming another review skill.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_MD="$ROOT/CLAUDE.md"
DOC_COAUTHORING="$ROOT/.claude/skills/doc-coauthoring/SKILL.md"
PLUGIN_JSON="$ROOT/.claude-plugin/plugin.json"
REVIEW_CLUSTER="critique prose-review"

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

# --- 5/6. review-cluster trigger phrases are disjoint, redirects present -
skill_md() { printf '%s\n' "$ROOT/.claude/skills/$1/SKILL.md"; }

trigger_phrases() { # trigger_phrases <skill-dir-name>
  sed -n 's/^description: //p' "$(skill_md "$1")" |
    grep -o '"[^"]*"' | tr -d '"' | tr '[:upper:]' '[:lower:]' | sed '/^$/d'
}

collisions=""
for a in $REVIEW_CLUSTER; do
  a_count="$(trigger_phrases "$a" | grep -c . || true)"
  assert_eq "$a advertises at least one quoted trigger phrase" \
    "yes" "$([ "$a_count" -ge 1 ] && echo yes || echo no)"
  for b in $REVIEW_CLUSTER; do
    [ "$a" = "$b" ] && continue
    while IFS= read -r pa; do
      while IFS= read -r pb; do
        case "$pb" in
          *"$pa"*) collisions="$collisions $a:'$pa' vs $b:'$pb'" ;;
        esac
      done <<EOF
$(trigger_phrases "$b")
EOF
    done <<EOF
$(trigger_phrases "$a")
EOF
  done
done
assert_eq "no review-cluster trigger phrase is claimed by two skills (${collisions:-none})" \
  "" "$collisions"

for a in $REVIEW_CLUSTER; do
  redirect_targets=0
  for b in $REVIEW_CLUSTER code-review review; do
    [ "$a" = "$b" ] && continue
    if sed -n 's/^description: //p' "$(skill_md "$a")" |
      grep -q -E "[Nn]ot (the tool )?for [^.]*/$b|that is /$b"; then
      redirect_targets=$((redirect_targets + 1))
    fi
  done
  assert_eq "$a's description names a 'not this skill, use X' redirect" \
    "yes" "$([ "$redirect_targets" -ge 1 ] && echo yes || echo no)"
done

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
