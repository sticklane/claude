#!/usr/bin/env bash
# Model-free test of the rolling-window scheduler's admission function (SPEC
# specs/drain-rolling-window/SPEC.md — requirements R1, R4, R8a, R9). Simulates
# admission purely mechanically: no LLM, no `claude` invocation. Header-only
# task-file fixtures live in a throwaway temp dir; a pure-shell admission
# function decides the next admissible task from committed headers plus the
# run's live in-flight window. Proves R9's termination properties (no deadlock,
# no livelock, no starvation) hold given the requirements text SPEC.md pins,
# independent of how the drain prose phrases them. Never touches a real repo.
#
# Mirrors tests/test_drain_owner_protocol.sh's style: custom assert helpers,
# one report_case line per scenario, non-zero exit if any case fails. Written
# for bash 3.2 (macOS default): no associative arrays, empty indexed arrays
# expanded by index only so `set -u` never trips on an unbound array element.
set -u

pass=0
fail=0
case_fail=0

note_pass() { pass=$((pass + 1)); }
note_fail() { # note_fail <description>
  fail=$((fail + 1))
  case_fail=1
  echo "FAIL: $1" >&2
}

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then note_pass; else note_fail "$desc"; fi
}

assert_not() { # assert_not <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then note_fail "$desc"; else note_pass; fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then note_pass; else note_fail "$desc (expected: '$expected', got: '$actual')"; fi
}

report_case() { # report_case <letter> <label>
  if [ "$case_fail" -eq 0 ]; then
    echo "PASS: ($1) $2"
  else
    echo "FAIL: ($1) $2"
  fi
  case_fail=0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Co-admissibility groups for the scenario under test: each element is one
# `Group:` line's task numbers, space-separated. Reset per case. Named GRP (not
# GROUPS — GROUPS is a bash builtin array and is read-only in some shells).
GRP=()

# --------------------------------------------------------------------------- #
# Fixture + header helpers                                                     #
# --------------------------------------------------------------------------- #

mktask() { # mktask <dir> <num> <name> <status> <deps> <touch>
  local dir="$1" num="$2" name="$3" status="$4" deps="$5" touch="$6"
  mkdir -p "$dir"
  cat > "$dir/$num-$name.md" <<EOF
Status: $status
Depends on: $deps
Touch: $touch

## Goal
fixture task $num
EOF
}

set_status() { # set_status <file> <newstatus> — flip Status header in place
  local f="$1" s="$2" tmp
  tmp="$(mktemp)"
  awk -v s="$s" '/^Status:/{print "Status: " s; next} {print}' "$f" > "$tmp"
  mv "$tmp" "$f"
}

taskfile() { ls "$1"/"$2"-*.md; }         # taskfile <dir> <num>
hdr() { grep "^$2:" "$1" | head -1 | sed "s/^$2: *//"; }  # hdr <file> <Key>
status_of() { hdr "$(taskfile "$1" "$2")" Status; }
deps_list() { hdr "$(taskfile "$1" "$2")" "Depends on"; }
touch_list() { hdr "$(taskfile "$1" "$2")" Touch; }

in_list() { # in_list <needle> <space-list> — 0 if present
  case " $2 " in *" $1 "*) return 0;; *) return 1;; esac
}

disjoint() { # disjoint <touchA> <touchB> — 0 if no shared path
  local a b
  for a in $1; do
    for b in $2; do
      [ "$a" = "$b" ] && return 1
    done
  done
  return 0
}

