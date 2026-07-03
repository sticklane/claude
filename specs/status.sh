#!/bin/sh
# specs/status.sh — live work-state dashboard, derived on demand.
# Scans specs/*/tasks/*.md relative to the current directory; each task's
# status is the FIRST line matching `^Status:` anywhere in the file (no
# match -> "none"). Prints one "<status> <path>" row per task, then a
# TOTAL section counting each distinct status. Read-only; POSIX shell +
# grep/sed/sort/uniq only. No arguments.
set -u

rows=""
for f in specs/*/tasks/*.md; do
  [ -e "$f" ] || continue
  s=$(sed -n '/^Status:/{s/^Status:[[:space:]]*//;s/[[:space:]]*$//;p;q;}' "$f")
  [ -n "$s" ] || s=none
  rows="${rows}${s} ${f}
"
done

if [ -z "$rows" ]; then
  echo "Queue is empty: no task files under specs/*/tasks/."
  exit 0
fi

printf '%s' "$rows" | while read -r s f; do
  printf '%-12s %s\n' "$s" "$f"
done

echo ""
echo "TOTAL"
printf '%s' "$rows" | sed 's/ .*//' | sort | uniq -c | while read -r n s; do
  echo "  $s: $n"
done
echo "  all: $(printf '%s' "$rows" | grep -c ' ')"
