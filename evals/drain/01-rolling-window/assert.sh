#!/usr/bin/env bash
# Grades the /drain run over the rolling-window fixture. CWD is $EVAL_DIR;
# exit 0 = pass, non-zero with output explaining what failed. Checks four
# things, mechanically, on the resulting git history and task-file statuses:
#   1. every specs/demo/tasks/NN-*.md ended Status: done;
#   2. the tasks landed as a rolling window of distinct per-task admissions,
#      not one all-in-one-commit barrier: no single commit flips >=2 task
#      files' Status to done, and there are >=2 distinct landings;
#   3. no landing's changed paths escaped that task's Touch: list (plus its
#      own task file, the spec, evidence/, and drain/runner infra);
#   4. every done task has an identifiable landing — so check 3 can never
#      silently no-op (a task with no landing fails loudly).
# A task's landing is identified by its Status: done-flip commit (the first
# commit reachable from HEAD whose blob has `Status: done`), never by a merge
# commit or a free-text subject — neither of which drain guarantees, and a
# fast-forwarded landing produces no merge commit at all. The landed range
# feeding the Touch check runs from the landing's fork-point (the closest
# prior landing that is its ancestor, else the repo's root/base commit)
# through the done-flip commit, so a violation in any branch commit is caught,
# not only one in the commit that happens to flip Status. Failure output stays
# under ~10 lines: one `ASSERT FAIL:` per broken check. bash 3.2 safe (no
# associative arrays: the runner invokes `bash assert.sh` and macOS ships 3.2).
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
nn_of() { basename "$1" | sed 's/^\([0-9][0-9]\)-.*/\1/'; }

shopt -s nullglob
tasks=(specs/demo/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -ge 2 ] || fail "expected >=2 specs/demo/tasks/NN-*.md files, found ${#tasks[@]}"

for t in "${tasks[@]}"; do
  grep -q '^Status: done' "$t" || fail "$t did not end Status: done"
done

# base = the repo's root commit (all task files pending here). Fork-point
# fallback when a landing didn't branch off a prior landing.
base=$(git rev-list --max-parents=0 HEAD | head -1)

# For each task, its done-flip commit: the earliest commit reachable from HEAD
# that touched the task file and whose blob reads `Status: done`. Parallel to
# `tasks` (bash 3.2: indexed arrays only).
flips=()
for t in "${tasks[@]}"; do
  flip=""
  for sha in $(git log --format=%H --reverse HEAD -- "$t"); do
    if git show "$sha:$t" 2>/dev/null | grep -q '^Status: done'; then
      flip="$sha"; break
    fi
  done
  # Check 4: a done task with no identifiable landing fails loudly.
  [ -n "$flip" ] || fail "task $(nn_of "$t") ended done but no commit introduced its landing"
  flips+=("$flip")
done

# Check 2 (barrier): a single commit that is the done-flip for >=2 task files
# is an all-in-one-commit barrier, not a rolling-window admission.
i=0
while [ "$i" -lt "${#tasks[@]}" ]; do
  j=$((i + 1))
  while [ "$j" -lt "${#tasks[@]}" ]; do
    if [ "${flips[$i]}" = "${flips[$j]}" ]; then
      fail "commit ${flips[$i]} flips task $(nn_of "${tasks[$i]}") and task $(nn_of "${tasks[$j]}") at once (all-in-one barrier)"
    fi
    j=$((j + 1))
  done
  i=$((i + 1))
done

# Distinct landings == number of tasks once the barrier check passes. Rolling
# window means >=2 separate admissions. No merge-commit floor: a fully
# fast-forwarded history (zero merge commits) still passes.
landings=${#tasks[@]}
[ "$landings" -ge 2 ] || fail "expected >=2 distinct task landings (rolling window), found $landings"

# Check 3 (Touch): diff each landing's FULL range fork-point..done-flip against
# the task's Touch list. Fork-point = the closest other-task done-flip that is
# an ancestor of this landing, else base.
i=0
while [ "$i" -lt "${#tasks[@]}" ]; do
  t="${tasks[$i]}"
  d="${flips[$i]}"
  nn=$(nn_of "$t")
  start="$base"
  j=0
  while [ "$j" -lt "${#tasks[@]}" ]; do
    if [ "$j" -ne "$i" ]; then
      other="${flips[$j]}"
      # keep `other` if it is an ancestor of this landing and strictly closer
      # to it than the current start (start is always an ancestor of `other`).
      if git merge-base --is-ancestor "$other" "$d" 2>/dev/null \
         && [ "$other" != "$start" ] \
         && git merge-base --is-ancestor "$start" "$other" 2>/dev/null; then
        start="$other"
      fi
    fi
    j=$((j + 1))
  done
  changed=$(git diff --name-only "$start" "$d")
  touch_paths=$(grep '^Touch:' "$t" | sed 's/^Touch:[[:space:]]*//' | tr ',' '\n' | sed 's/[[:space:]]//g' | grep -v '^$' || true)
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$p" in
      "$t") continue ;;
      .claude/*|.gitignore|specs/demo/SPEC.md|specs/demo/evidence/*|specs/demo/DRAIN-*) continue ;;
    esac
    printf '%s\n' "$touch_paths" | grep -qxF "$p" \
      || fail "task $nn landing changed $p, outside its Touch [$(printf '%s' "$touch_paths" | tr '\n' ' ')]"
  done < <(printf '%s\n' "$changed")
  i=$((i + 1))
done

echo "assert: all checks passed (${#tasks[@]} tasks done, $landings distinct landings, per-task Touch enforced)"
