#!/usr/bin/env bash
# Model-free regression test for the ctx capability surface the 2026-07-20
# shakedown proved live (specs/codebase-context-tree/evidence/
# capability-shakedown-2026-07-20.md): queries, notes + re-anchoring, lazy
# sync, and the MCP tool list, all against the committed demo fixture
# (context-tree/tests/fixtures/demo-codebase/). Guards the ctx binary's
# behavior contract as the /ctx skill and the crate evolve.
#
# Needs a prebuilt ctx binary (target/{release,debug}/ctx) and python3;
# without either it SKIPs (exit 0) so the fast model-free shell gate never
# compiles Rust — context-tree/scripts/check.sh owns the build. Opt in to
# an inline debug build with CTX_BUILD=1 (dev boxes with the toolchain).
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
crate="$repo_root/context-tree"

command -v python3 >/dev/null 2>&1 || {
  echo "test_ctx_capabilities: SKIP — python3 unavailable"
  exit 0
}

CTX=""
for cand in "$crate/target/release/ctx" "$crate/target/debug/ctx"; do
  [ -x "$cand" ] && CTX="$cand" && break
done
if [ -z "$CTX" ]; then
  if [ "${CTX_BUILD:-0}" = "1" ] && command -v cargo >/dev/null 2>&1; then
    (cd "$crate" && cargo build -q 2>/dev/null) || {
      echo "test_ctx_capabilities: FAIL — CTX_BUILD=1 but cargo build failed" >&2
      exit 1
    }
    CTX="$crate/target/debug/ctx"
  else
    echo "test_ctx_capabilities: SKIP — no prebuilt ctx (CTX_BUILD=1 + Rust toolchain to build inline)"
    exit 0
  fi
fi

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

fail() { echo "test_ctx_capabilities: FAIL — $*" >&2; exit 1; }

cp -R "$crate/tests/fixtures/demo-codebase/." "$TMP/repo"
cd "$TMP/repo"
git init -q .
git -c user.name=t -c user.email=t@example.com add -A
git -c user.name=t -c user.email=t@example.com commit -qm fixture

"$CTX" init >/dev/null || fail "ctx init errored"
[ -d .context ] || fail "init did not create .context/"

# --- query surface -----------------------------------------------------------
"$CTX" tree pyserver/taskflow | grep -q 'class Api' \
  || fail "tree: 'class Api' missing"
"$CTX" tree pyserver/taskflow | grep -q 'method submit' \
  || fail "tree: 'method submit' missing"
"$CTX" sig Dispatcher | grep -q 'class Dispatcher' \
  || fail "sig Dispatcher wrong"
"$CTX" refs claim_next | grep -q '^def .*dispatch\.py' \
  || fail "refs: def line missing"
"$CTX" refs claim_next | grep -q '^ref .*api\.py' \
  || fail "refs: cross-file ref in api.py missing"
"$CTX" deps pyserver/taskflow/api.py | grep -q -- '-> .storage' \
  || fail "deps: api.py -> .storage edge missing"
"$CTX" at pyserver/taskflow/storage.py:25 | grep -q 'class pyserver.taskflow.storage.Store' \
  || fail "at: enclosing class missing"
"$CTX" sig Store --json | python3 -c 'import json,sys; json.load(sys.stdin)' \
  || fail "--json output is not valid JSON"

# --- notes + re-anchoring ----------------------------------------------------
"$CTX" notes add pyserver.taskflow.dispatch.Dispatcher.claim_next \
  "retry accounting lives on claim" --kind invariant >/dev/null \
  || fail "notes add errored"
"$CTX" notes pyserver.taskflow.dispatch.Dispatcher.claim_next | grep -q fresh \
  || fail "note not fresh after add"
"$CTX" refs claim_next | grep -q '\[notes:1\]' \
  || fail "refs def line not decorated [notes:1]"

# shift the anchored symbol down two lines; note must survive as fresh
python3 - <<'PY'
from pathlib import Path
p = Path("pyserver/taskflow/dispatch.py")
p.write_text(p.read_text().replace(
    "class Dispatcher:", 'class Dispatcher:\n    """Claims tasks."""\n'))
PY
"$CTX" notes pyserver.taskflow.dispatch.Dispatcher.claim_next | grep -q fresh \
  || fail "note went stale after the symbol shifted (re-anchoring broke)"

# --- lazy sync (no manual sync step) -----------------------------------------
python3 - <<'PY'
from pathlib import Path
p = Path("pyserver/taskflow/storage.py")
p.write_text(p.read_text().replace("def load_task", "def fetch_task"))
PY
"$CTX" sig fetch_task | grep -q 'def fetch_task' \
  || fail "lazy sync: renamed symbol not visible on next query"
"$CTX" sig load_task 2>&1 | grep -q 'no symbol' \
  || fail "lazy sync: old symbol name still resolves"

# --- MCP smoke ---------------------------------------------------------------
mcp_tools="$(printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | "$CTX" mcp 2>/dev/null \
  | python3 -c 'import json,sys
for line in sys.stdin:
    try: m = json.loads(line)
    except ValueError: continue
    if m.get("id") == 2:
        print(",".join(sorted(t["name"] for t in m["result"]["tools"])))' )"
[ "$mcp_tools" = "at,deps,map,notes,notes_add,notes_list,refs,sig,tree" ] \
  || fail "MCP tools/list mismatch: got '$mcp_tools'"

echo "test_ctx_capabilities: PASS"
