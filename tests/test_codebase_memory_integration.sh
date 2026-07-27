#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="$ROOT/bin/install-codebase-memory"
LAUNCHER="$ROOT/bin/agentic-codebase-memory-mcp"
RELEASES="$ROOT/config/codebase-memory-release.json"
ROUTING="$ROOT/config/codebase-memory-routing-paths.txt"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() {
  echo "test_codebase_memory_integration: FAIL — $*" >&2
  exit 1
}

test -x "$INSTALLER" || fail "missing executable installer"
test -x "$LAUNCHER" || fail "missing executable launcher"
test -f "$RELEASES" || fail "missing release metadata"
test -f "$ROUTING" || fail "missing routing manifest"

python3 - "$RELEASES" <<'PY' || fail "release metadata mismatch"
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["version"] == "0.9.0"
assert data["repository"] == "DeusData/codebase-memory-mcp"
assert data["assets"] == {
    "darwin-amd64": {
        "name": "codebase-memory-mcp-darwin-amd64.tar.gz",
        "sha256": "6af3d02a27f589901fa763d3971089337bc8c9838bbed5d0cf543ca9f1a9e543",
    },
    "darwin-arm64": {
        "name": "codebase-memory-mcp-darwin-arm64.tar.gz",
        "sha256": "faa02f0404230c451a9812230394481948f80183801fa5bf67044b41c2f25ed4",
    },
    "linux-amd64": {
        "name": "codebase-memory-mcp-linux-amd64.tar.gz",
        "sha256": "e2832a8d207c26beaa30efa6222ed4a37cb3f526ca4bee060bfbf336ed6fc679",
    },
    "linux-arm64": {
        "name": "codebase-memory-mcp-linux-arm64.tar.gz",
        "sha256": "68a345d9a6842f02a3cb07e187b28bc38c4f3a22967f47fadbcd0757ba93a680",
    },
}
PY

mkdir -p "$TMP/no-network"
cat >"$TMP/no-network/curl" <<'SH'
#!/bin/sh
touch "$AGENTIC_CURL_WAS_CALLED"
exit 99
SH
chmod +x "$TMP/no-network/curl"

check_selection() {
  local os_name="$1" arch="$2" platform="$3" asset="$4" digest="$5"
  local out
  out="$(
    AGENTIC_CBM_TESTING=1 \
    AGENTIC_TEST_UNAME_S="$os_name" \
      AGENTIC_TEST_UNAME_M="$arch" \
      AGENTIC_CURL_WAS_CALLED="$TMP/curl-called" \
      PATH="$TMP/no-network:$PATH" \
      "$INSTALLER" --dry-run --dir "$TMP/install"
  )"
  grep -qF 'version: 0.9.0' <<<"$out" || fail "$platform version"
  grep -qF "platform: $platform" <<<"$out" || fail "$platform normalization"
  grep -qF "asset: $asset" <<<"$out" || fail "$platform asset"
  grep -qF "sha256: $digest" <<<"$out" || fail "$platform digest"
  grep -qF "destination: $TMP/install/codebase-memory-mcp" <<<"$out" \
    || fail "$platform destination"
  test ! -e "$TMP/curl-called" || fail "dry run called the network"
}

if AGENTIC_TEST_UNAME_S=Linux AGENTIC_TEST_UNAME_M=x86_64 \
  "$INSTALLER" --dry-run --dir "$TMP/install" >"$TMP/override.out" 2>&1
then
  fail "production mode accepted test-only platform overrides"
fi
grep -qF 'restricted to the test harness' "$TMP/override.out" \
  || fail "production override rejection is missing"

check_selection Darwin x86_64 darwin-amd64 \
  codebase-memory-mcp-darwin-amd64.tar.gz \
  6af3d02a27f589901fa763d3971089337bc8c9838bbed5d0cf543ca9f1a9e543
check_selection Darwin arm64 darwin-arm64 \
  codebase-memory-mcp-darwin-arm64.tar.gz \
  faa02f0404230c451a9812230394481948f80183801fa5bf67044b41c2f25ed4
check_selection Linux x86_64 linux-amd64 \
  codebase-memory-mcp-linux-amd64.tar.gz \
  e2832a8d207c26beaa30efa6222ed4a37cb3f526ca4bee060bfbf336ed6fc679
check_selection Linux aarch64 linux-arm64 \
  codebase-memory-mcp-linux-arm64.tar.gz \
  68a345d9a6842f02a3cb07e187b28bc38c4f3a22967f47fadbcd0757ba93a680

if AGENTIC_CBM_TESTING=1 \
  AGENTIC_TEST_UNAME_S=Plan9 AGENTIC_TEST_UNAME_M=mips \
  "$INSTALLER" --dry-run --dir "$TMP/install" >"$TMP/unsupported.out" 2>&1
