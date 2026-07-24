#!/usr/bin/env bash
# Model-free conformance test for CLAUDE.md's skill-closer convention
# (Authoring conventions: "closes with a `Next stage:` line ...").
#
# Three invariants over .claude/skills/*/SKILL.md:
#   A. No skill uses the non-canonical "Next pipeline step:" label.
#   B. build and fleet each carry exactly one `Next stage:` closer.
#   C. Wherever a `Next stage:` line exists, it OPENS the file's last
#      non-blank paragraph (the standalone-paragraph placement every
#      conforming skill already uses), never sits mid-paragraph.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS="$ROOT/.claude/skills"

pass=0
fail=0

report() {
  local desc="$1" ok="$2" detail="${3:-}"
  if [ "$ok" = "yes" ]; then
    pass=$((pass + 1))
    echo "  ok   $desc"
  else
    fail=$((fail + 1))
    echo "  FAIL $desc${detail:+ — $detail}"
  fi
}

# A. canonical label only
mislabeled="$(grep -rl 'Next pipeline step:' "$SKILLS" --include=SKILL.md || true)"
if [ -z "$mislabeled" ]; then
  report "no SKILL.md uses the 'Next pipeline step:' label" yes
else
  report "no SKILL.md uses the 'Next pipeline step:' label" no \
    "$(echo "$mislabeled" | tr '\n' ' ')"
fi

# B. required closers
for skill in build fleet; do
  file="$SKILLS/$skill/SKILL.md"
  count="$(grep -c '^Next stage:' "$file" || true)"
  if [ "$count" = "1" ]; then
    report "$skill/SKILL.md has exactly one 'Next stage:' closer" yes
  else
    report "$skill/SKILL.md has exactly one 'Next stage:' closer" no "found $count"
  fi
done

# C. placement: closer opens the last non-blank paragraph
opens_last_paragraph() {
  awk '
    { lines[NR] = $0 }
    END {
      last = NR
      while (last > 0 && lines[last] ~ /^[[:space:]]*$/) last--
      start = last
      while (start > 1 && lines[start - 1] !~ /^[[:space:]]*$/) start--
      if (lines[start] ~ /^Next stage:/) exit 0
      exit 1
    }
  ' "$1"
}

for file in "$SKILLS"/*/SKILL.md; do
  grep -q '^Next stage:' "$file" || continue
  name="$(basename "$(dirname "$file")")"
  if opens_last_paragraph "$file"; then
    report "$name/SKILL.md closer opens the final paragraph" yes
  else
    report "$name/SKILL.md closer opens the final paragraph" no \
      "final paragraph starts elsewhere"
  fi
done

echo "next-stage closers: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
