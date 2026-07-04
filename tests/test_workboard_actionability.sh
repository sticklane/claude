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

# pushable-repo: give it an upstream it is ahead of, so git_info reports
# ahead>0 and the board emits a `git -C <repo> push` into the actions script.
pushable="$tmp/tree/pushable-repo"
git -C "$pushable" add -A
git -C "$pushable" -c user.email=t@e -c user.name=t commit -qm base
git -C "$pushable" branch -M main
git init -q --bare "$tmp/remote.git"
git -C "$pushable" remote add origin "$tmp/remote.git"
git -C "$pushable" push -q -u origin main
git -C "$pushable" -c user.email=t@e -c user.name=t commit -q --allow-empty -m ahead

out="$tmp/wb.html"
python3 "$wb" "${roots[@]}" --out "$out" --actions-out "$tmp/a.sh" \
  --quiet --stale-days 7

asrc="$tmp/a.sh"
fail=0
has()    { grep -qF -- "$1" "$out" || { echo "MISSING: $1"; fail=1; }; }
absent() { if grep -qF -- "$1" "$out"; then echo "UNEXPECTED: $1"; fail=1; fi; }
shas()    { grep -qF -- "$1" "$asrc" || { echo "MISSING in script: $1"; fail=1; }; }
sabsent() { if grep -qF -- "$1" "$asrc"; then echo "UNEXPECTED in script: $1"; fail=1; fi; }

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

# R1 — an unresolvable dep id is surfaced even when a resolvable-but-still-pending
# dep precedes it in the header (must not be swallowed by header ordering).
absent '/build specs/order-blocked'
has '>88</code>'

# R1 — the <slug>/NN shorthand and specs/-rooted dep forms resolve to done tasks
# and yield ready /build items (both resolution modes exercised end-to-end).
has '/build specs/shorthand-ready/tasks/01-uses-shorthand.md'
has '/build specs/rooted-ready/tasks/01-uses-rooted.md'

# ---------------------------------------------------------------- R4/R5
# R4 — the actions script exists, is executable, and is valid shell.
[ -x "$asrc" ] || { echo "actions script not executable"; fail=1; }
bash -n "$asrc" || { echo "actions script failed bash -n"; fail=1; }

# R4 — labeled, independently-runnable sections.
shas '# === Pushes ==='
shas '# === Verify done specs ==='

# R4 — a repo ahead of its upstream ⇒ a `git -C <repo> push` line.
shas 'pushable-repo push'

# R4 — an all-done unarchived toolkit spec ⇒ a `cd <repo>` + verifier line.
shas 'Use the verifier agent to verify specs/all-done against its acceptance criteria'

# R4/S5 — a Kiro done-spec is excluded (no verifier-agent flow), even though the
# inbox done-spec detector fires for it.
sabsent 'specs/kiro-done'

# R4 — the script never contains destructive/auto-launching actions.
if grep -Eq 'git mv|push (--force|-f)|(^|[^[:alnum:]])rm |/build|/drain' "$asrc"; then
  echo "FORBIDDEN token in actions script"; fail=1
fi

# R5 — the HTML links the script: path text + a `<td><code>` bash invocation
# (so the existing closest('td code') copy handler applies).
has "$asrc"
has '<td><code'
has "bash $asrc"

if [ "$fail" -ne 0 ]; then
  echo "FAIL: workboard actionability assertions"
  exit 1
fi
echo "PASS: workboard actionability (R1-R5 subset)"