then
  fail "unsupported platform succeeded"
fi
grep -qi 'unsupported platform' "$TMP/unsupported.out" \
  || fail "unsupported platform error missing"

mkdir -p "$TMP/archive-root" "$TMP/mockbin"
cat >"$TMP/archive-root/codebase-memory-mcp" <<'SH'
#!/bin/sh
printf 'fixture-binary\n'
SH
chmod +x "$TMP/archive-root/codebase-memory-mcp"
tar -czf "$TMP/fixture.tar.gz" -C "$TMP/archive-root" codebase-memory-mcp

if command -v shasum >/dev/null 2>&1; then
  fixture_sha="$(shasum -a 256 "$TMP/fixture.tar.gz" | awk '{print $1}')"
else
  fixture_sha="$(sha256sum "$TMP/fixture.tar.gz" | awk '{print $1}')"
fi

cat >"$TMP/release.json" <<EOF
{
  "version": "0.9.0",
  "repository": "DeusData/codebase-memory-mcp",
  "assets": {
    "darwin-arm64": {
      "name": "fixture.tar.gz",
      "sha256": "$fixture_sha"
    }
  }
}
EOF
cat >"$TMP/mockbin/curl" <<'SH'
#!/bin/sh
out=
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o|--output)
      out="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
test -n "$out"
cp "$AGENTIC_TEST_ARCHIVE" "$out"
SH
chmod +x "$TMP/mockbin/curl"

mkdir -p "$TMP/success"
printf 'old-binary\n' >"$TMP/success/codebase-memory-mcp"
printf 'old-launcher\n' >"$TMP/success/agentic-codebase-memory-mcp"
AGENTIC_CBM_TESTING=1 \
  AGENTIC_CBM_RELEASE_FILE="$TMP/release.json" \
  AGENTIC_TEST_ARCHIVE="$TMP/fixture.tar.gz" \
  AGENTIC_TEST_UNAME_S=Darwin \
  AGENTIC_TEST_UNAME_M=arm64 \
  PATH="$TMP/mockbin:$PATH" \
  "$INSTALLER" --dir "$TMP/success"

test "$("$TMP/success/codebase-memory-mcp")" = "fixture-binary" \
  || fail "fixture binary was not installed"
test -x "$TMP/success/agentic-codebase-memory-mcp" \
  || fail "launcher was not installed"
grep -qF '#!/usr/bin/env bash' "$TMP/success/agentic-codebase-memory-mcp" \
  || fail "existing launcher was not replaced"

mkdir -p "$TMP/rollback" "$TMP/failbin"
printf 'rollback-binary\n' >"$TMP/rollback-binary.expected"
printf 'rollback-launcher\n' >"$TMP/rollback-launcher.expected"
cp "$TMP/rollback-binary.expected" "$TMP/rollback/codebase-memory-mcp"
cp "$TMP/rollback-launcher.expected" \
  "$TMP/rollback/agentic-codebase-memory-mcp"
real_mv="$(command -v mv)"
cat >"$TMP/failbin/mv" <<'SH'
#!/bin/sh
count=0
if test -f "$AGENTIC_MV_COUNT"; then
  count="$(cat "$AGENTIC_MV_COUNT")"
fi
count=$((count + 1))
printf '%s\n' "$count" >"$AGENTIC_MV_COUNT"
if test "$count" -eq 2; then
  exit 1
fi
exec "$AGENTIC_REAL_MV" "$@"
SH
chmod +x "$TMP/failbin/mv"
if AGENTIC_CBM_TESTING=1 \
  AGENTIC_CBM_RELEASE_FILE="$TMP/release.json" \
  AGENTIC_TEST_ARCHIVE="$TMP/fixture.tar.gz" \
  AGENTIC_TEST_UNAME_S=Darwin \
  AGENTIC_TEST_UNAME_M=arm64 \
  AGENTIC_MV_COUNT="$TMP/mv-count" \
  AGENTIC_REAL_MV="$real_mv" \
  PATH="$TMP/failbin:$TMP/mockbin:$PATH" \
  "$INSTALLER" --dir "$TMP/rollback" >"$TMP/rollback.out" 2>&1
then
  fail "second replacement failure succeeded"
fi
cmp -s "$TMP/rollback-binary.expected" "$TMP/rollback/codebase-memory-mcp" \
  || fail "second replacement failure did not restore the binary"
cmp -s "$TMP/rollback-launcher.expected" \
  "$TMP/rollback/agentic-codebase-memory-mcp" \
  || fail "second replacement failure did not restore the launcher"

mkdir -p "$TMP/preserved"
printf 'old-binary\n' >"$TMP/preserved-binary.expected"
printf 'old-launcher\n' >"$TMP/preserved-launcher.expected"
cp "$TMP/preserved-binary.expected" "$TMP/preserved/codebase-memory-mcp"
cp "$TMP/preserved-launcher.expected" \
  "$TMP/preserved/agentic-codebase-memory-mcp"