# The claim set (R1): every task whose committed Status is in-progress — live
# workers AND suspected zombies alike, since a zombie keeps Status:in-progress.
claim_set() { # claim_set <dir>
  local dir="$1" f num
  for f in "$dir"/*.md; do
    [ -e "$f" ] || continue
    if [ "$(hdr "$f" Status)" = "in-progress" ]; then
      num="$(basename "$f")"; num="${num%%-*}"
      printf '%s ' "$num"
    fi
  done
}

# Returns the claim-set task number whose Touch overlaps <num>, or empty.
touch_blocker() { # touch_blocker <dir> <num>
  local dir="$1" num="$2" c t
  t="$(touch_list "$dir" "$num")"
  for c in $(claim_set "$dir"); do
    [ "$c" = "$num" ] && continue
    if ! disjoint "$t" "$(touch_list "$dir" "$c")"; then
      echo "$c"; return
    fi
  done
}

deps_done() { # deps_done <dir> <num> — 0 if every dependency is done
  local dir="$1" num="$2" deps d
  deps="$(deps_list "$dir" "$num")"
  [ "$deps" = "none" ] && return 0
  for d in $deps; do
    [ "$(status_of "$dir" "$d")" = "done" ] || return 1
  done
  return 0
}

# R1 co-admissibility: <num> may join the in-flight set iff some single Group:
# line names <num> and every in-flight task. An empty window admits anything
# (vacuously true); a no-group task therefore admits only when the window is
# empty, and blocks anything else while it runs.
co_admissible() { # co_admissible <num> <inflight-list>
  local num="$1" inflight="$2" f i g ok
  [ -z "${inflight// }" ] && return 0
  for f in $inflight; do
    ok=1
    for (( i=0; i<${#GRP[@]}; i++ )); do
      g="${GRP[$i]}"
      if in_list "$num" "$g" && in_list "$f" "$g"; then ok=0; break; fi
    done
    [ "$ok" -eq 0 ] || return 1
  done
  return 0
}

# R1 full admission predicate for one task, given window size W and the live
# in-flight set. Window room caps TOTAL live workers, not the zombie claim set.
admissible() { # admissible <dir> <num> <W> <inflight>
  local dir="$1" num="$2" W="$3" inflight="$4" live
  [ "$(status_of "$dir" "$num")" = "pending" ] || return 1
  deps_done "$dir" "$num" || return 1
  [ -z "$(touch_blocker "$dir" "$num")" ] || return 1
  co_admissible "$num" "$inflight" || return 1
  live=$(set -- $inflight; echo $#)
  [ "$live" -lt "$W" ] || return 1
  return 0
}

# Deterministic tie-break: lowest task number first (ls | sort).
next_admissible() { # next_admissible <dir> <W> <inflight>
  local dir="$1" W="$2" inflight="$3" f num
  for f in $(ls "$dir"/*.md | sort); do
    num="$(basename "$f")"; num="${num%%-*}"
    if admissible "$dir" "$num" "$W" "$inflight"; then echo "$num"; return; fi
  done
}

# R9.2: a pending task refused because its Touch overlaps a suspected zombie's
# claim (a committed in-progress task holding no live window slot) is reported,
# not silently starved. Prints the report line, or fails if not zombie-blocked.
zombie_block_report() { # zombie_block_report <dir> <num> <inflight>
  local dir="$1" num="$2" inflight="$3" b
  b="$(touch_blocker "$dir" "$num")"
  [ -n "$b" ] || return 1
  in_list "$b" "$inflight" && return 1   # blocker holds a live slot: not a zombie
  echo "blocked by suspected zombie $b"
}

# R9.3: detect an unsatisfiable remainder — pending tasks remain but none can
# ever be admitted (a Depends on: cycle, or all pending depend transitively on
# tasks that cannot complete this run). Least-fixpoint over "can eventually
# complete": a pending task can complete iff every dependency is done, live
# in-flight (will finish), or itself a pending task that can complete. Returns 0
# (fire the batch-interview / final report) when no pending task can complete.
unsatisfiable_remainder() { # unsatisfiable_remainder <dir> <inflight>
  local dir="$1" inflight="$2" f n pend="" cc="" changed t deps d ds all_ok
  for f in "$dir"/*.md; do
    [ -e "$f" ] || continue
    n="$(basename "$f")"; n="${n%%-*}"
    [ "$(hdr "$f" Status)" = "pending" ] && pend="$pend $n"
  done
  [ -n "${pend// }" ] || return 1        # nothing pending: run ends normally
  changed=1
  while [ "$changed" -eq 1 ]; do
    changed=0
    for t in $pend; do
      in_list "$t" "$cc" && continue
      deps="$(deps_list "$dir" "$t")"
      all_ok=1
      if [ "$deps" != "none" ]; then
        for d in $deps; do
          ds="$(status_of "$dir" "$d")"
          if [ "$ds" = "done" ]; then :
          elif in_list "$d" "$inflight"; then :
          elif [ "$ds" = "pending" ] && in_list "$d" "$cc"; then :
          else all_ok=0; break
          fi
        done
      fi
      if [ "$all_ok" -eq 1 ]; then cc="$cc $t"; changed=1; fi
    done
  done
  for t in $pend; do
    in_list "$t" "$cc" && return 1        # some pending task can still complete
  done
  return 0                                # unsatisfiable remainder
}

# Top-level classifier. HOLD when admissions are suppressed as policy (R8
# drain-down / R8a tournament) — the R9.3 check is deliberately NOT consulted
# under a hold, since free slots are intentional there. Otherwise: ADMIT the
# next task, REPORT an unsatisfiable remainder, or WAIT for in-flight to land.
scheduler_step() { # scheduler_step <dir> <W> <inflight> <hold>
  local dir="$1" W="$2" inflight="$3" hold="$4" n
  if [ "$hold" = "1" ]; then echo "HOLD"; return; fi
  n="$(next_admissible "$dir" "$W" "$inflight")"
  if [ -n "$n" ]; then echo "ADMIT $n"; return; fi
  if unsatisfiable_remainder "$dir" "$inflight"; then echo "REPORT"; return; fi
  echo "WAIT"
}

# R4 merge-time Touch enforcement: a landing branch's actual changed paths must
# be a subset of the task's declared Touch list, plus its own task file, plus
# the spec's evidence dir. Any path outside that set is a merge failure (the
# slot-machine trigger), never a silent merge.
merge_check() { # merge_check <touch> <taskfile> <evidence_dir> <actual_path...>
  local touch="$1" taskfile="$2" evdir="$3"; shift 3
  local p t ok bad=""
  for p in "$@"; do
    ok=0
    for t in $touch; do [ "$p" = "$t" ] && ok=1; done
    [ "$p" = "$taskfile" ] && ok=1
    case "$p" in "$evdir"/*) ok=1;; esac
    [ "$ok" -eq 1 ] || bad="$bad $p"
  done
  if [ -n "${bad// }" ]; then echo "MERGE_REJECT:$bad"; return 1; fi
  echo "MERGE_OK"
}

# --------------------------------------------------------------------------- #
# (a) Admission order + window cap under W=3: four pairwise-disjoint tasks on   #
# one Group: line. The window fills to exactly 3 in task order; the 4th waits.  #
# --------------------------------------------------------------------------- #
case_a() {
  case_fail=0
  local dir="$TMP/case-a"
  mktask "$dir" 01 alpha pending none "p1"
  mktask "$dir" 02 beta  pending none "p2"
  mktask "$dir" 03 gamma pending none "p3"
  mktask "$dir" 04 delta pending none "p4"
  GRP=("01 02 03 04")

  local inflight="" admitted="" n
  while :; do
    n="$(next_admissible "$dir" 3 "$inflight")"
    [ -n "$n" ] || break
    set_status "$(taskfile "$dir" "$n")" in-progress
    inflight="$inflight $n"
    admitted="$admitted $n"
  done

  assert_eq "(a) window fills in task order, capped at W=3" \
    "01 02 03" "$(echo $admitted)"
  assert_eq "(a) exactly three live workers, not fewer" \
    3 "$(set -- $inflight; echo $#)"
  assert_not "(a) fourth task refused while window is full" \
    admissible "$dir" 04 3 "$inflight"
  report_case a "admission order and window cap"
}

# --------------------------------------------------------------------------- #
# (b) Touch-overlap refusal: two otherwise-eligible tasks share a path; only    #
# one admits. The refused task is not starved — it admits once the first lands. #
# --------------------------------------------------------------------------- #
case_b() {
  case_fail=0
  local dir="$TMP/case-b"
  mktask "$dir" 01 alpha pending none "a.txt b.txt"
  mktask "$dir" 02 beta  pending none "b.txt c.txt"
  GRP=("01 02")

  local first
  first="$(next_admissible "$dir" 3 "")"
  assert_eq "(b) lowest-numbered eligible task admits first" 01 "$first"
  set_status "$(taskfile "$dir" 01)" in-progress

  assert_eq "(b) Touch-overlapping sibling refused while claim held" \
    "" "$(next_admissible "$dir" 3 "01")"

  set_status "$(taskfile "$dir" 01)" done
  assert_eq "(b) refused task admits once the overlap clears (not starved)" \
    02 "$(next_admissible "$dir" 3 "")"
  report_case b "Touch-overlap refusal"
}

# --------------------------------------------------------------------------- #
# (c) No-group task runs solo: refused while the window is non-empty, admitted  #
# once it is empty, and admits nothing alongside it.                            #
# --------------------------------------------------------------------------- #
case_c() {
  case_fail=0
  local dir="$TMP/case-c"
  mktask "$dir" 01 alpha pending none "p1"
  mktask "$dir" 02 beta  pending none "p2"
  mktask "$dir" 03 solo  pending none "p3"
  GRP=("01 02")   # 03 is named on no Group: line

  assert_not "(c) no-group task refused while the window is non-empty" \
    admissible "$dir" 03 3 "01"
  assert "(c) no-group task admissible once the window is empty" \
    admissible "$dir" 03 3 ""

  set_status "$(taskfile "$dir" 03)" in-progress
  assert_not "(c) nothing admits alongside a running no-group task" \
    admissible "$dir" 01 3 "03"
  report_case c "no-group task runs solo"
}

# --------------------------------------------------------------------------- #
# (d) Depends on: cycle terminates with a report (R9.3), not a hang. A          #
# dependency-broken variant proves the report fires only on true               #
# unsatisfiability, not whenever admission is momentarily empty.                #
# --------------------------------------------------------------------------- #
case_d() {
  case_fail=0
  local dir="$TMP/case-d"
  mktask "$dir" 01 alpha pending 02 "x"
  mktask "$dir" 02 beta  pending 01 "y"
  GRP=()

  assert_eq "(d) mutual-dependency cycle admits nothing" \
    "" "$(next_admissible "$dir" 3 "")"
  assert_eq "(d) unsatisfiable remainder routes to a report, not a hang" \
    "REPORT" "$(scheduler_step "$dir" 3 "" 0)"

  local dir2="$TMP/case-d2"
  mktask "$dir2" 01 alpha pending none "x"
  mktask "$dir2" 02 beta  pending 01   "y"
  assert_eq "(d) a satisfiable queue admits instead of reporting" \
    "ADMIT 01" "$(scheduler_step "$dir2" 3 "" 0)"
  report_case d "dependency cycle terminates with a report"
}

# --------------------------------------------------------------------------- #
# (e) Zombie-claimed Touch blocks without starving. A committed in-progress     #
# task with no live window slot (a suspected zombie) whose Touch overlaps a     #
# pending task blocks that task with a "blocked by suspected zombie" report; a  #
# Touch-disjoint pending task admits normally.                                  #
# --------------------------------------------------------------------------- #
case_e() {
  case_fail=0
  local dir="$TMP/case-e"
  mktask "$dir" 01 overlap  pending     none "shared.txt other.txt"
  mktask "$dir" 02 disjoint pending     none "clear.txt"
  mktask "$dir" 90 zombie   in-progress none "shared.txt"
  GRP=()
  # inflight is empty: the zombie holds no live slot, so the window is "empty"
  # (R1: zero live in-flight workers), yet its Status:in-progress claim persists.

  assert_not "(e) pending task overlapping a zombie's claim is refused" \
    admissible "$dir" 01 3 ""
  assert_eq "(e) refusal surfaces the suspected zombie, not a silent stall" \
    "blocked by suspected zombie 90" "$(zombie_block_report "$dir" 01 "")"
  assert_eq "(e) a Touch-disjoint task admits, not starved behind the zombie" \
    02 "$(next_admissible "$dir" 3 "")"
  report_case e "zombie-claimed Touch blocks without starving"
}

# --------------------------------------------------------------------------- #
# (f) Admission held during a simulated tournament (R8a): free window slots and #
# an eligible task, yet no admission occurs while the tournament flag is open;  #
# admission resumes once it clears. A hold is never mistaken for R9.3.          #
# --------------------------------------------------------------------------- #
case_f() {
  case_fail=0
  local dir="$TMP/case-f"
  mktask "$dir" 01 alpha pending none "p1"
  mktask "$dir" 02 beta  pending none "p2"
  GRP=("01 02")

  assert "(f) a window slot is free and a task is eligible" \
    admissible "$dir" 01 3 ""
  assert_eq "(f) tournament hold suppresses admission despite free slots" \
    "HOLD" "$(scheduler_step "$dir" 3 "" 1)"
  assert_eq "(f) admission resumes once the tournament flag clears" \
    "ADMIT 01" "$(scheduler_step "$dir" 3 "" 0)"
  report_case f "admission held during a tournament"
}

# --------------------------------------------------------------------------- #
# (g) Merge-time Touch violation is rejected (R4). A branch whose actual changed #
# paths stay within Touch + task file + evidence dir merges; one whose paths     #
# stray outside is a merge failure naming the offending path.                    #
# --------------------------------------------------------------------------- #
case_g() {
  case_fail=0
  local touch="src/foo.ts"
  local tf="specs/demo/tasks/01-foo.md"
  local ev="specs/demo/evidence"

  assert "(g) a branch within Touch + task file + evidence merges cleanly" \
    merge_check "$touch" "$tf" "$ev" \
      src/foo.ts specs/demo/tasks/01-foo.md specs/demo/evidence/01-foo.md
  assert_not "(g) a path outside the allowed set is a merge failure" \
    merge_check "$touch" "$tf" "$ev" src/foo.ts src/OUTSIDE.ts

  local msg
  msg="$(merge_check "$touch" "$tf" "$ev" src/foo.ts src/OUTSIDE.ts)"
  case "$msg" in
    *"src/OUTSIDE.ts"*) note_pass;;
    *) note_fail "(g) merge failure names the offending path";;
  esac
  report_case g "merge-time Touch violation rejected"
}

case_a
case_b
case_c
case_d
case_e
case_f
case_g

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
