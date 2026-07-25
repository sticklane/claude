#!/usr/bin/env bash
# Tests for bin/review-gate, hooks/review-gate/pre-commit and
# bin/install-review-gate — the mechanical gate that blocks `git commit` until
# an adversarial review has been recorded against the diff that commit will
# contain. Every gate assertion drives a REAL `git commit` in a throwaway
# fixture repo and asserts on its exit status and resulting history; nothing
# here simulates a commit. This toolkit's own .git is never touched.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$TOOLKIT_DIR/bin/review-gate"
HOOK="$TOOLKIT_DIR/hooks/review-gate/pre-commit"
INSTALLER="$TOOLKIT_DIR/bin/install-review-gate"
README="$TOOLKIT_DIR/hooks/review-gate/README.md"

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

refute() { # refute <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $desc (command unexpectedly succeeded)" >&2
  else
    pass=$((pass + 1))
  fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

assert_ne() { # assert_ne <description> <unexpected> <actual>
  local desc="$1" unexpected="$2" actual="$3"
  if [ "$unexpected" != "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected something other than '$actual')" >&2
  fi
}

assert_has() { # assert_has <description> <needle> <haystack>
  local desc="$1" needle="$2" haystack="$3"
  if printf '%s' "$haystack" | grep -qF -- "$needle"; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (missing '$needle')" >&2
  fi
}

refute_has() { # refute_has <description> <needle> <haystack>
  local desc="$1" needle="$2" haystack="$3"
  if printf '%s' "$haystack" | grep -qF -- "$needle"; then
    fail=$((fail + 1))
    echo "FAIL: $desc (unexpectedly found '$needle')" >&2
  else
    pass=$((pass + 1))
  fi
}

TMP="$(mktemp -d)"
trap 'chmod -R u+w "$TMP" 2>/dev/null; rm -rf "$TMP"' EXIT

# A runaway chain would fork until the process table gives out, so the tests
# that probe recursion run under a wall-clock ceiling when one is available.
TIMEOUT_BIN=""
for candidate in timeout gtimeout; do
  command -v "$candidate" >/dev/null 2>&1 && { TIMEOUT_BIN="$candidate"; break; }
done
bounded() { # bounded <command...>
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" 60 "$@"; else "$@"; fi
}

# The hook as an install would leave it: a symlink in a hooks directory that
# core.hooksPath points at. The directory name contains a space on purpose.
GHOOKS="$TMP/global hooks"
mkdir -p "$GHOOKS"
ln -sf "$HOOK" "$GHOOKS/pre-commit"

new_repo() { # new_repo <path> — fixture repo wired to the global hook
  local repo="$1"
  mkdir -p "$repo"
  git -C "$repo" init -q
  git -C "$repo" config user.email test@example.com
  git -C "$repo" config user.name test
  git -C "$repo" config commit.gpgsign false
  git -C "$repo" config core.hooksPath "$GHOOKS"
}

commits_in() { # commits_in <repo>
  git -C "$1" rev-list --count HEAD 2>/dev/null || echo 0
}

# git_in <repo> <git-args...> -> GIT_EXIT / GIT_ERR (stdout discarded)
git_in() {
  local repo="$1"; shift
  GIT_ERR="$( cd "$repo" && bounded git "$@" 2>&1 >/dev/null )"
  GIT_EXIT=$?
}

# sh_in <repo> <shell-snippet> -> GIT_EXIT / GIT_ERR
sh_in() {
  local repo="$1" snippet="$2"
  GIT_ERR="$( cd "$repo" && bounded bash -c "$snippet" 2>&1 >/dev/null )"
  GIT_EXIT=$?
}

assert_blocked() { # assert_blocked <description> <repo> <git-args...>
  local desc="$1" repo="$2"; shift 2
  local before after
  before="$(commits_in "$repo")"
  git_in "$repo" "$@"
  after="$(commits_in "$repo")"
  assert_ne "$desc: git exits non-zero" 0 "$GIT_EXIT"
  assert_eq "$desc: history is unchanged" "$before" "$after"
}

assert_committed() { # assert_committed <description> <repo> <git-args...>
  local desc="$1" repo="$2"; shift 2
  local before after
  before="$(commits_in "$repo")"
  git_in "$repo" "$@"
  after="$(commits_in "$repo")"
  assert_eq "$desc: git exits 0" 0 "$GIT_EXIT"
  assert_eq "$desc: one new commit" "$((before + 1))" "$after"
}

record_in() { # record_in <repo> <verdict>
  ( cd "$1" && printf '%s' "$2" | "$GATE" record ) >/dev/null 2>&1
}

key_in() { # key_in <repo>
  ( cd "$1" && "$GATE" key 2>/dev/null )
}

# --- the three executables ship ----------------------------------------------

assert "bin/review-gate is executable" test -x "$GATE"
assert "hooks/review-gate/pre-commit is executable" test -x "$HOOK"
assert "bin/install-review-gate is executable" test -x "$INSTALLER"
refute "the PreToolUse hook is gone" \
  test -e "$TOOLKIT_DIR/hooks/review-gate/pretool-review.sh"

# --- a plain commit is blocked until a review is recorded --------------------

PLAIN="$TMP/plain repo"
new_repo "$PLAIN"
printf 'one\n' > "$PLAIN/a.txt"
git -C "$PLAIN" add a.txt

PLAIN_KEY="$(key_in "$PLAIN")"
assert "the staged key is 16 hex characters" \
  grep -Eqx '[0-9a-f]{16}' <<<"$PLAIN_KEY"

assert_blocked "plain commit without a review" "$PLAIN" commit -m first
assert_has "the refusal names the staged key" "$PLAIN_KEY" "$GIT_ERR"
assert_has "the refusal names the record command" "review-gate record" "$GIT_ERR"
assert_has "the refusal names the REVIEW_GATE=0 bypass" \
  "REVIEW_GATE=0 git commit" "$GIT_ERR"
assert_has "the refusal names the --no-verify bypass" \
  "git commit --no-verify" "$GIT_ERR"
assert "the refusal points at an adversarial review" \
  grep -Eq 'critique|critic|code-review' <<<"$GIT_ERR"

record_in "$PLAIN" "VERDICT: READY - no blocking findings"
assert_committed "plain commit once the review is recorded" "$PLAIN" commit -m first
assert_eq "the recorded marker lives inside .git" "1" \
  "$(ls "$PLAIN/.git/agentic-review" | wc -l | tr -d ' ')"

# --- a stale marker does not authorize a different diff ----------------------

printf 'two\n' >> "$PLAIN/a.txt"
git -C "$PLAIN" add a.txt
assert_ne "the key changes when the staged diff changes" \
  "$PLAIN_KEY" "$(key_in "$PLAIN")"
assert_blocked "a stale marker does not authorize a different diff" \
  "$PLAIN" commit -m second

# --- git commit -a: keyed on what the commit will contain, not the index -----

DASH_A="$TMP/dash a"
new_repo "$DASH_A"
printf 'base\n' > "$DASH_A/f.txt"
git -C "$DASH_A" add f.txt
record_in "$DASH_A" "VERDICT: READY - seed"
git -C "$DASH_A" commit -qm seed

printf 'modified\n' > "$DASH_A/f.txt"   # tracked, unstaged; the index is clean
assert_eq "the index really is clean" "" "$(key_in "$DASH_A")"

assert_blocked "commit -a is blocked before its content is reviewed" \
  "$DASH_A" commit -am unreviewed

# The key the refusal names is the key of that same content staged, so a review
# recorded against it authorizes the -a commit even with a clean index — which
# is only possible if the hook sees what `commit -a` will write.
git -C "$DASH_A" add f.txt
DASH_A_KEY="$(key_in "$DASH_A")"
assert_has "the commit -a refusal names the content's own key" \
  "$DASH_A_KEY" "$GIT_ERR"
assert_has "the refusal names git add -u, not git add -A" \
  "git add -u" "$GIT_ERR"
record_in "$DASH_A" "VERDICT: READY - the -a content"
git -C "$DASH_A" reset -q

assert_committed "commit -a is allowed once that content is reviewed" \
  "$DASH_A" commit -am reviewed
assert_eq "the commit -a landed the worktree content" "modified" \
  "$(git -C "$DASH_A" show HEAD:f.txt)"

# `git add -u` must be advice that works: `git add -A` would also stage
# untracked files, which a `-a` commit does not contain, so it would record a
# key the hook never computes and the refusal would repeat forever.
printf 'again\n' > "$DASH_A/f.txt"
printf 'untracked\n' > "$DASH_A/u.txt"
git -C "$DASH_A" add -u
DASH_A_KEY="$(key_in "$DASH_A")"
git -C "$DASH_A" add -A
assert_ne "git add -A records a different key when an untracked file exists" \
  "$DASH_A_KEY" "$(key_in "$DASH_A")"
git -C "$DASH_A" reset -q
git -C "$DASH_A" add -u
record_in "$DASH_A" "VERDICT: READY - staged the way the refusal says to"
git -C "$DASH_A" reset -q
assert_committed "the refusal's own instructions satisfy the gate" \
  "$DASH_A" commit -am "as instructed"
assert_eq "the untracked file stayed out of the commit" "" \
  "$(git -C "$DASH_A" ls-tree --name-only HEAD u.txt)"

# --- git commit --amend is gated on what is staged against HEAD --------------

AMEND="$TMP/amend repo"
new_repo "$AMEND"
printf 'base\n' > "$AMEND/f.txt"
git -C "$AMEND" add f.txt
record_in "$AMEND" "VERDICT: READY - seed"
git -C "$AMEND" commit -qm seed
AMEND_HEAD="$(git -C "$AMEND" rev-parse HEAD)"

printf 'amended\n' > "$AMEND/f.txt"
git -C "$AMEND" add f.txt
git_in "$AMEND" commit --amend --no-edit
assert_ne "an amend with staged content is refused" 0 "$GIT_EXIT"
assert_eq "the refused amend left HEAD alone" \
  "$AMEND_HEAD" "$(git -C "$AMEND" rev-parse HEAD)"
record_in "$AMEND" "VERDICT: READY - the amended content"
git_in "$AMEND" commit --amend --no-edit
assert_eq "an amend is allowed once its staged content is reviewed" 0 "$GIT_EXIT"
assert_ne "the allowed amend rewrote HEAD" \
  "$AMEND_HEAD" "$(git -C "$AMEND" rev-parse HEAD)"

# The documented amend caveat: a reword stages nothing, so nothing is gated.
git_in "$AMEND" commit --amend -m "reworded, ungated"
assert_eq "a reword with nothing staged is not gated" 0 "$GIT_EXIT"
assert_eq "the reword took effect" "reworded, ungated" \
  "$(git -C "$AMEND" log -1 --format=%s)"

# --- pathspec commits are gated on the pathspec's content --------------------

PS="$TMP/pathspec repo"
new_repo "$PS"
printf 'base\n' > "$PS/f.txt"
git -C "$PS" add f.txt
record_in "$PS" "VERDICT: READY - seed"
git -C "$PS" commit -qm seed

printf 'from the worktree\n' > "$PS/f.txt"   # worktree only; index stays clean
assert_blocked "a pathspec commit is blocked without a review" \
  "$PS" commit -m pathspec f.txt

git -C "$PS" add f.txt
PS_KEY="$(key_in "$PS")"
assert_has "the pathspec refusal names the pathspec content's key" \
  "$PS_KEY" "$GIT_ERR"
record_in "$PS" "VERDICT: READY - the pathspec content"
git -C "$PS" reset -q
assert_committed "a pathspec commit is allowed once reviewed" \
  "$PS" commit -m pathspec f.txt

# A pathspec commit is built from HEAD plus the named paths, so anything else
# left staged is in the recorded key but not in the commit. The documented
# recipe clears the index first; without that the refusal repeats forever.
printf 'other\n' > "$PS/g.txt"
git -C "$PS" add g.txt
git -C "$PS" commit -qm "seed g" --no-verify
printf 'changed f\n' > "$PS/f.txt"
printf 'changed g\n' > "$PS/g.txt"
git -C "$PS" add g.txt          # unrelated staged work
git -C "$PS" add -- f.txt
record_in "$PS" "VERDICT: READY - but the index holds more than the pathspec"
assert_blocked "unrelated staged content does not authorize a pathspec commit" \
  "$PS" commit -m pathspec f.txt

git -C "$PS" reset -q
git -C "$PS" add -- f.txt
record_in "$PS" "VERDICT: READY - the pathspec content alone"
assert_committed "the documented pathspec recipe satisfies the gate" \
  "$PS" commit -m pathspec f.txt
assert_eq "the unrelated change stayed out of the pathspec commit" "other" \
  "$(git -C "$PS" show HEAD:g.txt)"

# --- a commit inside bash -c is gated too (no command-string parsing left) ---

BC="$TMP/bash dash c"
new_repo "$BC"
printf 'one\n' > "$BC/a.txt"
git -C "$BC" add a.txt
before="$(commits_in "$BC")"
sh_in "$BC" 'git commit -m "from bash -c"'
assert_ne "a commit run under bash -c exits non-zero" 0 "$GIT_EXIT"
assert_eq "a commit run under bash -c creates no commit" \
  "$before" "$(commits_in "$BC")"
sh_in "$BC" 'eval "git commit -m evaled"'
assert_ne "a commit run under eval exits non-zero" 0 "$GIT_EXIT"
assert_eq "a commit run under eval creates no commit" \
  "$before" "$(commits_in "$BC")"

# --- the two bypasses --------------------------------------------------------

BYPASS="$TMP/bypass repo"
new_repo "$BYPASS"
printf 'one\n' > "$BYPASS/a.txt"
git -C "$BYPASS" add a.txt
assert_blocked "the bypass fixture is gated to begin with" \
  "$BYPASS" commit -m gated

before="$(commits_in "$BYPASS")"
sh_in "$BYPASS" 'REVIEW_GATE=0 git commit -m bypassed'
assert_eq "REVIEW_GATE=0 git commit exits 0" 0 "$GIT_EXIT"
assert_eq "REVIEW_GATE=0 git commit creates the commit" \
  "$((before + 1))" "$(commits_in "$BYPASS")"

printf 'two\n' >> "$BYPASS/a.txt"
git -C "$BYPASS" add a.txt
assert_blocked "the next diff is gated again" "$BYPASS" commit -m gated
assert_committed "git commit --no-verify skips the hook" \
  "$BYPASS" commit --no-verify -m unverified

# Both bypasses return before the chain, so neither runs the repository's own
# pre-commit hook. The README says so; this pins it.
BYPASS_CHAIN="$TMP/bypass chain"
new_repo "$BYPASS_CHAIN"
mkdir -p "$BYPASS_CHAIN/.git/hooks"
printf '#!/usr/bin/env bash\ndate > "%s"\nexit 0\n' "$TMP/bypass-chain-ran" \
  > "$BYPASS_CHAIN/.git/hooks/pre-commit"
chmod 755 "$BYPASS_CHAIN/.git/hooks/pre-commit"
printf 'one\n' > "$BYPASS_CHAIN/a.txt"
git -C "$BYPASS_CHAIN" add a.txt
assert_blocked "the bypass-chain fixture is gated to begin with" \
  "$BYPASS_CHAIN" commit -m gated
assert "the repo hook does run in this fixture without the bypass" \
  test -f "$TMP/bypass-chain-ran"
rm -f "$TMP/bypass-chain-ran"
sh_in "$BYPASS_CHAIN" 'REVIEW_GATE=0 git commit -m bypassed'
assert_eq "REVIEW_GATE=0 commits past the repo hook" 0 "$GIT_EXIT"
refute "REVIEW_GATE=0 does not run the repository's own hook" \
  test -f "$TMP/bypass-chain-ran"

# --- nothing staged is not something to gate ---------------------------------

EMPTY="$TMP/empty commit"
new_repo "$EMPTY"
printf 'seed\n' > "$EMPTY/a.txt"
git -C "$EMPTY" add a.txt
record_in "$EMPTY" "VERDICT: READY - seed"
git -C "$EMPTY" commit -qm seed
assert_committed "an empty commit is not blocked" \
  "$EMPTY" commit --allow-empty -m nothing
( cd "$EMPTY" && bounded "$GHOOKS/pre-commit" ) >/dev/null 2>&1
assert_eq "the hook itself exits 0 with nothing staged" 0 "$?"

# --- linked worktrees share the marker directory -----------------------------

WT_MAIN="$TMP/worktree main"
new_repo "$WT_MAIN"
printf 'base\n' > "$WT_MAIN/f.txt"
git -C "$WT_MAIN" add f.txt
record_in "$WT_MAIN" "VERDICT: READY - seed"
git -C "$WT_MAIN" commit -qm seed
WT_LINK="$TMP/worktree linked"
git -C "$WT_MAIN" worktree add -q "$WT_LINK" -b linked
printf 'from the worktree\n' > "$WT_LINK/f.txt"
git -C "$WT_LINK" add f.txt
assert_blocked "a commit in a linked worktree is gated" "$WT_LINK" commit -m x
record_in "$WT_LINK" "VERDICT: READY - the worktree change"
assert_committed "a linked worktree commits once reviewed" "$WT_LINK" commit -m x
assert "the worktree's marker landed in the shared common dir" \
  test -d "$WT_MAIN/.git/agentic-review"

# --- a commit from a subdirectory is gated on the same key -------------------

SUBDIR="$TMP/subdir repo"
new_repo "$SUBDIR"
mkdir -p "$SUBDIR/nested dir"
printf 'one\n' > "$SUBDIR/nested dir/a.txt"
git -C "$SUBDIR" add .
assert_blocked "a commit issued from a subdirectory is gated" \
  "$SUBDIR/nested dir" commit -m x
record_in "$SUBDIR/nested dir" "VERDICT: READY"
assert_committed "a subdirectory commit lands once reviewed" \
  "$SUBDIR/nested dir" commit -m x

# --- chaining: the repo's own pre-commit hook still runs ---------------------

write_repo_hook() { # write_repo_hook <repo> <body>
  local repo="$1" body="$2" dir
  dir="$repo/.git/hooks"
  mkdir -p "$dir"
  printf '#!/usr/bin/env bash\n%s\n' "$body" > "$dir/pre-commit"
  chmod 755 "$dir/pre-commit"
}

CHAIN_FAIL="$TMP/chain fail"
new_repo "$CHAIN_FAIL"
write_repo_hook "$CHAIN_FAIL" 'echo "repo hook says no" >&2; exit 1'
printf 'one\n' > "$CHAIN_FAIL/a.txt"
git -C "$CHAIN_FAIL" add a.txt
record_in "$CHAIN_FAIL" "VERDICT: READY - reviewed but the repo hook fails"
assert_blocked "a failing repo hook blocks even with a review recorded" \
  "$CHAIN_FAIL" commit -m x
assert_has "the repo hook's own message reaches the user" \
  "repo hook says no" "$GIT_ERR"
refute_has "a failing repo hook prints nothing extra from the gate" \
  "REVIEW_GATE=0 git commit" "$GIT_ERR"

write_repo_hook "$CHAIN_FAIL" 'exit 3'
( cd "$CHAIN_FAIL" && bounded "$GHOOKS/pre-commit" ) >/dev/null 2>&1
assert_eq "the hook exits with the repo hook's own status" 3 "$?"

CHAIN_OK="$TMP/chain ok"
new_repo "$CHAIN_OK"
write_repo_hook "$CHAIN_OK" "date > \"$TMP/chain-ok-ran\"; exit 0"
printf 'one\n' > "$CHAIN_OK/a.txt"
git -C "$CHAIN_OK" add a.txt
assert_blocked "a passing repo hook lets the review check decide" \
  "$CHAIN_OK" commit -m x
assert "the passing repo hook actually ran" test -f "$TMP/chain-ok-ran"
record_in "$CHAIN_OK" "VERDICT: READY"
assert_committed "a passing repo hook plus a review commits" \
  "$CHAIN_OK" commit -m x

CHAIN_IO="$TMP/chain io"
new_repo "$CHAIN_IO"
write_repo_hook "$CHAIN_IO" \
  "printf '%s' \"\$*\" > \"$TMP/chain-args\"; cat > \"$TMP/chain-stdin\"; exit 0"
( cd "$CHAIN_IO" && printf 'stdin payload' | bounded "$GHOOKS/pre-commit" one "arg two" ) \
  >/dev/null 2>&1
assert_eq "the repo hook receives the hook's own arguments" \
  "one arg two" "$(cat "$TMP/chain-args" 2>/dev/null)"
assert_eq "the repo hook receives the hook's own stdin" \
  "stdin payload" "$(cat "$TMP/chain-stdin" 2>/dev/null)"

# Recursion guards: the repo hook IS the global hook, by symlink and by copy.
CHAIN_LINK="$TMP/chain symlink"
new_repo "$CHAIN_LINK"
mkdir -p "$CHAIN_LINK/.git/hooks"
ln -sf "$GHOOKS/pre-commit" "$CHAIN_LINK/.git/hooks/pre-commit"
printf 'one\n' > "$CHAIN_LINK/a.txt"
git -C "$CHAIN_LINK" add a.txt
assert_blocked "a self-referential symlinked repo hook still gates" \
  "$CHAIN_LINK" commit -m x
assert_ne "the self-referential symlink does not run away" 124 "$GIT_EXIT"
record_in "$CHAIN_LINK" "VERDICT: READY"
assert_committed "a self-referential symlinked repo hook commits once reviewed" \
  "$CHAIN_LINK" commit -m x

CHAIN_COPY="$TMP/chain copy"
new_repo "$CHAIN_COPY"
mkdir -p "$CHAIN_COPY/.git/hooks"
cp "$HOOK" "$CHAIN_COPY/.git/hooks/pre-commit"
chmod 755 "$CHAIN_COPY/.git/hooks/pre-commit"
printf 'one\n' > "$CHAIN_COPY/a.txt"
git -C "$CHAIN_COPY" add a.txt
assert_blocked "a copied-in repo hook still gates without recursing" \
  "$CHAIN_COPY" commit -m x
assert_ne "the copied repo hook does not run away" 124 "$GIT_EXIT"
record_in "$CHAIN_COPY" "VERDICT: READY"
assert_committed "a copied-in repo hook commits once reviewed" \
  "$CHAIN_COPY" commit -m x

# A non-executable repo hook is not run, exactly as git would treat it.
CHAIN_NOX="$TMP/chain nonexec"
new_repo "$CHAIN_NOX"
write_repo_hook "$CHAIN_NOX" 'exit 1'
chmod 644 "$CHAIN_NOX/.git/hooks/pre-commit"
printf 'one\n' > "$CHAIN_NOX/a.txt"
git -C "$CHAIN_NOX" add a.txt
record_in "$CHAIN_NOX" "VERDICT: READY"
assert_committed "a non-executable repo hook is skipped" "$CHAIN_NOX" commit -m x

# --- fail-open boundaries ----------------------------------------------------

FO="$TMP/fail open"
new_repo "$FO"
printf 'one\n' > "$FO/a.txt"
git -C "$FO" add a.txt
assert_blocked "the fail-open fixture is gated to begin with" "$FO" commit -m x

# review-gate neither beside the hook nor on PATH. The fixture carries no
# core.hooksPath, so the stray copy has no hook of its own to chain into.
LONELY="$TMP/lonely hooks"
mkdir -p "$LONELY"
cp "$HOOK" "$LONELY/pre-commit"
chmod 755 "$LONELY/pre-commit"
LONELY_REPO="$TMP/lonely repo"
new_repo "$LONELY_REPO"
git -C "$LONELY_REPO" config --unset core.hooksPath
printf 'one\n' > "$LONELY_REPO/a.txt"
git -C "$LONELY_REPO" add a.txt
SCRUBBED=""
IFS=: read -r -a _pdirs <<< "$PATH"
for _d in "${_pdirs[@]}"; do
  [ -x "$_d/review-gate" ] && continue
  SCRUBBED="${SCRUBBED:+$SCRUBBED:}$_d"
done
FO_ERR="$( cd "$LONELY_REPO" && PATH="$SCRUBBED" bounded "$LONELY/pre-commit" 2>&1 )"
assert_eq "the hook exits 0 when review-gate cannot be located" 0 "$?"
assert_has "the hook says why it allowed" "review-gate not found" "$FO_ERR"

# outside a git repository
NOTREPO="$TMP/not a repo"
mkdir -p "$NOTREPO"
( cd "$NOTREPO" && bounded "$GHOOKS/pre-commit" ) >/dev/null 2>&1
assert_eq "the hook exits 0 outside a git repository" 0 "$?"

# No digest tool is the one documented condition that denies rather than
# allowing: a gate that cannot see the diff is not a gate.
stock_path_dir() { # stock_path_dir <dir> <binary...>
  local dir="$1" b src; shift
  mkdir -p "$dir"
  for b in "$@"; do
    src="$(command -v "$b" 2>/dev/null)" && ln -sf "$src" "$dir/$b"
  done
  ln -sf /bin/bash "$dir/bash"
}
NODIGEST="$TMP/no digest"
stock_path_dir "$NODIGEST" git cut dirname basename mkdir cat readlink printf
( cd "$FO" && PATH="$NODIGEST" bounded "$GHOOKS/pre-commit" ) >/dev/null 2>&1
assert_ne "the hook denies when no digest tool exists" 0 "$?"
( cd "$FO" && PATH="$NODIGEST" "$GATE" check ) >/dev/null 2>"$TMP/.nodigest_err"
assert_ne "review-gate check denies when no digest tool exists" 0 "$?"
assert "the denial names the missing digest tool" \
  grep -Eq 'shasum|sha256sum' "$TMP/.nodigest_err"

# An unwritable marker location must allow rather than wedge the repository.
UNWRITABLE="$TMP/unwritable"
new_repo "$UNWRITABLE"
printf 'one\n' > "$UNWRITABLE/a.txt"
git -C "$UNWRITABLE" add a.txt
( cd "$UNWRITABLE" && "$GATE" check ) >/dev/null 2>&1
assert_eq "check denies while the marker location is writable" 1 "$?"
chmod 500 "$UNWRITABLE/.git"
( cd "$UNWRITABLE" && "$GATE" check ) >/dev/null 2>&1
assert_eq "check allows when the marker cannot be written" 0 "$?"
chmod 700 "$UNWRITABLE/.git"

# --- bin/review-gate keeps its contract --------------------------------------

CLI="$TMP/cli repo"
new_repo "$CLI"
( cd "$CLI" && "$GATE" key ) >/dev/null 2>&1
assert_eq "key exits 1 on an empty staged diff" 1 "$?"
printf 'one\n' > "$CLI/a.txt"
git -C "$CLI" add a.txt
CLI_KEY="$(key_in "$CLI")"
mkdir -p "$CLI/sub dir"
assert_eq "the key is identical from a repo subdirectory" \
  "$CLI_KEY" "$(key_in "$CLI/sub dir")"
( cd "$CLI" && printf '' | "$GATE" record ) >/dev/null 2>&1
assert_eq "record refuses an empty verdict" 1 "$?"
( cd "$CLI" && "$GATE" key --all ) >/dev/null 2>&1
assert_ne "the --all flag is gone" 0 "$?"
( cd "$CLI" && "$GATE" key --amend ) >/dev/null 2>&1
assert_ne "the --amend flag is gone" 0 "$?"
refute "no diff-base widening is left in bin/review-gate" \
  grep -Eq 'effective_diff|diff_base' "$GATE"
assert "bin/review-gate documents the REVIEW_GATE=0 bypass" \
  bash -c 'sed -n "1,/^set -u/p" "$1" | grep -q "REVIEW_GATE=0"' _ "$GATE"
assert "bin/review-gate documents the --amend caveat" \
  bash -c 'sed -n "1,/^set -u/p" "$1" | grep -q -- "--amend"' _ "$GATE"

# --- bin/install-review-gate: per-repository installation --------------------
# Sandboxed: HOME and the global git config both point into the temp dir, so no
# assertion here can touch the real machine's configuration. If this git does
# not honor GIT_CONFIG_GLOBAL, the installer assertions are skipped rather than
# run against the real config.

FAKEHOME="$TMP/fake home"
mkdir -p "$FAKEHOME"
FAKECONFIG="$FAKEHOME/.gitconfig"
: > "$FAKECONFIG"
GIT_CONFIG_GLOBAL="$FAKECONFIG" git config --global reviewgate.probe sandboxed 2>/dev/null
if grep -q sandboxed "$FAKECONFIG" 2>/dev/null; then
  inst() { # inst <installer-args...>
    HOME="$FAKEHOME" GIT_CONFIG_GLOBAL="$FAKECONFIG" "$INSTALLER" "$@"
  }
  global_hookspath() {
    GIT_CONFIG_GLOBAL="$FAKECONFIG" git config --global --get core.hooksPath 2>/dev/null
  }
  local_hookspath() { # local_hookspath <repo>
    git -C "$1" config --local --get core.hooksPath 2>/dev/null
  }

  # bare_repo <path> — a fixture with no hooks wiring of any kind, so what
  # gates it can only be what the installer put there.
  bare_repo() {
    local repo="$1"
    mkdir -p "$repo"
    HOME="$FAKEHOME" GIT_CONFIG_GLOBAL="$FAKECONFIG" git -C "$repo" init -q
    git -C "$repo" config user.email t@e.com
    git -C "$repo" config user.name t
    git -C "$repo" config commit.gpgsign false
  }

  sb_git() { # sb_git <repo> <git-args...> -> GIT_EXIT / GIT_ERR
    local repo="$1"; shift
    GIT_ERR="$( cd "$repo" &&
      HOME="$FAKEHOME" GIT_CONFIG_GLOBAL="$FAKECONFIG" bounded git "$@" 2>&1 >/dev/null )"
    GIT_EXIT=$?
  }
  sb_blocked() { # sb_blocked <description> <repo> <git-args...>
    local desc="$1" repo="$2"; shift 2
    local before after
    before="$(commits_in "$repo")"
    sb_git "$repo" "$@"
    after="$(commits_in "$repo")"
    assert_ne "$desc: git exits non-zero" 0 "$GIT_EXIT"
    assert_eq "$desc: history is unchanged" "$before" "$after"
  }
  sb_committed() { # sb_committed <description> <repo> <git-args...>
    local desc="$1" repo="$2"; shift 2
    local before after
    before="$(commits_in "$repo")"
    sb_git "$repo" "$@"
    after="$(commits_in "$repo")"
    assert_eq "$desc: git exits 0" 0 "$GIT_EXIT"
    assert_eq "$desc: one new commit" "$((before + 1))" "$after"
  }

  sum_of() { shasum "$1" | cut -d' ' -f1; }
  prefix_sum() { # prefix_sum <file> <bytes>
    head -c "$2" "$1" | shasum | cut -d' ' -f1
  }
  marker_count() { grep -c 'BEGIN AGENTIC REVIEW-GATE' "$1" | tr -d ' '; }
  line_of() { grep -n "$1" "$2" | head -n 1 | cut -d: -f1; }

  write_hook() { # write_hook <path> <body-line...>
    local path="$1"; shift
    mkdir -p "$(dirname "$path")"
    { printf '#!/usr/bin/env bash\n'; printf '%s\n' "$@"; } > "$path"
    chmod 755 "$path"
  }

  # A repository with no pre-commit hook of its own.
  FRESH="$TMP/install fresh"
  bare_repo "$FRESH"
  FRESH_OUT="$(inst install "$FRESH" 2>&1)"
  assert_eq "install into a fresh repo exits 0" 0 "$?"
  assert "install puts an executable pre-commit in the repo's hooks dir" \
    test -x "$FRESH/.git/hooks/pre-commit"
  assert_has "install names the file it wrote" ".git/hooks/pre-commit" "$FRESH_OUT"
  assert_eq "install sets no global core.hooksPath" "" "$(global_hookspath)"
  assert_eq "install sets no local core.hooksPath" "" "$(local_hookspath "$FRESH")"
  printf 'one\n' > "$FRESH/a.txt"
  git -C "$FRESH" add a.txt
  sb_blocked "a per-repo install gates a commit" "$FRESH" commit -m x
  assert_has "the refusal comes from the review gate" \
    "no review is recorded" "$GIT_ERR"
  record_in "$FRESH" "VERDICT: READY"
  sb_committed "the installed repo commits once reviewed" "$FRESH" commit -m x

  # An existing passing pre-commit hook keeps running, and ours runs after it.
  ALONG="$TMP/install alongside"
  bare_repo "$ALONG"
  ALONG_HOOK="$ALONG/.git/hooks/pre-commit"
  ALONG_LOG="$TMP/alongside-runs"
  write_hook "$ALONG_HOOK" "echo ran >> \"$ALONG_LOG\""
  ALONG_BYTES="$(wc -c < "$ALONG_HOOK" | tr -d ' ')"
  ALONG_SUM="$(sum_of "$ALONG_HOOK")"
  inst install "$ALONG" >/dev/null 2>&1
  assert_eq "install beside an existing hook exits 0" 0 "$?"
  assert_eq "the existing hook survives byte-for-byte as the file's prefix" \
    "$ALONG_SUM" "$(prefix_sum "$ALONG_HOOK" "$ALONG_BYTES")"
  assert_eq "exactly one review-gate block is present" 1 "$(marker_count "$ALONG_HOOK")"
  assert "the appended block invokes the hook by absolute path" \
    grep -qF "$HOOK" "$ALONG_HOOK"
  printf 'one\n' > "$ALONG/a.txt"
  git -C "$ALONG" add a.txt
  : > "$ALONG_LOG"
  sb_blocked "an appended block gates a commit" "$ALONG" commit -m x
  assert_eq "the repo's own hook ran exactly once" 1 \
    "$(wc -l < "$ALONG_LOG" | tr -d ' ')"
  assert_has "the refusal comes from the review gate" \
    "no review is recorded" "$GIT_ERR"
  record_in "$ALONG" "VERDICT: READY"
  : > "$ALONG_LOG"
  sb_committed "the commit lands once reviewed" "$ALONG" commit -m x
  assert_eq "the repo's own hook ran once for the passing commit" 1 \
    "$(wc -l < "$ALONG_LOG" | tr -d ' ')"

  # Installing twice adds one block, not two, and runs the repo hook once.
  inst install "$ALONG" >/dev/null 2>&1
  assert_eq "a second install exits 0" 0 "$?"
  assert_eq "a second install leaves exactly one block" 1 \
    "$(marker_count "$ALONG_HOOK")"
  assert_eq "a second install leaves the existing hook byte-identical" \
    "$ALONG_SUM" "$(prefix_sum "$ALONG_HOOK" "$ALONG_BYTES")"
  printf 'two\n' >> "$ALONG/a.txt"
  git -C "$ALONG" add a.txt
  record_in "$ALONG" "VERDICT: READY"
  : > "$ALONG_LOG"
  sb_committed "a twice-installed repo still commits once reviewed" \
    "$ALONG" commit -m x
  assert_eq "the repo's own hook still ran exactly once" 1 \
    "$(wc -l < "$ALONG_LOG" | tr -d ' ')"

  # An existing hook that fails still blocks, and our check never runs.
  FAILS="$TMP/install over failing"
  bare_repo "$FAILS"
  FAILS_HOOK="$FAILS/.git/hooks/pre-commit"
  write_hook "$FAILS_HOOK" 'echo "repo hook says no" >&2' 'exit 1'
  inst install "$FAILS" >/dev/null 2>&1
  assert_eq "install over a failing hook exits 0" 0 "$?"
  printf 'one\n' > "$FAILS/a.txt"
  git -C "$FAILS" add a.txt
  record_in "$FAILS" "VERDICT: READY - reviewed, but the repo hook fails"
  sb_blocked "a failing repo hook blocks even with a review recorded" \
    "$FAILS" commit -m x
  assert_has "the repo hook's own message reaches the user" \
    "repo hook says no" "$GIT_ERR"
  refute_has "the review check never ran" "no review is recorded" "$GIT_ERR"

  # A hook whose last line is an unconditional `exit 0` would swallow an
  # appended block, so the installer refuses rather than reporting success.
  INERT="$TMP/install inert"
  bare_repo "$INERT"
  INERT_HOOK="$INERT/.git/hooks/pre-commit"
  write_hook "$INERT_HOOK" 'echo checking' 'exit 0'
  INERT_SUM="$(sum_of "$INERT_HOOK")"
  INERT_OUT="$(inst install "$INERT" 2>&1)"
  assert_ne "install refuses a hook ending in an unconditional exit" 0 "$?"
  assert_has "the refusal says the block would not run" \
    "would never run" "$INERT_OUT"
  assert_eq "the refused install left the hook untouched" \
    "$INERT_SUM" "$(sum_of "$INERT_HOOK")"

  # A local core.hooksPath is honored: the hook lands where git will look.
  LOCALHP="$TMP/local hookspath repo"
  bare_repo "$LOCALHP"
  LOCALHP_DIR="$TMP/local hookspath dir"
  mkdir -p "$LOCALHP_DIR"
  git -C "$LOCALHP" config core.hooksPath "$LOCALHP_DIR"
  inst install "$LOCALHP" >/dev/null 2>&1
  assert_eq "install into a repo with a local hooksPath exits 0" 0 "$?"
  assert "install lands in the configured hooks directory" \
    test -x "$LOCALHP_DIR/pre-commit"
  refute "install does not touch .git/hooks when a hooksPath is set" \
    test -e "$LOCALHP/.git/hooks/pre-commit"
  assert_eq "install leaves the local core.hooksPath alone" \
    "$LOCALHP_DIR" "$(local_hookspath "$LOCALHP")"
  printf 'one\n' > "$LOCALHP/a.txt"
  git -C "$LOCALHP" add a.txt
  sb_blocked "the configured hooks directory is what gates" "$LOCALHP" commit -m x

  # A bd-managed repository: a beads-owned block in .beads/hooks/pre-commit,
  # pointed at by a local core.hooksPath. Ours goes after the END marker and
  # the beads block is never written inside.
  BD="$TMP/beads managed"
  bare_repo "$BD"
  BD_HOOK="$BD/.beads/hooks/pre-commit"
  BD_LOG="$TMP/beads-runs"
  write_hook "$BD_HOOK" \
    '# --- BEGIN BEADS INTEGRATION v1.1.0 ---' \
    "echo beads >> \"$BD_LOG\"" \
    'if [ -n "${BEADS_FAIL:-}" ]; then exit 9; fi' \
    '# --- END BEADS INTEGRATION v1.1.0 ---'
  git -C "$BD" config core.hooksPath "$BD/.beads/hooks"
  BD_BYTES="$(wc -c < "$BD_HOOK" | tr -d ' ')"
  BD_SUM="$(sum_of "$BD_HOOK")"
  BD_BLOCK="$(awk '/BEGIN BEADS/,/END BEADS/' "$BD_HOOK")"
  inst install "$BD" >/dev/null 2>&1
  assert_eq "install into a bd-managed repo exits 0" 0 "$?"
  assert_eq "the beads block is byte-identical afterward" \
    "$BD_BLOCK" "$(awk '/BEGIN BEADS/,/END BEADS/' "$BD_HOOK")"
  assert_eq "the whole beads hook survives as the file's prefix" \
    "$BD_SUM" "$(prefix_sum "$BD_HOOK" "$BD_BYTES")"
  assert "our block begins after the beads END marker" \
    test "$(line_of 'BEGIN AGENTIC REVIEW-GATE' "$BD_HOOK")" -gt \
      "$(line_of 'END BEADS INTEGRATION' "$BD_HOOK")"
  printf 'one\n' > "$BD/a.txt"
  git -C "$BD" add a.txt
  : > "$BD_LOG"
  sb_blocked "a bd-managed repo is gated by the appended block" "$BD" commit -m x
  assert_eq "bd's own portion still executes" 1 "$(wc -l < "$BD_LOG" | tr -d ' ')"
  record_in "$BD" "VERDICT: READY"
  sb_committed "a bd-managed repo commits once reviewed" "$BD" commit -m x

  # status reports what is actually on disk, in each state.
  STATUS_OUT="$(inst status "$FRESH" 2>&1)"
  assert_eq "status exits 0" 0 "$?"
  assert_has "status names the repo" "$FRESH" "$STATUS_OUT"
  assert_has "status reports the effective hooks dir" \
    "$FRESH/.git/hooks" "$STATUS_OUT"
  assert "status reports our hook as present" \
    grep -Eqi 'review-gate: *present' <<<"$STATUS_OUT"
  assert "status reports no other pre-commit content" \
    grep -Eqi 'other pre-commit content: *no' <<<"$STATUS_OUT"
  assert "status reports the local core.hooksPath as unset" \
    grep -Eqi 'local core\.hooksPath: *\(unset\)' <<<"$STATUS_OUT"
  assert "status reports the global core.hooksPath as unset" \
    grep -Eqi 'global core\.hooksPath: *\(unset\)' <<<"$STATUS_OUT"

  STATUS_OUT="$(inst status "$BD" 2>&1)"
  assert_has "status reports the bd hooks dir" "$BD/.beads/hooks" "$STATUS_OUT"
  assert "status reports our block as present in a bd repo" \
    grep -Eqi 'review-gate: *present' <<<"$STATUS_OUT"
  assert "status reports the other content a bd hook carries" \
    grep -Eqi 'other pre-commit content: *yes' <<<"$STATUS_OUT"
  assert_has "status reports the local core.hooksPath" \
    "$BD/.beads/hooks" "$STATUS_OUT"

  STATUS_OUT="$(inst status "$INERT" 2>&1)"
  assert "status reports our hook as absent where install refused" \
    grep -Eqi 'review-gate: *absent' <<<"$STATUS_OUT"
  assert "status still reports the repo's own hook content" \
    grep -Eqi 'other pre-commit content: *yes' <<<"$STATUS_OUT"

  # uninstall removes only our block.
  inst uninstall "$ALONG" >/dev/null 2>&1
  assert_eq "uninstall exits 0" 0 "$?"
  assert_eq "uninstall restores the existing hook byte-for-byte" \
    "$ALONG_SUM" "$(sum_of "$ALONG_HOOK")"
  inst uninstall "$BD" >/dev/null 2>&1
  assert_eq "uninstall restores a bd-managed hook byte-for-byte" \
    "$BD_SUM" "$(sum_of "$BD_HOOK")"
  inst uninstall "$FRESH" >/dev/null 2>&1
  refute "uninstall removes a file that is only our hook" \
    test -e "$FRESH/.git/hooks/pre-commit"
  STATUS_OUT="$(inst status "$FRESH" 2>&1)"
  assert "status reports our hook as absent after uninstall" \
    grep -Eqi 'review-gate: *absent' <<<"$STATUS_OUT"
  inst uninstall "$FRESH" >/dev/null 2>&1
  assert_eq "uninstall on a repo with no hook exits 0" 0 "$?"

  # An uninstalled repo commits without a review again.
  printf 'three\n' >> "$ALONG/a.txt"
  git -C "$ALONG" add a.txt
  : > "$ALONG_LOG"
  sb_committed "an uninstalled repo is no longer gated" "$ALONG" commit -m x
  assert_eq "the repo's own hook still runs after uninstall" 1 \
    "$(wc -l < "$ALONG_LOG" | tr -d ' ')"

  # With no repository argument, the current repository is the target.
  DEFAULTED="$TMP/default target"
  bare_repo "$DEFAULTED"
  ( cd "$DEFAULTED" && inst install ) >/dev/null 2>&1
  assert_eq "install with no argument exits 0" 0 "$?"
  assert "install with no argument targets the current repo" \
    test -x "$DEFAULTED/.git/hooks/pre-commit"
  ( cd "$DEFAULTED" && inst uninstall ) >/dev/null 2>&1
  refute "uninstall with no argument targets the current repo" \
    test -e "$DEFAULTED/.git/hooks/pre-commit"

  # Several repositories in one invocation.
  MULTI_A="$TMP/multi a"; bare_repo "$MULTI_A"
  MULTI_B="$TMP/multi b"; bare_repo "$MULTI_B"
  inst install "$MULTI_A" "$MULTI_B" >/dev/null 2>&1
  assert_eq "install accepts several repositories" 0 "$?"
  assert "the first named repo is installed" test -x "$MULTI_A/.git/hooks/pre-commit"
  assert "the second named repo is installed" test -x "$MULTI_B/.git/hooks/pre-commit"

  # Refusals.
  NOTAREPO="$TMP/plain directory"
  mkdir -p "$NOTAREPO"
  REFUSE_OUT="$(inst install "$NOTAREPO" 2>&1)"
  assert_ne "install refuses a directory that is not a git repo" 0 "$?"
  assert "the refusal says it is not a git repository" \
    grep -Eqi 'not a git repositor' <<<"$REFUSE_OUT"
  refute "nothing was written into the plain directory" \
    test -e "$NOTAREPO/pre-commit"

  REFUSE_OUT="$(inst install "$TMP/no such path" 2>&1)"
  assert_ne "install refuses a path that does not exist" 0 "$?"

  UNWRITABLE_REPO="$TMP/unwritable hooks"
  bare_repo "$UNWRITABLE_REPO"
  mkdir -p "$UNWRITABLE_REPO/.git/hooks"
  chmod 500 "$UNWRITABLE_REPO/.git/hooks"
  REFUSE_OUT="$(inst install "$UNWRITABLE_REPO" 2>&1)"
  assert_ne "install refuses an unwritable hooks directory" 0 "$?"
  assert "the refusal says the directory is not writable" \
    grep -Eqi 'writable' <<<"$REFUSE_OUT"
  chmod 700 "$UNWRITABLE_REPO/.git/hooks"

  REFUSE_OUT="$(inst frobnicate "$FRESH" 2>&1)"
  assert_ne "an unknown subcommand exits non-zero" 0 "$?"
  assert "the usage message names the subcommands" \
    grep -Eq 'install.*uninstall.*status' <<<"$REFUSE_OUT"

  # Nothing anywhere in this section may have touched core.hooksPath.
  assert_eq "no global core.hooksPath was ever set" "" "$(global_hookspath)"
  assert_eq "the fresh repo's local core.hooksPath is still unset" \
    "" "$(local_hookspath "$FRESH")"
  refute "the installer never unsets a core.hooksPath" \
    grep -qF -- '--unset' "$INSTALLER"
  refute "the installer never writes a core.hooksPath" \
    grep -Eq 'git config[^|]*core\.hooksPath "' "$INSTALLER"
else
  echo "SKIP: git does not honor GIT_CONFIG_GLOBAL; installer assertions skipped" >&2
fi

# --- severity tiering: only correctness-class findings block -----------------

sev_repo() { # sev_repo <name> — a gated fixture with one staged change
  local repo="$TMP/$1"
  new_repo "$repo" >/dev/null
  printf 'one\n' > "$repo/a.txt"
  git -C "$repo" add a.txt
  printf '%s' "$repo"
}

NIT="$(sev_repo 'severity nits')"
record_in "$NIT" 'VERDICT: NOT READY
Nit: rename foo to bar
[style] prefer a const here
- structure: this helper belongs in the caller'
assert_committed "a review carrying only nits does not block" "$NIT" commit -m x
assert_has "the allowed commit still reports the findings" \
  "prefer a const here" "$GIT_ERR"

BUG="$(sev_repo 'severity correctness')"
record_in "$BUG" 'VERDICT: NOT READY
[correctness] off-by-one in the loop bound
Nit: rename foo to bar'
assert_blocked "a correctness finding blocks the commit" "$BUG" commit -m x
assert_has "the refusal quotes the blocking finding" \
  "off-by-one in the loop bound" "$GIT_ERR"
assert "the refusal says which categories block" \
  grep -Eqi 'correctness' <<<"$GIT_ERR"
assert_has "the refusal names the REVIEW_GATE=0 bypass" \
  "REVIEW_GATE=0 git commit" "$GIT_ERR"

SEC="$(sev_repo 'severity security')"
record_in "$SEC" 'VERDICT: NOT READY
Severity: security - the query is built by string concatenation'
assert_blocked "a security finding blocks the commit" "$SEC" commit -m x

LOSS="$(sev_repo 'severity data loss')"
record_in "$LOSS" 'Category: data-loss - the migration drops the column first'
assert_blocked "a data-loss finding blocks the commit" "$LOSS" commit -m x

SECRET="$(sev_repo 'severity secret')"
record_in "$SECRET" '[secrets] an API token is committed in config.yml'
assert_blocked "a committed-secret finding blocks the commit" "$SECRET" commit -m x

# The tolerant default: anything the parse does not recognize is reported and
# allowed. A gate that blocks on garbage input trains the operator to bypass it.
JUNK="$(sev_repo 'severity unparseable')"
record_in "$JUNK" 'VERDICT ?? {"findings": [{"sev": 7}]} ###'
assert_committed "an unparseable verdict defaults to non-blocking" \
  "$JUNK" commit -m x

UNKNOWN="$(sev_repo 'severity unknown label')"
record_in "$UNKNOWN" 'Severity: frobnicate - nobody knows what this tier means'
assert_committed "an unrecognized severity defaults to non-blocking" \
  "$UNKNOWN" commit -m x

# A label whose finding is that there is no finding is not a finding.
NEGATED="$(sev_repo 'severity negated')"
record_in "$NEGATED" 'VERDICT: READY
Security: none
Correctness: no bugs found
[data-loss] n/a'
assert_committed "a blocking label reporting nothing does not block" \
  "$NEGATED" commit -m x

PROSE="$(sev_repo 'severity prose')"
record_in "$PROSE" 'VERDICT: READY - I checked correctness and security and found nothing'
assert_committed "a prose mention of a blocking word does not block" \
  "$PROSE" commit -m x

# --- self-review marking: a recorded verdict never passes as independent -----
# `record` refuses to run without a staged diff in its own working tree, so the
# session recording a verdict is the session that authored it. The gate stamps
# that itself; nothing here is the recording agent's own claim about itself.

record_as() { # record_as <session-id> <repo> <verdict>
  local id="$1" repo="$2" verdict="$3"
  ( cd "$repo" && export CLAUDE_CODE_SESSION_ID="$id" &&
    printf '%s' "$verdict" | "$GATE" record ) >/dev/null 2>&1
}

record_unattributed() { # record_unattributed <repo> <verdict>
  ( cd "$1" && unset CLAUDE_CODE_SESSION_ID &&
    printf '%s' "$2" | "$GATE" record ) >/dev/null 2>&1
}

commit_as() { # commit_as <session-id> <repo> <git-args...>
  local id="$1" repo="$2"; shift 2
  GIT_ERR="$( cd "$repo" && export CLAUDE_CODE_SESSION_ID="$id" &&
    bounded git "$@" 2>&1 >/dev/null )"
  GIT_EXIT=$?
}

