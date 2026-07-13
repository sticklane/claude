#!/usr/bin/env bash
# Advisory mirror procedure-coverage gate (spec mirror-procedure-discipline, R3/R4).
#
# Reads tests/mirror-procedure-manifest.txt — one `<source>|<mirror>|<phrase>`
# entry per line — and fails when a phrase is present in the source file but
# absent from its mirror. This is a coverage heuristic, not a semantic-
# equivalence checker; see .claude/rules/mirror-procedure-discipline.md for its
# two named blind spots (ordering-only divergence, mirror-adds-content).
#
# Manifest parsing: blank lines and lines whose first non-empty character is #
# are skipped (later audits append "# checked: ..." comment lines to the same
# file). Each remaining line splits on the first two `|` delimiters.
#
# Skip rule: if the source file itself does not contain the phrase, skip the
# line silently — a stale manifest entry against a since-changed source is not
# this test's job to catch, only source-has/mirror-lacks is.
#
# Output: on success, exit 0 with no output. On failure, print one clear line
# per gap naming source, mirror, and phrase, then exit 1. All failures are
# collected before exiting — the check never stops at the first.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
manifest="$here/mirror-procedure-manifest.txt"

if [ ! -f "$manifest" ]; then
  echo "manifest not found: $manifest"
  exit 1
fi

failures=0
while IFS= read -r line || [ -n "$line" ]; do
  # Skip blank lines and comment lines (first non-space char is #).
  trimmed="${line#"${line%%[![:space:]]*}"}"
  [ -z "$trimmed" ] && continue
  case "$trimmed" in
    \#*) continue ;;
  esac

  src="${line%%|*}"
  rest="${line#*|}"
  mir="${rest%%|*}"
  phrase="${rest#*|}"

  # A well-formed entry needs two `|` delimiters. No first pipe → src == line;
  # no second pipe → the mirror field spans the whole remainder (mir == rest).
  if [ "$src" = "$line" ] || [ "$mir" = "$rest" ] || [ -z "$phrase" ]; then
    echo "malformed manifest line (need source|mirror|phrase): $line"
    failures=$((failures + 1))
    continue
  fi

  src_file="$repo_root/$src"
  mir_file="$repo_root/$mir"

  # Source must exist and contain the phrase, else skip silently.
  [ -f "$src_file" ] || continue
  grep -qF -- "$phrase" "$src_file" || continue

  if [ ! -f "$mir_file" ]; then
    echo "MISSING MIRROR: $mir (source $src has phrase: \"$phrase\")"
    failures=$((failures + 1))
    continue
  fi

  if ! grep -qF -- "$phrase" "$mir_file"; then
    echo "PROCEDURE GAP: \"$phrase\" present in $src but absent from $mir"
    failures=$((failures + 1))
  fi
done < "$manifest"

if [ "$failures" -gt 0 ]; then
  exit 1
fi
exit 0
