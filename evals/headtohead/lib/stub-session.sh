#!/usr/bin/env bash
# evals/headtohead/lib/stub-session.sh — deterministic, no-model stand-in for
# a headless session's cost accounting.
#
# Extends evals/stub-cli.sh's "no API key, no network, deterministic output"
# convention to the multi-session cost model this eval measures: a real run's
# usd/tokens are summed across the ROOT session AND every spawned child
# session, so the stub must be able to emit both. Each per-task stub.sh calls
# this helper to declare "I am a root session costing X" and, when it spawns
# work, "I spawned a child costing Y". The runner then sums every transcript
# file in the directory — root plus children — into one results row.
#
# Transcript files are plain JSON, one per session:
#   root.json      {"role":"root","usd":..,"tokens":..,"turns":..}
#   child-<id>.json{"role":"child","usd":..,"tokens":..,"turns":..}
#
# Written for bash 3.2 (macOS system bash).
set -eu

usage() {
  cat >&2 <<'EOF'
usage:
  stub-session.sh emit-root  <transcripts-dir> <usd> <tokens> <turns>
  stub-session.sh emit-child <transcripts-dir> <id> <usd> <tokens> <turns>
EOF
}

cmd="${1:-}"
case "$cmd" in
  emit-root)
    shift
    [ "$#" -eq 4 ] || { usage; exit 2; }
    dir="$1"; usd="$2"; tokens="$3"; turns="$4"
    mkdir -p "$dir"
    printf '{"role":"root","usd":%s,"tokens":%s,"turns":%s}\n' \
      "$usd" "$tokens" "$turns" > "$dir/root.json"
    ;;
  emit-child)
    shift
    [ "$#" -eq 5 ] || { usage; exit 2; }
    dir="$1"; id="$2"; usd="$3"; tokens="$4"; turns="$5"
    mkdir -p "$dir"
    printf '{"role":"child","usd":%s,"tokens":%s,"turns":%s}\n' \
      "$usd" "$tokens" "$turns" > "$dir/child-$id.json"
    ;;
  -h|--help)
    usage; exit 0
    ;;
  *)
    usage; exit 2
    ;;
esac
