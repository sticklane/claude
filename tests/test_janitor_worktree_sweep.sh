#!/usr/bin/env bash
# Tests for bin/janitor's worktree sweep (agentic-zz3k).
#
# The sweep deletes directories, so every removal path is exercised against
# throwaway git repositories with real worktrees under a temporary directory.
# `bd` is stubbed on PATH so issue status is fixture data rather than the
# machine's tracker.
set -u

TOOLKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JANITOR="$TOOLKIT_DIR/bin/janitor"

pass=0
fail=0
assert() { # assert <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1)); printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1)); printf 'FAIL - %s\n' "$1"
  fi
}
is() { [ "$1" = "$2" ] && echo 0 || echo 1; }
present() { [ -e "$1" ] && echo 0 || echo 1; }
absent() { [ -e "$1" ] && echo 1 || echo 0; }
ref_present() { git -C "$1" rev-parse --verify --quiet "$2" >/dev/null 2>&1 && echo 0 || echo 1; }
reachable_from_a_branch() {
  [ -n "$(git -C "$1" branch --contains "$2" 2>/dev/null)" ] && echo 0 || echo 1
}

TMP="$(mktemp -d)"
STUB="$TMP/stub-bin"
STATE="$TMP/bd-state"
mkdir -p "$STUB" "$STATE"
cat > "$STUB/bd" <<'STUB'
#!/usr/bin/env bash
state="${JANITOR_TEST_BD_STATE:-}"
case "$*" in
  *"--status in_progress"*)
    [ -f "$state/in_progress.json" ] && cat "$state/in_progress.json" || echo '[]' ;;
  *"--status closed"*)
    [ -f "$state/closed.json" ] && cat "$state/closed.json" || echo '[]' ;;
  *) echo '[]' ;;
esac
STUB
chmod 755 "$STUB/bd"
PATH="$STUB:$PATH"
export PATH
export JANITOR_TEST_BD_STATE="$STATE"
printf '%s\n' '[{"id":"agentic-4444"},{"id":"agentic-5555.6"}]' > "$STATE/in_progress.json"
printf '%s\n' '[{"id":"agentic-1111"},{"id":"agentic-2222"},{"id":"agentic-3333"},{"id":"agentic-5555"},{"id":"agentic-6666"}]' \
  > "$STATE/closed.json"

cleanup() { chmod -R u+w "$TMP" 2>/dev/null; rm -rf "$TMP" "${SHARED:-$TMP/none}"; }
trap cleanup EXIT

new_repo() { # new_repo <dir>
  local d="$1"
  mkdir -p "$d/.beads"
  git -C "$d" init -q -b main
  git -C "$d" config user.email test@example.invalid
  git -C "$d" config user.name "Janitor Test"
  printf 'base\n' > "$d/file.txt"
  git -C "$d" add -A
  git -C "$d" commit -qm base
}

commit_in() { # commit_in <worktree> <content> <message>
  printf '%s\n' "$2" > "$1/file.txt"
  git -C "$1" add -A
  git -C "$1" commit -qm "$3"
}

run_janitor() { # run_janitor <repo> [args…]
  local repo="$1"; shift
  (cd "$repo" && bash "$JANITOR" --scope drain "$@" 2>&1)
}

# --- fixture: four worktrees under <repo>/.claude/worktrees ------------------
REPO="$TMP/repo"
new_repo "$REPO"
WT="$REPO/.claude/worktrees"

git -C "$REPO" worktree add -q -b drain/agentic-1111 "$WT/clean-closed" main
commit_in "$WT/clean-closed" "clean-closed work" "clean-closed work"

git -C "$REPO" worktree add -q -b drain/agentic-2222 "$WT/reconstructible" main
commit_in "$WT/reconstructible" "second revision" "second revision"
printf 'base\n' > "$WT/reconstructible/file.txt"

git -C "$REPO" worktree add -q -b drain/agentic-3333 "$WT/unique" main
printf 'unique-payload\n' > "$WT/unique/file.txt"

git -C "$REPO" worktree add -q --detach "$WT/detached" main
commit_in "$WT/detached" "detached work" "detached work"
DETACHED_SHA="$(git -C "$WT/detached" rev-parse HEAD)"

