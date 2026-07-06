#!/usr/bin/env bash
# Grades the /drain run over the rolling-window fixture. CWD is $EVAL_DIR;
# exit 0 = pass, non-zero with output explaining what failed. Checks four
# things, mechanically, on the resulting git history and task-file statuses:
#   1. every specs/demo/tasks/NN-*.md ended Status: done;
#   2. the git log holds more than one merge commit (the tasks landed via a
#      rolling window of per-task merges, not one all-in-one-commit barrier);
#   3. no landing merge's changed paths escaped that task's Touch: list
#      (plus its own task file, the spec, evidence/, and drain/runner infra);
#   4. every done task was landed by exactly one merge — so check 3 can never
#      silently no-op (a task with no landing merge fails loudly).
# A landing merge is identified by the task-file done-flip it carries (a
# drain-contract invariant), never by the free-text commit subject, which
# drain does not guarantee. Failure output stays under ~10 lines: one
# `ASSERT FAIL:` per broken check.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
nn_of() { basename "$1" | sed 's/^\([0-9][0-9]\)-.*/\1/'; }

shopt -s nullglob
tasks=(specs/demo/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -ge 2 ] || fail "expected >=2 specs/demo/tasks/NN-*.md files, found ${#tasks[@]}"

for t in "${tasks[@]}"; do
  grep -q '^Status: done' "$t" || fail "$t did not end Status: done"
done

merges=$(git rev-list --merges --count HEAD)
[ "$merges" -ge 2 ] || fail "expected >1 merge commit (rolling window), found $merges"

# landed: space-delimited list of task numbers seen landing via a merge.
# Plain string, not an associative array — the runner invokes `bash
# assert.sh` and macOS ships bash 3.2, which has no `declare -A`.
landed=" "
for sha in $(git rev-list --merges HEAD); do
  changed=$(git diff --name-only "$sha^1" "$sha")
  merged_tasks=$(printf '%s\n' "$changed" | grep -E '^specs/demo/tasks/[0-9][0-9]-.*\.md$' || true)
  n=$(printf '%s' "$merged_tasks" | grep -c .)
  [ "$n" -eq 0 ] && continue
  [ "$n" -eq 1 ] || fail "merge $sha lands $n task files at once (all-in-one barrier)"
  tf="$merged_tasks"
  nn=$(nn_of "$tf")
  landed="$landed$nn "
  touch_paths=$(grep '^Touch:' "$tf" | sed 's/^Touch:[[:space:]]*//' | tr ',' '\n' | sed 's/[[:space:]]//g' | grep -v '^$' || true)
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$p" in
      "$tf") continue ;;
      .claude/*|.gitignore|specs/demo/SPEC.md|specs/demo/evidence/*|specs/demo/DRAIN-*) continue ;;
    esac
    printf '%s\n' "$touch_paths" | grep -qxF "$p" \
      || fail "task $nn merge changed $p, outside its Touch [$(printf '%s' "$touch_paths" | tr '\n' ' ')]"
  done < <(printf '%s\n' "$changed")
done

for t in "${tasks[@]}"; do
  nn=$(nn_of "$t")
  case "$landed" in
    *" $nn "*) : ;;
    *) fail "task $nn ended done but no merge introduced its landing" ;;
  esac
done

echo "assert: all checks passed (${#tasks[@]} tasks done, $merges merges, per-task Touch enforced)"
