#!/usr/bin/env bash
# Mechanical antigravity parity gate (spec antigravity-parity-gate, R1-R5).
#
# Every directory directly under .claude/skills/ (except _shared) and every
# .md file directly under .claude/agents/ must be EITHER
#   - mirrored into antigravity/.agents/skills/<name>/ (a directory), or
#   - mirrored into antigravity/.agents/workflows/<name>.md (a file), or
#   - explicitly exempted by a first-token-anchored row in
#     antigravity/README.md's "What maps to what" table whose right (second)
#     cell contains the literal substring "Not ported".
#
# Anchoring (R2): a row exempts <name> only when the FIRST delimited token of
# its left cell — the leading backtick-quoted `...` span or the leading
# /slash-command token, whichever starts the cell — equals <name> (with or
# without backticks/leading slash). A token appearing later in the cell does
# NOT count.
#
# Existence-only (R5): this gate never inspects a mirrored skill's content.
#
# Output (R4): on success, exit 0 with NO output. On failure, print each
# uncovered name (one per line) and exit 1.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
skills_dir="$repo_root/.claude/skills"
agents_dir="$repo_root/.claude/agents"
ag_skills="$repo_root/antigravity/.agents/skills"
ag_workflows="$repo_root/antigravity/.agents/workflows"
readme="$repo_root/antigravity/README.md"

# --- Build the set of names to check: skill dirs (minus _shared) + agent basenames.
names=()
for d in "$skills_dir"/*/; do
  [ -d "$d" ] || continue
  n="$(basename "$d")"
  [ "$n" = "_shared" ] && continue
  names+=("$n")
done
for f in "$agents_dir"/*.md; do
  [ -e "$f" ] || continue
  names+=("$(basename "$f" .md)")
done

# --- exempted <name>: true if a README table row's anchored first token equals
# <name> and that row's second cell contains "Not ported".
exempted() {
  local target="$1"
  local line rest cell1 cell2 tok
  while IFS= read -r line; do
    case "$line" in
      \|*) ;;
      *) continue ;;
    esac
    rest="${line#|}"
    cell1="${rest%%|*}"
    rest="${rest#*|}"
    cell2="${rest%%|*}"
    # ltrim cell1
    cell1="${cell1#"${cell1%%[![:space:]]*}"}"
    tok=""
    if [[ "$cell1" =~ ^\`([^\`]+)\` ]]; then
      tok="${BASH_REMATCH[1]}"
    elif [[ "$cell1" =~ ^(/[A-Za-z0-9_-]+) ]]; then
      tok="${BASH_REMATCH[1]}"
    else
      continue
    fi
    tok="${tok#/}"
    if [ "$tok" = "$target" ]; then
      case "$cell2" in
        *"Not ported"*) return 0 ;;
      esac
    fi
  done < "$readme"
  return 1
}

uncovered=()
for n in "${names[@]}"; do
  if [ -d "$ag_skills/$n" ] || [ -f "$ag_workflows/$n.md" ]; then
    continue
  fi
  if exempted "$n"; then
    continue
  fi
  uncovered+=("$n")
done

if [ "${#uncovered[@]}" -gt 0 ]; then
  for u in "${uncovered[@]}"; do
    echo "$u"
  done
  exit 1
fi
exit 0
