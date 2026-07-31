# shellcheck shell=bash
#
# Shared worktree classification. bin/janitor and bin/drain-release-worktrees
# both source this file, so the three-way content rule (clean /
# reconstructible / unique), the salvage-before-remove step, the idle probe
# that protects a live session, and default-branch merge detection exist in
# exactly one place. A second copy of any of these is a defect.

worktree_detect_base_branch() { # <repo_dir>
  local repo="$1" base_ref candidate
  if base_ref=$(git -C "$repo" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null); then
    echo "${base_ref#refs/remotes/}"
    return 0
  fi
  for candidate in origin/main origin/master main master; do
    if git -C "$repo" rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

# 0 = merged into base, 1 = ahead of base, 2 = undetermined.
worktree_branch_merged() { # <repo_dir> <base_branch> <branch_ref>
  local repo="$1" base="$2" branch_ref="$3" ahead_count

  if [ -z "$base" ]; then
    return 2
  fi
  if ! git -C "$repo" rev-parse --verify --quiet "$branch_ref" >/dev/null 2>&1; then
    return 2
  fi
  if ! git -C "$repo" rev-parse --verify --quiet "$base" >/dev/null 2>&1; then
    return 2
  fi

  ahead_count="$(git -C "$repo" rev-list --left-right --count "$base...$branch_ref" 2>/dev/null | awk '{print $2}' || true)"
  if [ -z "$ahead_count" ]; then
    return 2
  fi
  if [ "$ahead_count" -eq 0 ]; then
    return 0
  fi
  return 1
}

worktree_recently_active() { # <worktree_path> <idle_minutes>
  python3 - "$1" "$2" <<'PY'
import os
import sys
import time

path, minutes = sys.argv[1], float(sys.argv[2])
gitlink = os.path.join(path, ".git")
targets = [path, gitlink]
gitdir = None
if os.path.isdir(gitlink):
  gitdir = gitlink
elif os.path.isfile(gitlink):
  try:
    with open(gitlink, encoding="utf-8") as handle:
      for line in handle:
        if line.startswith("gitdir:"):
          gitdir = line.split(":", 1)[1].strip()
          break
  except OSError:
    gitdir = None
if gitdir:
  if not os.path.isabs(gitdir):
    gitdir = os.path.join(path, gitdir)
  targets += [gitdir, os.path.join(gitdir, "HEAD"), os.path.join(gitdir, "index")]
newest = 0.0
for target in targets:
  try:
    newest = max(newest, os.stat(target).st_mtime)
  except OSError:
    continue
raise SystemExit(0 if (time.time() - newest) < minutes * 60.0 else 1)
PY
}

# Prints clean, reconstructible, or unique.
worktree_content_state() { # <worktree_path> <rev> <history_scan_limit>
  local wt_path="$1" rev="$2" limit="$3" commit
  if [ -z "$(git -C "$wt_path" status --porcelain)" ]; then
    echo clean
    return
  fi
  if [ -z "$(git -C "$wt_path" ls-files --others --exclude-standard)" ]; then
    while IFS= read -r commit; do
      [ -n "$commit" ] || continue
      if git -C "$wt_path" diff --quiet "$commit" 2>/dev/null; then
        echo reconstructible
        return
      fi
    done < <(git -C "$wt_path" rev-list --max-count="$limit" "$rev" 2>/dev/null)
  fi
  echo unique
}

# Prints the created ref name; nonzero exit means nothing was salvaged.
worktree_salvage_content() { # <worktree_path> <label> <parent_rev>
  local wt_path="$1" label="$2" parent="$3" index tree commit
  index="$(mktemp -u)"
  GIT_INDEX_FILE="$index" git -C "$wt_path" add -A >/dev/null 2>&1 || { rm -f "$index"; return 1; }
  tree="$(GIT_INDEX_FILE="$index" git -C "$wt_path" write-tree 2>/dev/null)"
  rm -f "$index"
  [ -n "$tree" ] || return 1
  if [ -n "$parent" ] && git -C "$wt_path" rev-parse --verify --quiet "$parent" >/dev/null 2>&1; then
    commit="$(git -C "$wt_path" commit-tree "$tree" -p "$parent" -m "janitor salvage of $label" 2>/dev/null)"
  else
    commit="$(git -C "$wt_path" commit-tree "$tree" -m "janitor salvage of $label" 2>/dev/null)"
  fi
  [ -n "$commit" ] || return 1
  git -C "$wt_path" branch --force "salvage/$label" "$commit" >/dev/null 2>&1 || return 1
  printf 'salvage/%s\n' "$label"
}