python3 - "$TMP/release.json" "$TMP/bad-release.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
data["assets"]["darwin-arm64"]["sha256"] = "0" * 64
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(data, handle)
PY
if AGENTIC_CBM_TESTING=1 \
  AGENTIC_CBM_RELEASE_FILE="$TMP/bad-release.json" \
  AGENTIC_TEST_ARCHIVE="$TMP/fixture.tar.gz" \
  AGENTIC_TEST_UNAME_S=Darwin \
  AGENTIC_TEST_UNAME_M=arm64 \
  PATH="$TMP/mockbin:$PATH" \
  "$INSTALLER" --dir "$TMP/preserved" >"$TMP/bad.out" 2>&1
then
  fail "checksum mismatch succeeded"
fi
cmp -s "$TMP/preserved-binary.expected" "$TMP/preserved/codebase-memory-mcp" \
  || fail "checksum failure replaced the binary"
cmp -s "$TMP/preserved-launcher.expected" \
  "$TMP/preserved/agentic-codebase-memory-mcp" \
  || fail "checksum failure replaced the launcher"

printf 'not a tar archive\n' >"$TMP/broken.tar.gz"
if command -v shasum >/dev/null 2>&1; then
  broken_sha="$(shasum -a 256 "$TMP/broken.tar.gz" | awk '{print $1}')"
else
  broken_sha="$(sha256sum "$TMP/broken.tar.gz" | awk '{print $1}')"
fi
python3 - "$TMP/release.json" "$TMP/broken-release.json" "$broken_sha" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
data["assets"]["darwin-arm64"]["sha256"] = sys.argv[3]
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(data, handle)
PY
if AGENTIC_CBM_TESTING=1 \
  AGENTIC_CBM_RELEASE_FILE="$TMP/broken-release.json" \
  AGENTIC_TEST_ARCHIVE="$TMP/broken.tar.gz" \
  AGENTIC_TEST_UNAME_S=Darwin \
  AGENTIC_TEST_UNAME_M=arm64 \
  PATH="$TMP/mockbin:$PATH" \
  "$INSTALLER" --dir "$TMP/preserved" >"$TMP/broken.out" 2>&1
then
  fail "broken archive extraction succeeded"
fi
cmp -s "$TMP/preserved-binary.expected" "$TMP/preserved/codebase-memory-mcp" \
  || fail "extraction failure replaced the binary"
cmp -s "$TMP/preserved-launcher.expected" \
  "$TMP/preserved/agentic-codebase-memory-mcp" \
  || fail "extraction failure replaced the launcher"

mkdir -p "$TMP/stubbin" "$TMP/project" "$TMP/non-git"
git -C "$TMP/project" init -q
project_root="$(cd "$TMP/project" && pwd -P)"
cat >"$TMP/stubbin/codebase-memory-mcp" <<'SH'
#!/bin/sh
{
  printf 'root=%s\n' "$CBM_ALLOWED_ROOT"
  printf 'cache=%s\n' "$CBM_CACHE_DIR"
  printf 'args=%s\n' "$*"
} >"$AGENTIC_CAPTURE"
SH
chmod +x "$TMP/stubbin/codebase-memory-mcp"
(
  cd "$TMP/project"
  AGENTIC_CAPTURE="$TMP/launch.env" \
    XDG_CACHE_HOME="$TMP/xdg-cache" \
    PATH="$TMP/stubbin:$PATH" \
    "$LAUNCHER" alpha beta
)
grep -qF "root=$project_root" "$TMP/launch.env" \
  || fail "launcher did not restrict to the Git root"
grep -qF "cache=$TMP/xdg-cache/agentic/codebase-memory" "$TMP/launch.env" \
  || fail "launcher did not use the toolkit cache"
grep -qF 'args=alpha beta' "$TMP/launch.env" \
  || fail "launcher did not preserve arguments"
if (
  cd "$TMP/non-git"
  PATH="$TMP/stubbin:$PATH" "$LAUNCHER"
) >"$TMP/non-git.out" 2>&1
then
  fail "launcher started outside a Git worktree"
fi
grep -qi 'CBM_ALLOWED_ROOT' "$TMP/non-git.out" \
  || fail "launcher failure did not explain the allowed-root requirement"

mkdir -p "$TMP/claude-package" "$TMP/codex-package/.codex-plugin"
cp "$ROOT/.mcp.json" "$TMP/claude-package/.mcp.json"
cp "$ROOT/.codex-plugin/plugin.json" \
  "$TMP/codex-package/.codex-plugin/plugin.json"
