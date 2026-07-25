#!/usr/bin/env bash
# Launch a boundary-sensitive drain worker. This entrypoint deliberately has
# no unguarded mode: every accepted command is delegated to write-deny.sh.
set -u

usage() {
  echo "usage: dispatch-worker.sh --deny-write /absolute/path [--deny-write /absolute/path ...] -- command [args ...]" >&2
  exit 64
}

guard="$(cd "$(dirname "$0")" && pwd)/write-deny.sh"
deny_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --deny-write)
      [ "$#" -ge 2 ] || usage
      deny_args+=(--deny-write "$2")
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

[ "${#deny_args[@]}" -gt 0 ] || usage
[ "$#" -gt 0 ] || usage
if [ ! -x "$guard" ]; then
  echo "dispatch-worker: write-deny.sh is missing or not executable" >&2
  exit 78
fi

exec "$guard" "${deny_args[@]}" -- "$@"
