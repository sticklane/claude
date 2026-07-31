#!/usr/bin/env bash
# Tests for bin/drain-release-worktrees (agentic-v50x).
#
# Every case builds a throwaway git repository with real worktrees under a
# temporary directory, so nothing here touches this repository's own worktrees.
set -u

TOOLKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="$TOOLKIT_DIR/bin/drain-release-worktrees"

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
nonempty() { [ -n "$1" ] && echo 0 || echo 1; }
present() { [ -e "$1" ] && echo 0 || echo 1; }
absent() { [ -e "$1" ] && echo 1 || echo 0; }
ref_present() { git -C "$1" rev-parse --verify --quiet "$2" >/dev/null 2>&1 && echo 0 || echo 1; }
ref_absent() { git -C "$1" rev-parse --verify --quiet "$2" >/dev/null 2>&1 && echo 1 || echo 0; }

TMP="$(mktemp -d)"
trap 'chmod -R u+w "$TMP" 2>/dev/null || true; rm -rf "$TMP"' EXIT

new_repo() { # new_repo <path>
  local repo="$1"
  mkdir -p "$repo"
  git -C "$repo" init -q -b main
  git -C "$repo" config user.email drain-release@example.invalid
  git -C "$repo" config user.name "Drain Release Test"
  printf 'base\n' > "$repo/file.txt"
  git -C "$repo" add -A
  git -C "$repo" commit -qm base
}

commit_in() { # commit_in <worktree> <content> <message>
  printf '%s\n' "$2" > "$1/file.txt"
  git -C "$1" add -A
  git -C "$1" commit -qm "$3"
}

run_release() { # run_release <repo> [args…]
  local repo="$1"; shift
  (cd "$repo" && bash "$RELEASE" "$@" 2>&1)
}

# Ages every mtime the shared idle probe reads, so a fixture stands in for a
# worktree no session has touched. Without this a just-built fixture looks
# live to the default idle window.
backdate_worktree() { # backdate_worktree <worktree>
  local wt="$1" gitdir stamp=200001010000
  gitdir="$(git -C "$wt" rev-parse --absolute-git-dir)"
  touch -t "$stamp" "$gitdir/HEAD" "$gitdir/index" "$wt/.git" 2>/dev/null || true
  touch -t "$stamp" "$gitdir" "$wt" 2>/dev/null || true
}

# --- a merged branch carrying TWO worktrees releases both --------------------
# This is the duplicate that bin/janitor refuses with "branch checked out by
# another worktree", which is why drain needs its own release step.
DUP="$TMP/duplicate"
new_repo "$DUP"
DUP_WT="$DUP/.claude/worktrees"
git -C "$DUP" worktree add -q -b drain/agentic-1111 "$DUP_WT/first" main
commit_in "$DUP_WT/first" "worker output" "worker output"
git -C "$DUP" worktree add -q --detach "$DUP_WT/second" main
git -C "$DUP_WT/second" switch -q --ignore-other-worktrees drain/agentic-1111
git -C "$DUP" merge -q --no-ff -m "merge worker branch" drain/agentic-1111
backdate_worktree "$DUP_WT/first"
backdate_worktree "$DUP_WT/second"

# No flags: the invocation /drain's SKILL.md step 3 prescribes.
DUP_OUT="$(run_release "$DUP" drain/agentic-1111)"; DUP_RC=$?
assert "duplicate worktrees: release exits 0" "$(is "$DUP_RC" 0)"
assert "duplicate worktrees: bin/drain-release-worktrees removes the first worktree on the branch" \
  "$(absent "$DUP_WT/first")"
assert "duplicate worktrees: bin/drain-release-worktrees removes the second worktree on the same branch in one invocation" \
  "$(absent "$DUP_WT/second")"
assert "merged branch: deleted once every worktree carrying it is released" \
  "$(ref_absent "$DUP" refs/heads/drain/agentic-1111)"

# --- unique content is salvaged, and an unmerged branch survives -------------
UNIQ="$TMP/unique"
new_repo "$UNIQ"
UNIQ_WT="$UNIQ/.claude/worktrees"
git -C "$UNIQ" worktree add -q -b drain/agentic-2222 "$UNIQ_WT/only" main
commit_in "$UNIQ_WT/only" "committed work" "committed work"
printf 'unique-payload\n' > "$UNIQ_WT/only/file.txt"
printf 'untracked-payload\n' > "$UNIQ_WT/only/extra.txt"
backdate_worktree "$UNIQ_WT/only"

UNIQ_OUT="$(run_release "$UNIQ" drain/agentic-2222)"; UNIQ_RC=$?
UNIQ_REF="$(git -C "$UNIQ" for-each-ref --format='%(refname)' 'refs/heads/salvage/*' | head -n 1)"
assert "unique content: release exits 0" "$(is "$UNIQ_RC" 0)"
assert "unique content: bin/drain-release-worktrees writes a salvage/ ref" "$(nonempty "$UNIQ_REF")"
assert "unique content: tracked bytes are recoverable from the salvage ref" \
  "$(is "$(git -C "$UNIQ" show "${UNIQ_REF:-refs/heads/main}:file.txt" 2>/dev/null)" "unique-payload")"