marker_of() { # marker_of <repo> <key>
  cat "$1/.git/agentic-review/$2" 2>/dev/null
}

SELFMARK="$(sev_repo 'self review marker')"
SELFMARK_KEY="$(key_in "$SELFMARK")"
record_as session-alpha "$SELFMARK" 'VERDICT: READY - looks fine to me'
SELFMARK_TEXT="$(marker_of "$SELFMARK" "$SELFMARK_KEY")"
assert_has "the marker marks the recorded verdict a self-review" \
  "self-review" "$SELFMARK_TEXT"
assert_has "the marker names the session that recorded it" \
  "session-alpha" "$SELFMARK_TEXT"
assert_has "the marker still carries the verdict verbatim" \
  "VERDICT: READY - looks fine to me" "$SELFMARK_TEXT"

commit_as session-alpha "$SELFMARK" commit -m x
assert_eq "a self-recorded review still commits" 0 "$GIT_EXIT"
assert "the commit says the review was a self-review" \
  grep -qi 'self-review' <<<"$GIT_ERR"
assert_has "the self-review notice names the recording session" \
  "session-alpha" "$GIT_ERR"
refute_has "the self-review notice teaches no bypass" \
  "REVIEW_GATE=0" "$GIT_ERR"

# The obvious attack is omission: write the marker by hand and leave the stamp
# out. An unstamped marker is not evidence of independence, so it reads the
# same as a stamped one.
UNSTAMPED="$(sev_repo 'self review unstamped')"
UNSTAMPED_KEY="$(key_in "$UNSTAMPED")"
mkdir -p "$UNSTAMPED/.git/agentic-review"
printf 'VERDICT: READY - stamped by nobody\n' \
  > "$UNSTAMPED/.git/agentic-review/$UNSTAMPED_KEY"