cp "$ROOT/plugin.json" "$TMP/codex-package/plugin.json"
python3 - "$TMP/claude-package" "$TMP/codex-package" <<'PY' \
  || fail "MCP packaging mismatch"
import json
import pathlib
import sys

claude_root = pathlib.Path(sys.argv[1])
codex_root = pathlib.Path(sys.argv[2])
claude = json.loads((claude_root / ".mcp.json").read_text())
codex_manifest = json.loads(
    (codex_root / ".codex-plugin/plugin.json").read_text()
)
antigravity = json.loads((codex_root / "plugin.json").read_text())

claude_server = claude["mcpServers"]["codebase-memory-mcp"]
assert claude_server["command"] == "agentic-codebase-memory-mcp"
assert claude_server["args"] == []
assert claude_server["env"]["CBM_ALLOWED_ROOT"] == "${CLAUDE_PROJECT_DIR}"

codex_server = codex_manifest["mcpServers"]["codebase-memory-mcp"]
assert codex_server == {
    "command": "agentic-codebase-memory-mcp",
    "args": [],
}
assert set(antigravity) == {"$schema", "name", "description"}
PY

skill="$ROOT/.claude/skills/codebase-memory/SKILL.md"
test -f "$skill" || fail "canonical Codebase-Memory skill missing"
test ! -e "$ROOT/.claude/skills/ctx" || fail "canonical ctx skill still exists"
test ! -e "$ROOT/.agents/skills/ctx" && test ! -L "$ROOT/.agents/skills/ctx" \
  || fail "repo-local Codex ctx skill link still exists"
test -L "$ROOT/.agents/skills/codebase-memory" \
  || fail "repo-local Codex Codebase-Memory skill link missing"
test "$(readlink "$ROOT/.agents/skills/codebase-memory")" = \
  "../../.claude/skills/codebase-memory" \
  || fail "repo-local Codex Codebase-Memory skill link has the wrong target"
test -f "$ROOT/.agents/skills/codebase-memory/SKILL.md" \
  || fail "repo-local Codex Codebase-Memory skill target is broken"
for token in \
  index_repository get_architecture get_graph_schema search_graph trace_path \
  function_name direction depth mode detect_changes get_code_snippet \
  search_code index_status pagination \
  'ambiguous symbol' 'incomplete coverage' 'uncommitted' \
  'graph-empty' 'bounded direct source'
do
  grep -qiF "$token" "$skill" || fail "skill contract missing: $token"
done

python3 - "$skill" "$ROOT/tests/fixtures/codebase-memory-contract.json" <<'PY' \
  || fail "skill query-order fixture mismatch"
import json
import pathlib
import re
import sys

skill = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").lower()
cases = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
for name, sequence in cases.items():
    title = name.replace("-", " ")
    match = re.search(
        rf"^### {re.escape(title)}\s*$\n(?P<body>.*?)(?=^### |^## |\Z)",
        skill,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"{name}: local recipe section missing"
    recipe = " ".join(match.group("body").split())
    offset = 0
    for token in sequence:
        found = recipe.find(token.lower(), offset)
        assert found >= 0, f"{name}: {token!r} missing after offset {offset}"
        offset = found + len(token)
PY

while IFS='|' read -r rel contracts; do
  case "$rel" in
    ''|'#'*) continue ;;
  esac
  path="$ROOT/$rel"
  test -f "$path" || fail "routing path missing: $rel"
  IFS=',' read -r -a required <<<"$contracts"
  for contract in "${required[@]}"; do
    case "$contract" in
      cbm-first)
        grep -Eqi 'Codebase-Memory|codebase-memory' "$path" \
          || fail "$rel lacks CBM-first routing"
        ;;
      bounded-fallback)
        tr '\n' ' ' <"$path" |
          grep -Eqi '(bounded.{0,80}(^|[^[:alnum:]_])rg([^[:alnum:]_]|$)|(^|[^[:alnum:]_])rg([^[:alnum:]_]|$).{0,80}bounded)' \
          || fail "$rel lacks bounded rg fallback"
        ;;
      parent-handoff)
        tr '\n' ' ' <"$path" |
          grep -Eqi '(parent.{0,100}(project|qualified|coverage)|handoff.{0,100}(project|qualified|coverage))' \
          || fail "$rel lacks parent evidence handoff"
        ;;
      antigravity-native)
        grep -Eq '/mcp|mcp_config\\.json' "$path" \
          || fail "$rel lacks Antigravity-native MCP registration"
        ;;
      telemetry)
        grep -Eqi 'codebase.?memory' "$path" \
          || fail "$rel lacks Codebase-Memory telemetry"
        ;;
      *)
        fail "unknown routing contract '$contract' for $rel"
        ;;
    esac
  done
done <"$ROUTING"

echo "test_codebase_memory_integration: PASS"
