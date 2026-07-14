#!/usr/bin/env bash
# lint-skill-size-gate.sh — model-free gate check for skill-doc size/TOC conventions.
#
# Mechanically checks two CLAUDE.md authoring conventions across every
# .claude/skills/*/SKILL.md and .claude/skills/*/reference.md:
#   (a) no SKILL.md exceeds 500 lines;
#   (b) no reference.md over 100 lines lacks a `## Table of contents` /
#       `## Contents` heading (case-insensitive) within its first 20 lines.
# Files are discovered by glob, so a new skill's docs are covered
# automatically. Prints each violation as `<path>:<count>: <reason>` and a
# final OK/FAIL line. Exits 0 only if every checked file is compliant.
#
# Invoked directly, never wired into the model-session eval runner (run.sh).
# Ref: specs/skill-doc-size-guards/SPEC.md R1, R2, R3.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

status=0

# (a) SKILL.md files must not exceed 500 lines.
for f in "$ROOT"/.claude/skills/*/SKILL.md; do
  [ -f "$f" ] || continue
  rel="${f#"$ROOT"/}"
  n=$(wc -l < "$f" | tr -d '[:space:]')
  if [ "$n" -gt 500 ]; then
    echo "$rel:$n: exceeds 500-line SKILL.md budget"
    status=1
  fi
done

# (b) reference.md files over 100 lines need a TOC heading in first 20 lines.
for f in "$ROOT"/.claude/skills/*/reference.md; do
  [ -f "$f" ] || continue
  rel="${f#"$ROOT"/}"
  n=$(wc -l < "$f" | tr -d '[:space:]')
  if [ "$n" -gt 100 ]; then
    if ! head -20 "$f" | grep -qiE '^## (Table of Contents|Contents)\b'; then
      echo "$rel:$n: missing TOC heading in first 20 lines"
      status=1
    fi
  fi
done

if [ "$status" -ne 0 ]; then
  echo "lint-skill-size-gate: FAIL"
  exit 1
fi
echo "lint-skill-size-gate: OK — all skill docs within size/TOC conventions"