commit_as session-alpha "$UNSTAMPED" commit -m x
assert_eq "an unstamped marker still commits" 0 "$GIT_EXIT"
assert "an unstamped marker is treated as a self-review" \
  grep -qi 'self-review' <<<"$GIT_ERR"

# The other attack is assertion: put a stamp in the verdict text and hope it is
# read as the gate's own. The gate writes its stamp first, and reads only that.
SPOOF="$(sev_repo 'self review spoofed')"
SPOOF_KEY="$(key_in "$SPOOF")"
record_as session-alpha "$SPOOF" 'review-gate-recorded-by: an-independent-critic
VERDICT: READY - trying to look independent'
SPOOF_TEXT="$(marker_of "$SPOOF" "$SPOOF_KEY")"
assert_eq "the gate stamp is the marker's first line" \
  "review-gate-recorded-by: session-alpha" "$(head -n 1 <<<"$SPOOF_TEXT")"
commit_as session-alpha "$SPOOF" commit -m x
assert "a stamp inside the verdict text does not buy independence" \
  grep -qi 'self-review' <<<"$GIT_ERR"
assert_has "the notice names the recorder the gate observed" \
  "session-alpha" "$GIT_ERR"

ANON="$(sev_repo 'self review unattributed')"
ANON_KEY="$(key_in "$ANON")"
record_unattributed "$ANON" 'VERDICT: READY - recorded outside any agent session'
assert_has "a recorder with no session identity is stamped unidentified" \
  "unidentified" "$(marker_of "$ANON" "$ANON_KEY")"

