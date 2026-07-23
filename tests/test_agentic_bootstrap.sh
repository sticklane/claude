#!/usr/bin/env bash
# SPEC R-B: fresh-clone bootstrap is `git clone <url> && agentic init` — ordinary
# git only, rebuilt from the committed JSONL. Only `git clone` and `agentic init`
# touch the fixture remote; the tracker is reconstructed from the committed
# `.beads/issues.jsonl`. Prints BOOTSTRAP OK with the imported issue count.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 1. Source repo with a bd tracker; commit only the JSONL transport + bd config
#    (mirrors a real repo: the Dolt store is gitignored, never committed).
SRC="$WORK/src"
mkdir -p "$SRC"
cd "$SRC"
git init -q .
git config user.name test
git config user.email test@example.com
BD_NON_INTERACTIVE=1 bd init --prefix bs >/dev/null 2>&1
for i in 1 2 3 4 5; do bd create "bootstrap issue $i" >/dev/null 2>&1; done
bd export -o .beads/issues.jsonl 2>/dev/null
EXPECTED="$(grep -c '"_type":"issue"' .beads/issues.jsonl)"
git add .beads/issues.jsonl .beads/config.yaml
git commit -qm "seed committed tracker JSONL"

# 2. Bare remote to clone from.
REMOTE="$WORK/remote.git"
git clone -q --bare "$SRC" "$REMOTE" 2>/dev/null

# 3. Bootstrap: clone + agentic init only.
CLONE="$WORK/clone"
git clone -q "$REMOTE" "$CLONE" 2>/dev/null
cd "$CLONE"
git config user.name test
git config user.email test@example.com
test -d .beads/embeddeddolt && { echo "FAIL: clone should not carry a Dolt store"; exit 1; }

"$AGENTIC" init >/dev/null 2>&1 || { echo "agentic init failed"; exit 1; }

COUNT="$(bd list --json 2>/dev/null | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"

if [ "$COUNT" = "$EXPECTED" ]; then
  echo "BOOTSTRAP OK ($COUNT issues imported)"
else
  echo "BOOTSTRAP FAIL: expected $EXPECTED issues, got $COUNT"
  exit 1
fi