assert "unique content: untracked bytes are recoverable from the salvage ref" \
  "$(is "$(git -C "$UNIQ" show "${UNIQ_REF:-refs/heads/main}:extra.txt" 2>/dev/null)" "untracked-payload")"
assert "unique content: the worktree directory is removed after salvage" "$(absent "$UNIQ_WT/only")"
assert "unmerged branch: retained as the archive even though its worktree is released" \
  "$(ref_present "$UNIQ" refs/heads/drain/agentic-2222)"

# --- salvage happens BEFORE removal -----------------------------------------
# A git shim fails every `worktree remove`, so a salvage ref that exists while
# the directory is still present proves the ordering rather than inferring it.
SHIM="$TMP/shim"
mkdir -p "$SHIM"
REAL_GIT="$(command -v git)"
cat > "$SHIM/git" <<EOF
#!/usr/bin/env bash
case " \$* " in
  *" worktree remove "*) echo "shim: worktree remove refused" >&2; exit 1 ;;
esac
exec "$REAL_GIT" "\$@"
EOF
chmod +x "$SHIM/git"

ORDER="$TMP/order"
new_repo "$ORDER"
ORDER_WT="$ORDER/.claude/worktrees"
git -C "$ORDER" worktree add -q -b drain/agentic-4444 "$ORDER_WT/only" main
commit_in "$ORDER_WT/only" "committed work" "committed work"
printf 'unsalvaged-payload\n' > "$ORDER_WT/only/file.txt"
backdate_worktree "$ORDER_WT/only"
ORDER_OUT="$(cd "$ORDER" && PATH="$SHIM:$PATH" bash "$RELEASE" drain/agentic-4444 2>&1)"; ORDER_RC=$?
ORDER_REF="$(git -C "$ORDER" for-each-ref --format='%(refname)' 'refs/heads/salvage/*' | head -n 1)"
assert "salvage ordering: release exits 0 when a removal fails" "$(is "$ORDER_RC" 0)"
assert "salvage ordering: the salvage ref exists while the directory is still present" \
  "$(nonempty "$ORDER_REF")"
assert "salvage ordering: the directory survives a failed removal" "$(present "$ORDER_WT/only")"
assert "salvage ordering: salvaged bytes match the unremoved worktree" \
  "$(is "$(git -C "$ORDER" show "${ORDER_REF:-refs/heads/main}:file.txt" 2>/dev/null)" "unsalvaged-payload")"

# --- the shared checkout is never released ----------------------------------
SHARED="$TMP/shared"
new_repo "$SHARED"
SHARED_OUT="$(run_release "$SHARED" main)"; SHARED_RC=$?
assert "shared checkout: release exits 0" "$(is "$SHARED_RC" 0)"
assert "shared checkout: the repository root worktree is never removed" "$(present "$SHARED/file.txt")"
assert "shared checkout: its branch is never deleted while it holds it" \
  "$(ref_present "$SHARED" refs/heads/main)"

# --- a worktree a live session is using is never released --------------------
LIVE="$TMP/live"
new_repo "$LIVE"
LIVE_WT="$LIVE/.claude/worktrees"
git -C "$LIVE" worktree add -q -b drain/agentic-3333 "$LIVE_WT/busy" main
commit_in "$LIVE_WT/busy" "live worker output" "live worker output"
git -C "$LIVE" merge -q --no-ff -m "merge live branch" drain/agentic-3333
touch "$LIVE_WT/busy"
# No flags again: the protection has to hold in the shipped invocation, not
# only when a caller remembers to ask for it.
LIVE_OUT="$(run_release "$LIVE" drain/agentic-3333)"; LIVE_RC=$?
assert "live session: release exits 0" "$(is "$LIVE_RC" 0)"
assert "live session: an active worktree is never removed by the default invocation" \
  "$(present "$LIVE_WT/busy")"
assert "live session: the branch is retained while a live worktree still holds it" \
  "$(ref_present "$LIVE" refs/heads/drain/agentic-3333)"

OPT_OUT="$(run_release "$LIVE" --idle-minutes 0 drain/agentic-3333)"; OPT_RC=$?
assert "idle opt-out: --idle-minutes 0 exits 0" "$(is "$OPT_RC" 0)"
assert "idle opt-out: --idle-minutes 0 releases the worktree the default protected" \
  "$(absent "$LIVE_WT/busy")"

# --- a flag missing its operand errors instead of looping --------------------
MISSING_OUT="$(cd "$LIVE" && timeout 10 bash "$RELEASE" --idle-minutes 2>&1)"; MISSING_RC=$?
assert "missing operand: --idle-minutes without a value exits with the usage code" \
  "$(is "$MISSING_RC" 64)"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