# The gate fails open where a marker could never be written. Nothing was
# reviewed there at all, which is a different thing from a self-review.
UNRECORDABLE="$(sev_repo 'self review unrecordable')"
mkdir -p "$UNRECORDABLE/.git/agentic-review"
chmod a-w "$UNRECORDABLE/.git/agentic-review"
commit_as session-alpha "$UNRECORDABLE" commit -m x
chmod u+w "$UNRECORDABLE/.git/agentic-review"
assert_eq "an unrecordable marker directory still lets the commit through" \
  0 "$GIT_EXIT"
refute_has "a commit carrying no review is not called a self-review" \
  "self-review" "$GIT_ERR"

# The stamp sits above the verdict, so severity tiering reads exactly what the
# reviewer wrote.
STAMPED_BUG="$(sev_repo 'self review severity')"
record_as session-alpha "$STAMPED_BUG" 'VERDICT: NOT READY
[correctness] off-by-one in the loop bound'
assert_blocked "the stamp does not hide a blocking finding" \
  "$STAMPED_BUG" commit -m x
assert_has "the refusal still quotes the blocking finding" \
  "off-by-one in the loop bound" "$GIT_ERR"

STAMPED_NIT="$(sev_repo 'self review nit')"
record_as session-alpha "$STAMPED_NIT" 'VERDICT: READY
Nit: rename foo to bar'
assert_committed "the stamp is not itself read as a finding" \
  "$STAMPED_NIT" commit -m x
