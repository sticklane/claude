#!/usr/bin/env bash
# Link checker gate for docs/guides/ (specs/skill-profiling-workboard, R7):
# every relative link in a guide file must resolve to an existing file
# (resolved from that file's own directory), and every ```mermaid fence
# must have a non-empty body. Rides the repo's existing
# `for t in tests/test_*.sh; do bash "$t"; done` gate.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
guides_dir="$repo_root/docs/guides"

pass=0
fail=0

assert() {
  local desc="$1" ok="$2"
  if [ "$ok" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

if [ ! -d "$guides_dir" ]; then
  echo "FAIL: docs/guides/ directory is missing" >&2
  echo "pass: 0 fail: 1"
  exit 1
fi

shopt -s nullglob
guide_files=("$guides_dir"/*.md)
shopt -u nullglob

if [ "${#guide_files[@]}" -eq 0 ]; then
  echo "FAIL: docs/guides/ contains no markdown files" >&2
  echo "pass: 0 fail: 1"
  exit 1
fi

for f in "${guide_files[@]}"; do
  fdir="$(dirname "$f")"

  # --- relative markdown links: [text](path) where path is not a URL,
  # not an anchor-only fragment, and not empty. Strip any #fragment
  # before resolving.
  while IFS= read -r link; do
    [ -z "$link" ] && continue
    case "$link" in
      http://* | https://* | mailto:* | \#*) continue ;;
    esac
    target="${link%%#*}"
    [ -z "$target" ] && continue
    resolved="$fdir/$target"
    if [ -e "$resolved" ]; then
      assert "$f: link '$link' resolves" 0
    else
      assert "$f: link '$link' resolves (missing: $resolved)" 1
    fi
  done < <(grep -oE '\]\([^)]+\)' "$f" | sed -E 's/^\]\((.*)\)$/\1/')

  # --- mermaid fences: every ```mermaid opening fence must be followed
  # by a non-empty body before the closing ``` fence.
  awk -v file="$f" '
    /^```mermaid[[:space:]]*$/ {
      in_block = 1
      body_lines = 0
      next
    }
    in_block && /^```[[:space:]]*$/ {
      print (body_lines > 0) ? "OK" : "EMPTY"
      in_block = 0
      next
    }
    in_block {
      line = $0
      gsub(/[[:space:]]/, "", line)
      if (length(line) > 0) body_lines++
    }
  ' "$f" > "$here/.mermaid_check.$$" 2>/dev/null

  mermaid_count=0
  while IFS= read -r status; do
    [ -z "$status" ] && continue
    mermaid_count=$((mermaid_count + 1))
    if [ "$status" = "OK" ]; then
      assert "$f: mermaid fence #$mermaid_count has a non-empty body" 0
    else
      assert "$f: mermaid fence #$mermaid_count has a non-empty body" 1
    fi
  done < "$here/.mermaid_check.$$"
  rm -f "$here/.mermaid_check.$$"

  if [ "$mermaid_count" -eq 0 ]; then
    assert "$f: has at least one mermaid fence" 1
  fi
done

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
