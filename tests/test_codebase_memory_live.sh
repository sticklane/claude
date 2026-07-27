#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASES="$ROOT/config/codebase-memory-release.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
checkout_state_before="$(git -C "$ROOT" status --porcelain=v1 -uall)"

fail() {
  echo "test_codebase_memory_live: FAIL — $*" >&2
  exit 1
}

case "$(uname -s):$(uname -m)" in
  Darwin:x86_64) platform=darwin-amd64 ;;
  Darwin:arm64) platform=darwin-arm64 ;;
  Linux:x86_64) platform=linux-amd64 ;;
  Linux:aarch64|Linux:arm64) platform=linux-arm64 ;;
  *) fail "manual-pending: unsupported live-smoke host $(uname -s)/$(uname -m)" ;;
esac

metadata="$(
  python3 - "$RELEASES" "$platform" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
asset = data["assets"][sys.argv[2]]
print(data["version"])
print(data["repository"])
print(asset["name"])
print(asset["sha256"])
PY
)"
version="$(printf '%s\n' "$metadata" | sed -n '1p')"
repository="$(printf '%s\n' "$metadata" | sed -n '2p')"
asset="$(printf '%s\n' "$metadata" | sed -n '3p')"
expected_sha="$(printf '%s\n' "$metadata" | sed -n '4p')"
url="https://github.com/$repository/releases/download/v$version/$asset"
archive="$TMP/$asset"

curl -fsSL --retry 2 -o "$archive" "$url"
if command -v shasum >/dev/null 2>&1; then
  actual_sha="$(shasum -a 256 "$archive" | awk '{print $1}')"
else
  actual_sha="$(sha256sum "$archive" | awk '{print $1}')"
fi
test "$actual_sha" = "$expected_sha" \
  || fail "archive checksum mismatch: expected $expected_sha, got $actual_sha"

mkdir -p "$TMP/bin" "$TMP/repo"
tar -xzf "$archive" -C "$TMP/bin"
binary="$(find "$TMP/bin" -type f -name codebase-memory-mcp | head -1)"
test -n "$binary" || fail "archive did not contain codebase-memory-mcp"
chmod +x "$binary"

cat >"$TMP/repo/example.py" <<'PY'
def greet(name: str) -> str:
    return f"hello {name}"


def main() -> None:
    print(greet("world"))
PY
git -C "$TMP/repo" init -q
git -C "$TMP/repo" -c user.name=t -c user.email=t@example.com add example.py
git -C "$TMP/repo" -c user.name=t -c user.email=t@example.com commit -qm fixture

export CBM_ALLOWED_ROOT="$TMP/repo"
export CBM_CACHE_DIR="$TMP/cache"
"$binary" cli index_repository --repo-path "$TMP/repo" >"$TMP/index.json"
"$binary" cli list_projects >"$TMP/projects.json"
project="$(
  python3 - "$TMP/projects.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
projects = data.get("projects", data if isinstance(data, list) else [])
if not projects:
    raise SystemExit("no indexed projects")
first = projects[0]
print(first["name"] if isinstance(first, dict) else first)
PY
)"

"$binary" cli get_architecture --project "$project" >"$TMP/architecture.json"
"$binary" cli get_graph_schema --project "$project" >"$TMP/schema.json"
"$binary" cli search_graph --project "$project" \
  --name-pattern '.*greet.*' --label Function >"$TMP/search.json"
qualified="$(
  python3 - "$TMP/search.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
items = data.get("results", data.get("nodes", []))
for item in items:
    if isinstance(item, dict):
        value = item.get("qualified_name") or item.get("qualifiedName") or item.get("qname")
        if value:
            print(value)
            break
else:
    raise SystemExit("greet qualified name missing")
PY
)"
"$binary" cli get_code_snippet --project "$project" \
  --qualified-name "$qualified" >"$TMP/snippet.json"
grep -q 'greet' "$TMP/snippet.json" || fail "source snippet did not contain greet"

test ! -e "$ROOT/.codebase-memory" \
  || fail "live smoke wrote graph state into the checkout"
test -d "$TMP/cache" || fail "live smoke did not use the temporary cache"
checkout_state_after="$(git -C "$ROOT" status --porcelain=v1 -uall)"
test "$checkout_state_after" = "$checkout_state_before" \
  || fail "live smoke changed checkout state"
echo "test_codebase_memory_live: PASS ($platform $version, project=$project)"