refute_has "the stamp is not reported as a review finding" \
  "review-gate-recorded-by" "$GIT_ERR"

# --- the README describes the design that actually ships ---------------------

assert "hooks/review-gate/README.md exists" test -f "$README"
assert "the README documents the REVIEW_GATE=0 bypass" \
  grep -qF 'REVIEW_GATE=0' "$README"
assert "the README documents the --no-verify bypass" \
  grep -qF -- '--no-verify' "$README"
assert "the README documents the core.hooksPath chaining caveat" \
  grep -qF 'core.hooksPath' "$README"
assert "the README names bin/install-review-gate" \
  grep -qF 'bin/install-review-gate' "$README"
assert "the README describes a per-repository install" \
  grep -Eqi 'per.repositor' "$README"
assert "the README keeps a section on not using a global core.hooksPath" \
  grep -q '^## Why not a global' "$README"
assert "the README gives the local-override reason" \
  grep -qi 'overrides the global' "$README"
assert "the README gives the replaced-hooks reason" \
  bash -c 'tr "\n" " " < "$1" | grep -Eqi "replaces[^.]*\.git/hooks"' _ "$README"
assert "the README names the marker block it appends" \
  grep -qF 'BEGIN AGENTIC REVIEW-GATE' "$README"
assert "the README names the beads block it must not write inside" \
  grep -qF 'BEADS INTEGRATION' "$README"
