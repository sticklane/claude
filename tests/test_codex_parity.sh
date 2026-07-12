#!/usr/bin/env bash
# Mechanical codex parity gate, sibling to test_antigravity_parity.sh.
#
# Every directory directly under .claude/skills/ (except _shared) and every
# .md file directly under .claude/agents/ must be EITHER
#   - present under codex/.agents/skills/<name>/ as a real directory or a
#     symlink whose target actually resolves (catches dangling links, not
#     just missing entries), or
#   - explicitly exempted by a first-token-anchored row in codex/README.md's
#     "What's not ported" table whose right (second) cell contains the
#     literal substring "Not ported" — same anchoring rule as the
#     antigravity gate (first delimited token of the left cell).
#
# Existence-only: this gate never inspects a mirrored skill's content.
#
# Output: on success, exit 0 with NO output. On failure, print each
# uncovered name (one per line) and exit 1.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
skills_dir="$repo_root/.claude/skills"
agents_dir="$repo_root/.claude/agents"
codex_skills="$repo_root/codex/.agents/skills"
readme="$repo_root/codex/README.md"

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

# --- exempted <name>: true if a README table row's anchored first token
# equals <name> and that row's second cell contains "Not ported".
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

# --- covered <name>: a real directory, or a symlink resolving to one.
covered() {
  local entry="$codex_skills/$1"
  [ -d "$entry" ] || return 1
  if [ -L "$entry" ]; then
    [ -e "$entry" ] || return 1  # dangling symlink
  fi
  return 0
}

uncovered=()
for n in "${names[@]}"; do
  covered "$n" && continue
  exempted "$n" && continue
  uncovered+=("$n")
done

if [ "${#uncovered[@]}" -gt 0 ]; then
  for u in "${uncovered[@]}"; do
    echo "$u"
  done
  exit 1
fi
exit 0
