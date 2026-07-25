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

# --- bin/install-review-gate -------------------------------------------------
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
  sandboxed() { # sandboxed <command...>
    HOME="$FAKEHOME" GIT_CONFIG_GLOBAL="$FAKECONFIG" "$@"
  }
  global_hookspath() {
    GIT_CONFIG_GLOBAL="$FAKECONFIG" git config --global --get core.hooksPath 2>/dev/null
  }

  IDIR="$TMP/installed hooks"
  INS_OUT="$(sandboxed "$INSTALLER" install "$IDIR" 2>&1)"
  assert_eq "install exits 0" 0 "$?"
  assert "install puts an executable pre-commit in the hooks dir" \
    test -x "$IDIR/pre-commit"
  assert_eq "install points core.hooksPath at the hooks dir" \
    "$IDIR" "$(global_hookspath)"

  sandboxed "$INSTALLER" install "$IDIR" >/dev/null 2>&1
  assert_eq "install is idempotent" 0 "$?"
  assert_eq "a second install leaves core.hooksPath alone" \
    "$IDIR" "$(global_hookspath)"

  STATUS_OUT="$(sandboxed "$INSTALLER" status 2>&1)"
  assert_eq "status exits 0 when installed" 0 "$?"
  assert_has "status reports the hooks dir" "$IDIR" "$STATUS_OUT"
  assert "status reports that it is installed" \
    grep -Eqi 'installed: *yes' <<<"$STATUS_OUT"

  # An installed hook gates a real commit through the global config alone.
  GLOBALLY="$TMP/globally gated"
  mkdir -p "$GLOBALLY"
  sandboxed git init -q "$GLOBALLY"
  sandboxed git -C "$GLOBALLY" config user.email t@e.com
  sandboxed git -C "$GLOBALLY" config user.name t
  printf 'one\n' > "$GLOBALLY/a.txt"
  sandboxed git -C "$GLOBALLY" add a.txt
  ( cd "$GLOBALLY" && sandboxed bounded git commit -m x ) >/dev/null 2>&1
  assert_ne "an installed hook gates a repo with no local config" 0 "$?"
  assert_eq "no commit was created under the installed hook" \
    "0" "$(commits_in "$GLOBALLY")"

  # A foreign core.hooksPath is refused, never clobbered.
  FOREIGN="$TMP/foreign hooks"
  mkdir -p "$FOREIGN"
  GIT_CONFIG_GLOBAL="$FAKECONFIG" git config --global core.hooksPath "$FOREIGN"
  REFUSE_OUT="$(sandboxed "$INSTALLER" install "$IDIR" 2>&1)"
  assert_ne "install refuses a foreign core.hooksPath" 0 "$?"
  assert_has "the refusal names core.hooksPath" "core.hooksPath" "$REFUSE_OUT"
  assert_eq "the foreign core.hooksPath is left untouched" \
    "$FOREIGN" "$(global_hookspath)"

  sandboxed "$INSTALLER" uninstall >/dev/null 2>&1
  assert_eq "uninstall leaves a foreign core.hooksPath set" \
    "$FOREIGN" "$(global_hookspath)"

  GIT_CONFIG_GLOBAL="$FAKECONFIG" git config --global core.hooksPath "$IDIR"
  sandboxed "$INSTALLER" uninstall >/dev/null 2>&1
  assert_eq "uninstall exits 0" 0 "$?"
  assert_eq "uninstall unsets our core.hooksPath" "" "$(global_hookspath)"
  refute "uninstall removes the hook" test -e "$IDIR/pre-commit"

  STATUS_OUT="$(sandboxed "$INSTALLER" status 2>&1)"
  assert "status reports that it is not installed" \
    grep -Eqi 'installed: *no' <<<"$STATUS_OUT"

  # A moved toolkit checkout leaves a dangling symlink. Uninstall must still
  # clear core.hooksPath, or every repository's own hooks stay disabled with
  # no supported way back.
  sandboxed "$INSTALLER" install "$IDIR" >/dev/null 2>&1
  ln -sfn "$TMP/moved away/hooks/review-gate/pre-commit" "$IDIR/pre-commit"
  sandboxed "$INSTALLER" uninstall >/dev/null 2>&1
  assert_eq "uninstall exits 0 with a dangling hook symlink" 0 "$?"
  assert_eq "uninstall clears core.hooksPath for a dangling symlink" \
    "" "$(global_hookspath)"
  refute "uninstall removes the dangling symlink" test -L "$IDIR/pre-commit"

  # Install warns that a global hooks path retires every other hook type.
  INS_OUT="$(sandboxed "$INSTALLER" install "$IDIR" 2>&1)"
  assert_has "install warns about non-pre-commit hooks" "commit-msg" "$INS_OUT"
  sandboxed "$INSTALLER" uninstall >/dev/null 2>&1
else
  echo "SKIP: git does not honor GIT_CONFIG_GLOBAL; installer assertions skipped" >&2
fi

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
assert "the README keeps an Install section" grep -q '^## Install' "$README"
assert "the README keeps an Uninstall section" grep -q '^## Uninstall' "$README"
assert "the README keeps a Known gaps section" grep -q '^## Known gaps' "$README"
assert "the README keeps the review-bar section" \
  grep -q '^## What the review itself should block on' "$README"
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
