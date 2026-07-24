#!/usr/bin/env bash
# Structural checks on .claude/rules/token-discipline.md (bd agentic-zpx).
#
# The file is always-on context re-sent every session. Two properties are
# checked here:
#
#   1. It carries a table of contents, per CLAUDE.md's ">100-line reference
#      files open with a table of contents" convention, placed after the
#      intro paragraph and before the first content section, and listing
#      exactly the file's other section headings (the
#      .claude/skills/drain/reference.md TOC precedent).
#   2. It states its live rules directly rather than narrating machinery
#      that no longer exists. Three paragraphs used to spend their words on
#      "X was deleted, so the carve-out no longer applies"; each must now
#      state only what currently binds, without losing the rule itself.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$TOOLKIT_DIR/.claude/rules/token-discipline.md"

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  if [ "$2" = "$3" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1 (expected '$2', got '$3')" >&2
  fi
}

assert "token-discipline.md exists" test -f "$SRC"

# ─── 1. Table of contents ───

assert_eq "exactly one '## Table of contents' section" \
  1 "$(grep -c '^## Table of contents' "$SRC")"

assert_eq "the TOC is the file's first section (it follows the intro paragraph)" \
  "## Table of contents" "$(grep -m1 '^## ' "$SRC")"

# The 8 pre-existing section headings. Other repo files cite these by name,
# so none may be renamed or dropped.
sections=(
  "Delegation defaults"
  "Model and effort matching"
  "Dispatch authoring"
  "Session hygiene"
  "Session refresh"
  "Cache economics"
  "Cheap before expensive"
  "Match the research tool to the question"
)

for s in "${sections[@]}"; do
  assert "section heading '## $s' still present verbatim" \
    grep -qxF "## $s" "$SRC"
done

assert_eq "adding the TOC brings total sections to 9 (8 original + TOC)" \
  9 "$(grep -c '^## ' "$SRC")"

toc_bullets="$(awk '/^## Table of contents/{f=1;next} /^## /{f=0} f' "$SRC" | grep '^- ')"

assert_eq "the TOC has one bullet per other section" \
  8 "$(printf '%s\n' "$toc_bullets" | grep -c '^- ')"

for s in "${sections[@]}"; do
  assert "TOC names section '$s'" \
    grep -qF "$s" <<<"$toc_bullets"
done

# ─── 2. Dead-machinery narration trimmed, live rules retained ───

dead_phrases=(
  "was superseded by the agentic-core-redesign"
  "no longer applies: the agentic-core-redesign cutover deleted"
  "deleted in the agentic-core-redesign cutover"
)

for p in "${dead_phrases[@]}"; do
  assert_eq "dead-machinery narration removed: '$p'" \
    0 "$(grep -cF "$p" "$SRC")"
done

# Each trimmed location still states its live rule.
assert "the 3-5 concurrent-writer ceiling survives the trim" \
  grep -qF "concurrent-writer window" "$SRC"
assert "the awaited-children rule still binds without exception" \
  grep -qF "binds without exception" "$SRC"
assert "session refresh still scopes itself to freehand/watch-then-act sessions" \
  grep -qF "watch-then-act sessions" "$SRC"
assert "drain's lack of a baton/generation mechanism is still stated" \
  grep -qE "no baton (or|nor) generation" "$SRC"

echo "---"
echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
