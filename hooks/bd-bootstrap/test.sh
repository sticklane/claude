#!/usr/bin/env bash
# Unit tests for ensure-bd.sh — the bd-bootstrap SessionStart hook.
# Builds throwaway project trees under mktemp -d and a stub bd on PATH;
# never touches the real repo's .beads or the network.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/ensure-bd.sh"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1"
  fi
}

# Build a stub bd that logs every invocation and succeeds. `bd where`
# succeeds only when the fake DB dir exists, mirroring the real detection
# surface (hydrated store vs fresh clone).
make_stub() { # make_stub <bindir> <logfile> <project-root>
  cat > "$1/bd" <<EOF
#!/usr/bin/env bash
echo "bd \$*" >> "$2"
if [ "\$1" = "where" ]; then
  [ -d "$3/.beads/embeddeddolt" ] || exit 1
fi
exit 0
EOF
  chmod +x "$1/bd"
}

# --- no .beads dir: silent no-op ------------------------------------------
tmp="$(mktemp -d)"
out="$(CLAUDE_PROJECT_DIR="$tmp" BD_BOOTSTRAP_NO_INSTALL=1 bash "$HOOK" </dev/null 2>&1)"
rc=$?
check "no-beads: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "no-beads: silent" "$([ -z "$out" ] && echo 0 || echo 1)"
rm -rf "$tmp"

# --- bd on PATH, DB hydrated: passes straight through to bd prime ----------
tmp="$(mktemp -d)"
mkdir -p "$tmp/.beads/embeddeddolt" "$tmp/bin"
log="$tmp/calls.log"
make_stub "$tmp/bin" "$log" "$tmp"
out="$(CLAUDE_PROJECT_DIR="$tmp" BD_BOOTSTRAP_NO_INSTALL=1 PATH="$tmp/bin:$PATH" bash "$HOOK" </dev/null 2>&1)"
rc=$?
check "hydrated: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "hydrated: primes" "$(grep -q '^bd prime' "$log" && echo 0 || echo 1)"
check "hydrated: no init" "$(grep -q '^bd init' "$log" && echo 1 || echo 0)"
check "hydrated: no import" "$(grep -q '^bd import' "$log" && echo 1 || echo 0)"
rm -rf "$tmp"

# --- bd on PATH, no DB, committed JSONL present: hydrates then primes ------
tmp="$(mktemp -d)"
mkdir -p "$tmp/.beads" "$tmp/bin"
printf '{"id":"demo-abc","title":"x"}\n' > "$tmp/.beads/issues.jsonl"
printf '{"dolt_database": "demo"}\n' > "$tmp/.beads/metadata.json"
log="$tmp/calls.log"
make_stub "$tmp/bin" "$log" "$tmp"
out="$(CLAUDE_PROJECT_DIR="$tmp" BD_BOOTSTRAP_NO_INSTALL=1 PATH="$tmp/bin:$PATH" bash "$HOOK" </dev/null 2>&1)"
rc=$?
check "hydrate: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "hydrate: init with derived prefix" "$(grep -q '^bd init --prefix demo' "$log" && echo 0 || echo 1)"
check "hydrate: imports" "$(grep -q '^bd import' "$log" && echo 0 || echo 1)"
check "hydrate: primes after" "$(grep -q '^bd prime' "$log" && echo 0 || echo 1)"
rm -rf "$tmp"

# --- bd missing, install suppressed: one advisory line, exit 0 -------------
tmp="$(mktemp -d)"
mkdir -p "$tmp/.beads" "$tmp/emptybin"
printf '{"id":"demo-abc","title":"x"}\n' > "$tmp/.beads/issues.jsonl"
out="$(CLAUDE_PROJECT_DIR="$tmp" BD_BOOTSTRAP_NO_INSTALL=1 \
      BD_BOOTSTRAP_EXTRA_DIRS="" PATH="$tmp/emptybin:/usr/bin:/bin" bash "$HOOK" </dev/null 2>&1)"
rc=$?
lines="$(printf '%s' "$out" | grep -c . || true)"
check "missing: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "missing: exactly one line" "$([ "$lines" -eq 1 ] && echo 0 || echo 1)"
check "missing: names bd" "$(printf '%s' "$out" | grep -qi 'bd' && echo 0 || echo 1)"
rm -rf "$tmp"

# --- bd off PATH but in a known install dir: found via extra dirs ----------
tmp="$(mktemp -d)"
mkdir -p "$tmp/.beads/embeddeddolt" "$tmp/gobin" "$tmp/emptybin"
log="$tmp/calls.log"
make_stub "$tmp/gobin" "$log" "$tmp"
mkdir -p "$tmp/linkdir"
out="$(CLAUDE_PROJECT_DIR="$tmp" BD_BOOTSTRAP_NO_INSTALL=1 \
      BD_BOOTSTRAP_EXTRA_DIRS="$tmp/gobin" BD_BOOTSTRAP_LINK_DIR="$tmp/linkdir" \
      PATH="$tmp/emptybin:/usr/bin:/bin" bash "$HOOK" </dev/null 2>&1)"
rc=$?
check "off-path: exit 0" "$([ "$rc" -eq 0 ] && echo 0 || echo 1)"
check "off-path: primes via install dir" "$(grep -q '^bd prime' "$log" && echo 0 || echo 1)"
rm -rf "$tmp"

echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
