#!/usr/bin/env bash
# bd-bootstrap: SessionStart hook that makes the bd tracker usable before
# priming it. The previous wiring ran `bd prime --hook-json` bare, which
# silently fails on any machine without the binary or a hydrated database —
# every fresh cloud container ran outside the tracker while CLAUDE.md said
# bd was the source of truth. This hook closes that gap:
#
#   1. Repo has no .beads/           -> silent exit 0 (repo doesn't use bd).
#   2. bd off PATH but in a known    -> use it, and symlink into
#      install dir (go/bin, etc.)       /usr/local/bin when writable so the
#                                       session's later Bash calls resolve it.
#   3. bd missing entirely           -> start the documented installer (the
#      same command .beads/README.md gives) detached in the background, once
#      per container (marker file), and print ONE advisory line so the
#      session KNOWS it is outside the tracker instead of silently drifting.
#      BD_BOOTSTRAP_NO_INSTALL=1 suppresses the install attempt.
#   4. bd present, no database       -> hydrate from the committed JSONL:
#                                       bd init --prefix <metadata.json's
#                                       dolt_database> && bd import.
#   5. Finally: exec bd prime --hook-json (the original hook's behavior).
#
# Output discipline (token-discipline.md's hook cost rule): silent apart
# from bd prime's own output when everything is in place; exactly one line
# when the tracker is genuinely unavailable this session.
set -u

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
[ -d "$root/.beads" ] || exit 0

# Known install locations checked when bd is off PATH. Overridable for tests.
extra_dirs="${BD_BOOTSTRAP_EXTRA_DIRS-/root/go/bin:$HOME/go/bin:$HOME/.local/bin:/usr/local/bin}"

find_bd() {
  command -v bd 2>/dev/null && return 0
  local IFS=':' d
  for d in $extra_dirs; do
    [ -n "$d" ] && [ -x "$d/bd" ] && { printf '%s\n' "$d/bd"; return 0; }
  done
  return 1
}

bd_bin="$(find_bd)" || bd_bin=""

if [ -z "$bd_bin" ]; then
  marker="${TMPDIR:-/tmp}/bd-bootstrap-install-$(id -u 2>/dev/null || echo 0)"
  if [ "${BD_BOOTSTRAP_NO_INSTALL:-0}" != "1" ] && [ ! -e "$marker" ]; then
    : > "$marker"
    # Detached, logged, bounded: session start never blocks on a build.
    nohup bash -c \
      'curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | timeout 600 bash' \
      > "$marker.log" 2>&1 &
    echo "bd (beads) is not installed — background install started (log: $marker.log); the tracker is unavailable this session, so note bd-bound work in your final message instead of silently skipping it."
  else
    echo "bd (beads) is not installed and no install will be attempted — the tracker is unavailable this session, so note bd-bound work in your final message instead of silently skipping it."
  fi
  exit 0
fi

# Make bd resolvable for the session's later Bash calls when it lives off
# PATH (e.g. a go-install landed in /root/go/bin). Link dir is overridable
# so tests never write into the real /usr/local/bin.
link_dir="${BD_BOOTSTRAP_LINK_DIR:-/usr/local/bin}"
if ! command -v bd >/dev/null 2>&1; then
  if [ -d "$link_dir" ] && [ -w "$link_dir" ] && [ ! -e "$link_dir/bd" ]; then
    ln -s "$bd_bin" "$link_dir/bd" 2>/dev/null || true
  fi
fi

# Hydrate a fresh clone: binary present, no database, committed JSONL there.
if ! "$bd_bin" where >/dev/null 2>&1 && [ -f "$root/.beads/issues.jsonl" ]; then
  prefix=""
  if [ -f "$root/.beads/metadata.json" ]; then
    prefix="$(sed -n 's/.*"dolt_database"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
      "$root/.beads/metadata.json" | head -1)"
  fi
  if [ -n "$prefix" ]; then
    (cd "$root" && "$bd_bin" init --prefix "$prefix" >/dev/null 2>&1)
  else
    (cd "$root" && "$bd_bin" init >/dev/null 2>&1)
  fi
  (cd "$root" && "$bd_bin" import >/dev/null 2>&1) || true
fi

cd "$root" 2>/dev/null || true
exec "$bd_bin" prime --hook-json
