#!/usr/bin/env bash
# Grades the /drain run over the rolling-window fixture. CWD is $EVAL_DIR;
# exit 0 = pass, non-zero with output explaining what failed. Checks four
# things, mechanically, on the resulting git history and task-file statuses:
#   1. every specs/demo/tasks/NN-*.md ended Status: done;
#   2. the tasks landed as a rolling window of per-task landings, not one
#      all-in-one-commit barrier (no single landing flips >=2 task files);
#   3. no landing's full changed range escaped that task's Touch: list (plus
#      its own task file, the spec, evidence/, and drain/runner infra);
#   4. every done task was attributed exactly one landing — so check 3 can
#      never silently no-op (a task with no landing fails loudly).
#
# Landing identification is anchored on each task file's Status done-flip (a
# drain-contract invariant), NOT on the presence of a merge commit. A /drain
# landing is a plain `git merge` with no `--no-ff`, so when a task branch is
# still main's direct descendant at merge time it fast-forwards and produces
# NO merge commit. Keying off merge commits would then undercount landings,
# skip the Touch check, and mis-fire the unlanded loop for that task. Instead
# we walk main's first-parent chain and treat as a landing tip the first
# first-parent commit that brings a task's done-flip into main — the done-flip
# commit itself for a fast-forward, or the merge commit for a real merge. Both
# land identically. The Touch check diffs the FULL landed range
# (prior-landing-tip -> this tip), so a violation anywhere in a multi-commit
# branch (TDD test->feat->refactor) is caught, not just one in the done-flip
# commit. Failure output stays under ~10 lines: one `ASSERT FAIL:` per broken
# check. Plain strings/indexed arrays only — the runner invokes `bash
# assert.sh` and macOS ships bash 3.2 (no `declare -A`).
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }
nn_of() { basename "$1" | sed 's/^\([0-9][0-9]\)-.*/\1/'; }
is_anc() { git merge-base --is-ancestor "$1" "$2" 2>/dev/null; }

shopt -s nullglob
tasks=(specs/demo/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -ge 2 ] || fail "expected >=2 specs/demo/tasks/NN-*.md files, found ${#tasks[@]}"

for t in "${tasks[@]}"; do
  grep -q '^Status: done' "$t" || fail "$t did not end Status: done"
done

# done-flip commit per task (parallel to the tasks array): the earliest commit
# in topo order whose version of the task file already reads `Status: done`.
doneflip=()
for t in "${tasks[@]}"; do
  df=""
  for sha in $(git log --format=%H --topo-order --reverse -- "$t"); do
    if git show "$sha:$t" 2>/dev/null | grep -q '^Status: done'; then
      df="$sha"; break
    fi
  done
  [ -n "$df" ] || fail "task $(nn_of "$t") is Status: done but no commit flips it to done"
  doneflip+=("$df")
done

root=$(git rev-list --max-parents=0 HEAD | tail -1)

# Walk main's first-parent chain oldest->newest. A landing tip is the first
# first-parent commit that brings one or more task done-flips into main
# (ancestor of the tip, not yet of the running base). base advances to each
# landing tip so the next landing's range starts where this one ended.
base="$root"
landed=" "
landings=0
for C in $(git rev-list --first-parent --topo-order --reverse HEAD); do
  [ "$C" = "$root" ] && continue

  flipped_idx=()
  i=0
  for df in "${doneflip[@]}"; do
    if is_anc "$df" "$C" && ! is_anc "$df" "$base"; then
      flipped_idx+=("$i")
    fi
    i=$((i + 1))
  done

  if [ "${#flipped_idx[@]}" -eq 0 ]; then
    # A merge that lands no new done-flip still advances main's tip; a plain
    # non-landing commit mid-branch does not (keep the range base anchored).
    nparents=$(git rev-list --parents -n1 "$C" | wc -w)
    [ "$nparents" -ge 3 ] && base="$C"
    continue
  fi

  [ "${#flipped_idx[@]}" -eq 1 ] \
    || fail "landing $C flips ${#flipped_idx[@]} task files at once (all-in-one barrier, not a rolling-window landing)"

  tf="${tasks[${flipped_idx[0]}]}"
  nn=$(nn_of "$tf")
  changed=$(git diff --name-only "$base" "$C")
  touch_paths=$(grep '^Touch:' "$tf" | sed 's/^Touch:[[:space:]]*//' | tr ',' '\n' | sed 's/[[:space:]]//g' | grep -v '^$' || true)
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$p" in
      "$tf") continue ;;
      .claude/*|.gitignore|specs/demo/SPEC.md|specs/demo/evidence/*|specs/demo/DRAIN-*) continue ;;
    esac
    printf '%s\n' "$touch_paths" | grep -qxF "$p" \
      || fail "task $nn landing changed $p, outside its Touch [$(printf '%s' "$touch_paths" | tr '\n' ' ')]"
  done < <(printf '%s\n' "$changed")

  landed="$landed$nn "
  landings=$((landings + 1))
  base="$C"
done

for t in "${tasks[@]}"; do
  nn=$(nn_of "$t")
  case "$landed" in
    *" $nn "*) : ;;
    *) fail "task $nn ended done but no landing introduced it" ;;
  esac
done

echo "assert: all checks passed (${#tasks[@]} tasks done, $landings rolling-window landings, per-task Touch enforced)"
