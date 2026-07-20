#!/usr/bin/env bash
# Fixture: the committed multi-language demo codebase plus a prebuilt ctx
# binary at the skill's documented resolution path
# (context-tree/target/release/ctx). PRECONDITION: the source checkout has
# that binary built (cargo build --release in context-tree/) — setup fails
# loudly without it rather than spending eval-session turns compiling.
set -eu

SRC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BIN="$SRC_ROOT/context-tree/target/release/ctx"
[ -x "$BIN" ] || {
  echo "setup: missing $BIN — run 'cargo build --release' in context-tree/ first" >&2
  exit 1
}

cd "$EVAL_DIR"
cp -R "$SRC_ROOT/context-tree/tests/fixtures/demo-codebase/." .
mkdir -p context-tree/target/release
cp "$BIN" context-tree/target/release/ctx

git init -q
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: taskflow demo + ctx binary"
