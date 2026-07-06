#!/usr/bin/env bash
# Install-docs consistency gate (specs/install-docs-gate, R1-R6): the
# install commands in README.md and the cp paths in antigravity/README.md
# must stay consistent with .claude-plugin/{plugin,marketplace}.json and the
# repo tree. Rides the repo's existing
# `for t in tests/test_*.sh; do bash "$t"; done` gate (AGENTS.md:36).
#
# R6: an optional first argument overrides the repo root (defaulting to this
# script's own repo root, resolved the same way tests/test_doc_links.sh
# resolves paths). All file reads resolve under that root — this is the
# fixture-injection seam the acceptance criteria rely on.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${1:-$here/..}" && pwd)"

readme="$repo_root/README.md"
ag_readme="$repo_root/antigravity/README.md"
plugin_json="$repo_root/.claude-plugin/plugin.json"
marketplace_json="$repo_root/.claude-plugin/marketplace.json"

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

# Top-level "name" of a JSON file. jq when available; otherwise the first
# `"name":` key, which is the top-level one in both plugin.json (author.name
# comes later) and marketplace.json (owner.name / plugins[0].name come later).
json_top_name() {
  if command -v jq >/dev/null 2>&1; then
    jq -r '.name // empty' "$1"
  else
    grep -oE '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$1" | head -1 \
      | sed -E 's/.*:[[:space:]]*"([^"]*)".*/\1/'
  fi
}

# Nested owner.name. jq when available; otherwise the first `"name":` at or
# after the `"owner"` key (so plugins[0].name, which follows, is never hit).
json_owner_name() {
  if command -v jq >/dev/null 2>&1; then
    jq -r '.owner.name // empty' "$1"
  else
    grep -A3 '"owner"[[:space:]]*:' "$1" \
      | grep -oE '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 \
      | sed -E 's/.*:[[:space:]]*"([^"]*)".*/\1/'
  fi
}

for f in "$readme" "$ag_readme" "$plugin_json" "$marketplace_json"; do
  [ -f "$f" ] || { assert "required file exists: $f" 1; }
done

if [ "$fail" -gt 0 ]; then
  echo "pass: $pass fail: $fail"
  exit 1
fi

plugin_name="$(json_top_name "$plugin_json")"
market_name="$(json_top_name "$marketplace_json")"
owner_name="$(json_owner_name "$marketplace_json")"

# --- R1: every `/plugin install <X>@<Y>` in README pairs <X> with
# plugin.json's top-level name and <Y> with marketplace.json's top-level name.
r1_count=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  r1_count=$((r1_count + 1))
  x="${line%@*}"
  y="${line#*@}"
  if [ "$x" = "$plugin_name" ]; then
    assert "README '/plugin install $x@$y': plugin name matches plugin.json '$plugin_name'" 0
  else
    assert "plugin name mismatch: README install '$x' != plugin.json top-level name '$plugin_name'" 1
  fi
  if [ "$y" = "$market_name" ]; then
    assert "README '/plugin install $x@$y': marketplace name matches marketplace.json '$market_name'" 0
  else
    assert "marketplace name mismatch: README install '$y' != marketplace.json top-level name '$market_name'" 1
  fi
done < <(grep -oE '/plugin install [^ ]+@[^ ]+' "$readme" | sed -E 's#^/plugin install ##')

if [ "$r1_count" -eq 0 ]; then
  assert "README.md has at least one '/plugin install <X>@<Y>' command" 1
fi

# --- R2: every `/plugin marketplace add <owner>/<repo>` in README pairs
# <owner> with marketplace.json's owner.name.
r2_count=0
while IFS= read -r owner; do
  [ -z "$owner" ] && continue
  r2_count=$((r2_count + 1))
  if [ "$owner" = "$owner_name" ]; then
    assert "README '/plugin marketplace add $owner/...': owner matches marketplace.json owner.name '$owner_name'" 0
  else
    assert "owner mismatch: README marketplace add '$owner' != marketplace.json owner.name '$owner_name'" 1
  fi
done < <(grep -oE '/plugin marketplace add [^/ ]+/[^ ]+' "$readme" | sed -E 's#^/plugin marketplace add ([^/ ]+)/.*#\1#')

if [ "$r2_count" -eq 0 ]; then
  assert "README.md has at least one '/plugin marketplace add <owner>/<repo>' command" 1
fi

# --- R3: every source path a `cp` command in antigravity/README.md's install
# section copies from must exist under repo_root. Extraction: scope to the
# `## Install` section, take each `cp` line, drop flags and any trailing inline
# `# comment`, drop the last operand (the `.` destination), strip a leading
# `~/agentic-toolkit/` clone-dir prefix from each source, and check existence.
r3_count=0
while IFS= read -r src; do
  [ -z "$src" ] && continue
  r3_count=$((r3_count + 1))
  rel="${src#\~/agentic-toolkit/}"
  if [ -e "$repo_root/$rel" ]; then
    assert "antigravity install cp source '$src' exists at $rel" 0
  else
    assert "missing path: antigravity/README.md cp source '$src' -> $repo_root/$rel does not exist" 1
  fi
done < <(awk '
  /^## / { insec = ($0 ~ /^## Install([[:space:]]|$)/) ? 1 : 0 }
  insec && /^[[:space:]]*cp[[:space:]]/ {
    sub(/#.*/, "")                 # strip trailing inline comment
    n = split($0, tok, /[[:space:]]+/)
    # collect operands (non-flag tokens after the leading cp)
    ops = 0
    for (i = 1; i <= n; i++) {
      t = tok[i]
      if (t == "" || t == "cp") continue
      if (substr(t, 1, 1) == "-") continue
      ops++
      operand[ops] = t
    }
    # last operand is the destination; print the rest (sources)
    for (i = 1; i < ops; i++) print operand[i]
  }
' "$ag_readme")

if [ "$r3_count" -eq 0 ]; then
  assert "antigravity/README.md install section has at least one 'cp' source path" 1
fi

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
