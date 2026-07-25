#!/usr/bin/env bash
# Run a command with writes mechanically denied beneath one or more existing
# absolute paths. Used by drain before a boundary-sensitive worker starts.
set -u

usage() {
  echo "usage: write-deny.sh --deny-write /absolute/path [--deny-write /absolute/path ...] -- command [args ...]" >&2
  exit 64
}

denied=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --deny-write)
      [ "$#" -ge 2 ] || usage
      denied+=("$2")
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      usage
      ;;
  esac
done

[ "${#denied[@]}" -gt 0 ] || usage
[ "$#" -gt 0 ] || usage

canonical=()
for path in "${denied[@]}"; do
  case "$path" in
    /*) ;;
    *)
      echo "write-deny: denied path must be absolute: $path" >&2
      exit 65
      ;;
  esac
  if [ ! -e "$path" ]; then
    echo "write-deny: denied path does not exist: $path" >&2
    exit 66
  fi
  if ! resolved="$(realpath "$path" 2>/dev/null)"; then
    echo "write-deny: could not resolve denied path: $path" >&2
    exit 66
  fi
  canonical+=("$resolved")
done

case "$(uname -s)" in
  Darwin)
    sandbox="${AGENTIC_SANDBOX_EXEC:-$(command -v sandbox-exec 2>/dev/null || true)}"
    if [ -z "$sandbox" ] || [ ! -x "$sandbox" ]; then
      echo "write-deny: sandbox-exec is unavailable; refusing an unguarded launch" >&2
      exit 78
    fi
    profile='(version 1)(allow default)'
    for path in "${canonical[@]}"; do
      escaped="${path//\\/\\\\}"
      escaped="${escaped//\"/\\\"}"
      profile+="(deny file-write* (subpath \"$escaped\"))"
    done
    exec "$sandbox" -p "$profile" "$@"
    ;;
  Linux)
    bubblewrap="${AGENTIC_BWRAP:-$(command -v bwrap 2>/dev/null || true)}"
    if [ -z "$bubblewrap" ] || [ ! -x "$bubblewrap" ]; then
      echo "write-deny: bwrap is unavailable; refusing an unguarded launch" >&2
      exit 78
    fi
    bwrap_args=(--die-with-parent --bind / /)
    for path in "${canonical[@]}"; do
      bwrap_args+=(--ro-bind "$path" "$path")
    done
    exec "$bubblewrap" "${bwrap_args[@]}" -- "$@"
    ;;
  *)
    echo "write-deny: no supported OS sandbox; refusing an unguarded launch" >&2
    exit 78
    ;;
esac
