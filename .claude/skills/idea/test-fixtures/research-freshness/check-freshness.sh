#!/usr/bin/env bash
# check-freshness.sh <dir> [--today YYYY-MM-DD]
#
# Scans a docs/-shaped tree for `##` headings and reports each heading's
# verification freshness as one of `fresh` / `stale` / `absent`, one line
# per matching heading (files walked in sorted path order).
#
# A heading is `fresh` when its `Verified:` date is within 90 days of
# --today, `stale` when older, `absent` when no stamp applies.
#
# Stamp resolution, per heading:
#   - heading-level: the FIRST non-blank line below the `##` heading must be
#     exactly `Verified: YYYY-MM-DD` (strict adjacency — no intro prose
#     permitted between a heading and its own stamp).
#   - file-level fallback (only when the heading has no heading-level stamp):
#     a `Verified: YYYY-MM-DD` line appearing anywhere in the file preamble
#     (after the H1, before the first `##`); this tolerates an intro
#     paragraph between the H1 and the stamp.
#   - a heading-level stamp always wins when both exist.
#
# --today defaults to the real current date.
set -u

usage() {
  echo "usage: check-freshness.sh <dir> [--today YYYY-MM-DD]" >&2
  exit 2
}

dir=""
today=""
while [ $# -gt 0 ]; do
  case "$1" in
    --today)
      shift
      today="${1:-}"
      [ -z "$today" ] && usage
      ;;
    -*) usage ;;
    *) dir="$1" ;;
  esac
  shift
done

[ -z "$dir" ] && usage
[ -d "$dir" ] || { echo "not a directory: $dir" >&2; exit 2; }
[ -z "$today" ] && today="$(date +%F)"

# Days since the civil epoch (Howard Hinnant's algorithm) — pure integer
# arithmetic, so no dependence on GNU-vs-BSD `date` difference math.
days_since_epoch() {
  local y=$((10#$1)) m=$((10#$2)) d=$((10#$3)) era yoe doy doe mp
  [ "$m" -le 2 ] && y=$((y - 1))
  if [ "$y" -ge 0 ]; then era=$((y / 400)); else era=$(((y - 399) / 400)); fi
  yoe=$((y - era * 400))
  if [ "$m" -gt 2 ]; then mp=$((m - 3)); else mp=$((m + 9)); fi
  doy=$(((153 * mp + 2) / 5 + d - 1))
  doe=$((yoe * 365 + yoe / 4 - yoe / 100 + doy))
  echo $((era * 146097 + doe - 719468))
}

date_to_days() {
  local s="$1" y m d rest
  y="${s%%-*}"; rest="${s#*-}"; m="${rest%%-*}"; d="${rest#*-}"
  days_since_epoch "$y" "$m" "$d"
}

today_days="$(date_to_days "$today")"

classify() {
  local vdate="$1" vdays diff
  if [ "$vdate" = "ABSENT" ]; then
    echo absent
    return
  fi
  vdays="$(date_to_days "$vdate")"
  diff=$((today_days - vdays))
  if [ "$diff" -le 90 ]; then echo fresh; else echo stale; fi
}

# Emit one date (or ABSENT) per `##` heading in the file, applying the
# heading-level / file-level resolution rules above.
extract_stamps() {
  awk '
    { lines[NR] = $0 }
    END {
      n = NR
      h1 = 0; first_h2 = 0
      for (i = 1; i <= n; i++) {
        if (!h1 && lines[i] ~ /^# /) { h1 = i; continue }
        if (lines[i] ~ /^## /) { first_h2 = i; break }
      }
      file_stamp = ""
      if (h1 > 0) {
        end = (first_h2 > 0) ? first_h2 - 1 : n
        for (i = h1 + 1; i <= end; i++) {
          if (lines[i] ~ /^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$/) {
            file_stamp = substr(lines[i], 11)
            break
          }
        }
      }
      for (i = 1; i <= n; i++) {
        if (lines[i] ~ /^## /) {
          hs = ""
          for (j = i + 1; j <= n; j++) {
            if (lines[j] ~ /^[[:space:]]*$/) continue
            if (lines[j] ~ /^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$/)
              hs = substr(lines[j], 11)
            break
          }
          if (hs != "") print hs
          else if (file_stamp != "") print file_stamp
          else print "ABSENT"
        }
      }
    }
  ' "$1"
}

while IFS= read -r f; do
  while IFS= read -r stamp; do
    [ -z "$stamp" ] && continue
    classify "$stamp"
  done < <(extract_stamps "$f")
done < <(find "$dir" -type f -name '*.md' | sort)