assert "the README keeps an Install section" grep -q '^## Install' "$README"
assert "the README keeps an Uninstall section" grep -q '^## Uninstall' "$README"
assert "the README keeps a Known gaps section" grep -q '^## Known gaps' "$README"
assert "the README keeps the review-bar section" \
  grep -q '^## What the review itself should block on' "$README"
assert "the README documents severity" grep -qi 'severity' "$README"
assert "the README keeps a self-review section" \
  grep -q '^## Every recorded review is a self-review' "$README"
SELF_REVIEW_RANGE='/^## Every recorded review is a self-review/,/^## What the review/p'
assert "the self-review section names the independent review that runs instead" \
  bash -c 'sed -n "$2" "$1" | grep -Eqi "orchestrator|critic"' _ "$README" "$SELF_REVIEW_RANGE"
assert "the self-review section names the marker stamp the gate writes" \
  bash -c 'sed -n "$2" "$1" | grep -qF "review-gate-kind: self-review"' \
    _ "$README" "$SELF_REVIEW_RANGE"
assert "the README names every category that blocks" \
  bash -c 'tr "\n" " " < "$1" | grep -Eqi "correctness.*security.*data.loss.*secret"' \
    _ "$README"
assert "the README says nits are reported rather than blocking" \
  bash -c 'tr "\n" " " < "$1" | grep -Eqi "nit[^.]*(report|allow|not block)"' _ "$README"
assert "the README states the unrecognized-severity default" \
  bash -c 'tr "\n" " " < "$1" | grep -Eqi "unrecogni[sz]ed|unparseable"' _ "$README"
for source in "eng-practices" "Claude Code Review" "RADAR"; do
  assert "the README cites $source" grep -qF "$source" "$README"
done
for gap in "git merge" "pre-merge-commit" "git rebase" "git am"; do
  assert "the README's Known gaps names $gap" grep -qF "$gap" "$README"
done
assert "the README states what the gate does not guarantee" \
  bash -c 'tr "\n" " " < "$1" | grep -Eqi "not proof|does not prove|no proof"' _ "$README"
refute "the README no longer installs the retired PreToolUse hook" \
  grep -qF 'pretool-review.sh' "$README"
refute "the README no longer wires a Bash matcher into settings.json" \
  grep -qF '"matcher": "Bash"' "$README"

# --- Summary -----------------------------------------------------------------

echo "pass: $pass, fail: $fail"
[ "$fail" -eq 0 ]