git -C "$REPO" worktree add -q -b drain/agentic-4444 "$WT/in-progress" main
commit_in "$WT/in-progress" "live worker output" "live worker output"

git -C "$REPO" worktree add -q -b drain/agentic-5555.6-codex "$WT/open-child" main
commit_in "$WT/open-child" "open child output" "open child output"

# --- dry run removes nothing -------------------------------------------------
DRY="$(run_janitor "$REPO" --dry-run)"; DRY_RC=$?
assert "dry run: exits 0" "$(is "$DRY_RC" 0)"
assert "dry run: clean closed-issue worktree still on disk" "$(present "$WT/clean-closed")"
assert "dry run: reconstructible worktree still on disk" "$(present "$WT/reconstructible")"
assert "dry run: unique-content worktree still on disk" "$(present "$WT/unique")"
assert "dry run: detached worktree still on disk" "$(present "$WT/detached")"
assert "dry run: no salvage ref created" \
  "$(ref_present "$REPO" refs/heads/salvage/agentic-3333 >/dev/null; [ -z "$(git -C "$REPO" for-each-ref --format='%(refname)' refs/heads/salvage 2>/dev/null)" ] && echo 0 || echo 1)"

# --- apply -------------------------------------------------------------------
OUT="$(run_janitor "$REPO" --apply)"; RC=$?
assert "apply: exits 0" "$(is "$RC" 0)"

# A2 — a CLEAN worktree whose issue is CLOSED is reclaimed, branch survives.
assert "closed issue + clean worktree: directory removed" "$(absent "$WT/clean-closed")"
assert "closed issue + clean worktree: branch kept as the archive" \
  "$(ref_present "$REPO" refs/heads/drain/agentic-1111)"

# A3 — a DIRTY worktree whose content equals an earlier commit on its branch.
assert "dirty but reconstructible: directory removed" "$(absent "$WT/reconstructible")"
assert "dirty but reconstructible: branch still exists afterwards" \
  "$(ref_present "$REPO" refs/heads/drain/agentic-2222)"

# A4 — a DIRTY worktree matching no commit is salvaged before removal.
assert "unique content: salvage ref created" \
  "$(ref_present "$REPO" refs/heads/salvage/agentic-3333)"
SALVAGED="$(git -C "$REPO" show salvage/agentic-3333:file.txt 2>/dev/null || true)"
assert "unique content: salvaged bytes recoverable from the ref" \
  "$(is "$SALVAGED" "unique-payload")"
assert "unique content: directory removed only after salvage" "$(absent "$WT/unique")"

# A5 — a DETACHED-HEAD worktree does not lose its commits.
if [ -e "$WT/detached" ]; then
  assert "detached HEAD: worktree left alone and reported" \
    "$(printf '%s' "$OUT" | grep -qi 'detach' && echo 0 || echo 1)"
else
  assert "detached HEAD: commits reachable from a branch after removal" \
    "$(reachable_from_a_branch "$REPO" "$DETACHED_SHA")"
fi

# A live session's detached isolation worktree is never force-removed.
assert "detached HEAD: recently active worktree survives the sweep" \
  "$(present "$WT/detached")"

# The in-progress guard is the only liveness protection left on branch
# worktrees, so both of its shapes are exercised.
assert "in-progress issue: worktree survives the sweep" "$(present "$WT/in-progress")"
assert "closed parent epic, in-progress sub-issue: worktree survives the sweep" \
  "$(present "$WT/open-child")"

# A6 — the shared checkout is never a removal candidate.
SHARED="$(mktemp -d /tmp/janitor-shared.XXXXXX)"
new_repo "$SHARED"
git -C "$SHARED" checkout -q -b drain/agentic-6666
SHARED_OUT="$(run_janitor "$SHARED" --apply)"; SHARED_RC=$?
assert "shared checkout: janitor exits 0" "$(is "$SHARED_RC" 0)"
assert "shared checkout: repository root not removed" "$(present "$SHARED/file.txt")"
assert "shared checkout: no salvage ref for the root checkout" \
  "$([ -z "$(git -C "$SHARED" for-each-ref --format='%(refname)' refs/heads/salvage 2>/dev/null)" ] && echo 0 || echo 1)"

printf '\n%s: %d passed, %d failed\n' "$(basename "$0")" "$pass" "$fail"
[ "$fail" -eq 0 ]
