#!/usr/bin/env bash
# lint-ultra-gate.sh — model-free gate check for the ultra-path skills.
#
# For each of the four SKILL.md files that carry a `## Ultra path` section,
# every case-insensitive occurrence of "ultra" MUST have the literal marker
# phrase "active runtime profile" within ±3 lines. This keeps gate-closed
# installs (plugin caches, eval fixtures — no runtimes/ dir) reading as
# today's skills. Exits non-zero listing every violation as file:line.
#
# Invoked directly, never wired into evals/run.sh (that runs model sessions).
# Ref: specs/ultra-mode/SPEC.md R6.
set -u

MARKER="active runtime profile"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FILES=(
  ".claude/skills/critique/SKILL.md"
  ".claude/skills/drain/SKILL.md"
  ".claude/skills/build/SKILL.md"
  ".claude/skills/idea/SKILL.md"
)

status=0
for rel in "${FILES[@]}"; do
  f="$ROOT/$rel"
  if [ ! -f "$f" ]; then
    echo "$rel: MISSING"
    status=1
    continue
  fi
  awk -v marker="$MARKER" -v file="$rel" '
    { line[NR] = $0 }
    END {
      for (i = 1; i <= NR; i++) {
        if (index(tolower(line[i]), "ultra") == 0) continue
        found = 0
        for (j = i - 3; j <= i + 3; j++) {
          if (j >= 1 && j <= NR && index(line[j], marker) > 0) { found = 1; break }
        }
        if (!found) {
          printf "%s:%d: \"ultra\" not within 3 lines of \"%s\"\n", file, i, marker
          bad = 1
        }
      }
      exit bad ? 1 : 0
    }
  ' "$f" || status=1
done

if [ "$status" -ne 0 ]; then
  echo "lint-ultra-gate: FAIL"
  exit 1
fi
echo "lint-ultra-gate: OK — all ultra mentions gated in ${#FILES[@]} files"
