#!/usr/bin/env bash
# Hermetic tests for workboard actionability (specs/workboard-actionability).
# Exports HOME + CLAUDE_CONFIG_DIR to a throwaway tree and passes the fixture
# repo as an EXPLICIT positional root (default_roots() appends Path.cwd(), so
# omitting roots would leak the real repo into the scan). Tasks 02 and 03
# EXTEND this file; they never rewrite it.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
wb="$repo_root/.claude/skills/workboard/workboard.py"
fixtures_src="$here/fixtures/workboard-actionability"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Isolated HOME/CLAUDE_CONFIG_DIR ⇒ no real sessions leak into the scan.
export HOME="$tmp/home"
export CLAUDE_CONFIG_DIR="$tmp/home/.claude"
mkdir -p "$CLAUDE_CONFIG_DIR"

# Copy the fixture tree and git-init each repo (find_repos only yields dirs
# that contain a .git).
mkdir -p "$tmp/tree"
cp -R "$fixtures_src/." "$tmp/tree/"
roots=()
for d in "$tmp/tree"/*/; do
  git init -q "$d"
  roots+=("$d")
done

out="$tmp/wb.html"
python3 "$wb" "${roots[@]}" --out "$out" --actions-out "$tmp/a.sh" \
  --quiet --stale-days 7

fail=0
has()    { grep -qF -- "$1" "$out" || { echo "MISSING: $1"; fail=1; }; }
absent() { if grep -qF -- "$1" "$out"; then echo "UNEXPECTED: $1"; fail=1; fi; }

# R3 — the section always renders.
has "Ready to start"

# R1/R2/R3 — same-spec bare-numeric dep satisfied ⇒ single ready ⇒ /build with
# the fully-resolved filename (not an NN-*.md glob).
has '/build specs/single-ready/tasks/02-build-it.md'

# R1 — cross-spec ../-relative dep to a done task ⇒ ready (the case a
# same-spec-only rule would wrongly hide).
has '/build specs/cross-spec/tasks/01-consume.md'

# R2 — a spec with two ready tasks yields ONE spec-level /drain item.
has '/drain specs/multi-ready'

# R1 — a still-pending dependency ⇒ not ready (no launch command emitted).
absent '/build specs/pending-dep'
absent '/drain specs/pending-dep'

# R1 — an unresolvable dep id ⇒ not ready, but surfaced as blocked-by-unresolved
# with the offending id (99) visible.
absent '/build specs/unresolvable'
absent '/drain specs/unresolvable'
has 'unresolved dependency'
has '>99</code>'

if [ "$fail" -ne 0 ]; then
  echo "FAIL: workboard actionability assertions"
  exit 1
fi
echo "PASS: workboard actionability (R1-R3 subset)"
