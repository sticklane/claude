#!/usr/bin/env bash
# Tests for bin/review-gate and hooks/review-gate/pretool-review.sh — the
# mechanical gate that blocks `git commit` until an adversarial review has
# been recorded against the exact staged diff. Runs against a throwaway
# fixture repo in a temp dir; never touches this toolkit's own .git.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$TOOLKIT_DIR/bin/review-gate"
HOOK="$TOOLKIT_DIR/hooks/review-gate/pretool-review.sh"

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

refute() { # refute <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $desc (command unexpectedly succeeded)" >&2
  else
    pass=$((pass + 1))
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Fixture repo (name contains a space: paths must be space-safe throughout).
REPO="$TMP/gate repo"
mkdir -p "$REPO/sub dir"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name test

# run_gate <subcommand> [stdin] [cwd] -> RG_EXIT / RG_OUT / RG_ERR
run_gate() {
  local sub="$1" stdin="${2:-}" cwd="${3:-$REPO}"
  local out_f="$TMP/.rg_out" err_f="$TMP/.rg_err"
  (
    cd "$cwd" || exit 97
    printf '%s' "$stdin" | "$GATE" "$sub" >"$out_f" 2>"$err_f"
  )
  RG_EXIT=$?
  RG_OUT="$(cat "$out_f")"
  RG_ERR="$(cat "$err_f")"
}

# run_hook <stdin> [cwd] -> RH_EXIT / RH_OUT / RH_ERR. Honors HOOK_PATH.
run_hook() {
  local stdin="$1" cwd="${2:-$REPO}" script="${HOOK_SCRIPT:-$HOOK}"
  local out_f="$TMP/.rh_out" err_f="$TMP/.rh_err"
  (
    cd "$cwd" || exit 97
    [ -n "${HOOK_PATH:-}" ] && export PATH="$HOOK_PATH"
    printf '%s' "$stdin" | "$script" >"$out_f" 2>"$err_f"
  )
  RH_EXIT=$?
  RH_OUT="$(cat "$out_f")"
  RH_ERR="$(cat "$err_f")"
}

hook_json() { # hook_json <command>
  jq -nc --arg cmd "$1" --arg cwd "$REPO" \
    '{tool_name: "Bash", tool_input: {command: $cmd}, cwd: $cwd}'
}

hook_decision() {
  printf '%s' "$RH_OUT" | jq -r '.hookSpecificOutput.permissionDecision // empty' 2>/dev/null
}

hook_reason() {
  printf '%s' "$RH_OUT" | jq -r '.hookSpecificOutput.permissionDecisionReason // empty' 2>/dev/null
}

# --- Files exist and are executable ------------------------------------------

assert "bin/review-gate exists and is executable" test -x "$GATE"
assert "pretool-review.sh exists and is executable" test -x "$HOOK"

# --- key: empty staged diff --------------------------------------------------

run_gate key
assert_eq "key exits 1 with an empty staged diff" 1 "$RG_EXIT"
assert_eq "key prints nothing with an empty staged diff" "" "$RG_OUT"

# --- check: no staged diff at all allows -------------------------------------

run_gate check
assert_eq "check exits 0 when nothing is staged" 0 "$RG_EXIT"

# --- key: stable for the same staged diff ------------------------------------

echo "one" > "$REPO/a.txt"
git -C "$REPO" add a.txt
run_gate key
KEY1="$RG_OUT"
assert_eq "key exits 0 with a staged diff" 0 "$RG_EXIT"
assert "key is 16 hex characters" grep -Eqx '[0-9a-f]{16}' <<<"$KEY1"

run_gate key
assert_eq "key is stable for the same staged diff" "$KEY1" "$RG_OUT"

# key is identical when computed from a subdirectory of the same repo
run_gate key "" "$REPO/sub dir"
assert_eq "key is identical from a repo subdirectory" "$KEY1" "$RG_OUT"

# --- check fails before record, passes after ---------------------------------

run_gate check
assert_eq "check exits 1 before any review is recorded" 1 "$RG_EXIT"

run_gate record ""
assert_eq "record refuses empty stdin (exit 1)" 1 "$RG_EXIT"
assert "record refusal explains itself on stderr" test -n "$RG_ERR"

run_gate check
assert_eq "check still fails after a refused record" 1 "$RG_EXIT"

STATUS_BEFORE="$(git -C "$REPO" status --porcelain)"
run_gate record "VERDICT: READY - no blocking findings"
assert_eq "record exits 0 with a verdict on stdin" 0 "$RG_EXIT"

run_gate check
assert_eq "check exits 0 once a review is recorded" 0 "$RG_EXIT"

# --- markers live inside the git common dir, never in the worktree -----------

MARKER="$REPO/.git/agentic-review/$KEY1"
assert "marker written under the git common dir" test -f "$MARKER"
assert "marker carries the recorded verdict" grep -q "VERDICT: READY" "$MARKER"
assert_eq "git status is unchanged by recording" \
  "$STATUS_BEFORE" "$(git -C "$REPO" status --porcelain)"

# --- a stale marker must not authorize a different staged diff ---------------

echo "two" >> "$REPO/a.txt"
git -C "$REPO" add a.txt
run_gate key
KEY2="$RG_OUT"
assert_ne "key changes when the staged diff changes" "$KEY1" "$KEY2"

run_gate check
assert_eq "check fails again once more changes are staged" 1 "$RG_EXIT"

# --- hook: denies commits without a recorded review --------------------------

hook_denies() { # hook_denies <description> <command>
  run_hook "$(hook_json "$2")"
  assert_eq "$1: exit 0" 0 "$RH_EXIT"
  assert_eq "$1: permissionDecision deny" "deny" "$(hook_decision)"
  assert_eq "$1: hookEventName PreToolUse" "PreToolUse" \
    "$(printf '%s' "$RH_OUT" | jq -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null)"
  assert "$1: reason names the staged key" grep -qF "$KEY2" <<<"$(hook_reason)"
  assert "$1: reason names the record command" \
    grep -qF "review-gate record" <<<"$(hook_reason)"
  assert "$1: reason names an adversarial review path" \
    grep -Eq "critic|code-review" <<<"$(hook_reason)"
}

hook_allows() { # hook_allows <description> <command>
  run_hook "$(hook_json "$2")"
  assert_eq "$1: exit 0" 0 "$RH_EXIT"
  assert_eq "$1: no output (allow)" "" "$RH_OUT"
}

hook_denies "plain commit" "git commit -m x"
hook_denies "bare commit" "git commit"
hook_denies "commit after &&" "cd /x && git commit -m y"
hook_denies "commit after ;" "echo hi; git commit -m y"
hook_denies "commit with -C into the repo" "git -C \"$REPO\" commit -m y"
hook_denies "commit with global flags" "git --no-pager -c user.name=a commit -m y"
hook_denies "commit piped after another command" "true | git commit -m y"

hook_allows "git status" "git status"
hook_allows "git log --oneline" "git log --oneline"
hook_allows "git log with commit in a format string" "git log --format=%H-commit-%s"
hook_allows "git commit-graph" "git commit-graph write"
hook_allows "pre-commit runner" "pre-commit run --all-files"
hook_allows "precommit npm script" "npm run precommit"
hook_allows "commit inside a quoted argument" 'echo "git commit -m x"'
hook_allows "commit inside a single-quoted argument" "grep 'git commit' notes.txt"

# --- hook: allows a commit once the review is recorded -----------------------

run_gate record "VERDICT: READY - second pass"
assert_eq "record exits 0 for the new staged key" 0 "$RG_EXIT"
hook_allows "commit with a recorded review" "git commit -m x"

# --- hook: fail-open boundaries ----------------------------------------------

# Re-stage so the gate would otherwise deny, proving fail-open is what allows.
echo "three" >> "$REPO/a.txt"
git -C "$REPO" add a.txt
run_gate check
assert_eq "check fails for the third staged diff" 1 "$RG_EXIT"

NOJQ="$TMP/nojq"
mkdir -p "$NOJQ"
for b in git shasum cut mkdir cat sed grep dirname basename; do
  ln -sf "/usr/bin/$b" "$NOJQ/$b" 2>/dev/null || true
done
ln -sf /bin/bash "$NOJQ/bash"
[ -x "$NOJQ/cat" ] || ln -sf /bin/cat "$NOJQ/cat"
[ -x "$NOJQ/mkdir" ] || ln -sf /bin/mkdir "$NOJQ/mkdir"
[ -x "$NOJQ/sed" ] || ln -sf /usr/bin/sed "$NOJQ/sed"

HOOK_PATH="$NOJQ" run_hook "$(hook_json "git commit -m x")"
assert_eq "hook exits 0 when jq is unavailable" 0 "$RH_EXIT"
assert_eq "hook emits no deny JSON when jq is unavailable" "" "$RH_OUT"
unset HOOK_PATH

run_hook "this is not json {"
assert_eq "hook exits 0 on malformed JSON" 0 "$RH_EXIT"
assert_eq "hook emits no deny JSON on malformed JSON" "" "$RH_OUT"

run_hook ""
assert_eq "hook exits 0 on empty stdin" 0 "$RH_EXIT"
assert_eq "hook emits no deny JSON on empty stdin" "" "$RH_OUT"

# not a git repo -> fail open
NOTREPO="$TMP/not a repo"
mkdir -p "$NOTREPO"
run_hook "$(jq -nc --arg cmd "git commit -m x" --arg cwd "$NOTREPO" \
  '{tool_name: "Bash", tool_input: {command: $cmd}, cwd: $cwd}')" "$NOTREPO"
assert_eq "hook exits 0 outside a git repo" 0 "$RH_EXIT"
assert_eq "hook emits no deny JSON outside a git repo" "" "$RH_OUT"

# review-gate not findable (hook copied away from bin/, and not on PATH)
LONELY="$TMP/lonely hook"
mkdir -p "$LONELY"
cp "$HOOK" "$LONELY/pretool-review.sh"
chmod 755 "$LONELY/pretool-review.sh"
# PATH is scrubbed of any directory shipping review-gate, so this still
# exercises fail-open once the gate is installed on PATH machine-wide.
SCRUBBED=""
IFS=: read -r -a _pdirs <<< "$PATH"
for _d in "${_pdirs[@]}"; do
  [ -x "$_d/review-gate" ] && continue
  SCRUBBED="${SCRUBBED:+$SCRUBBED:}$_d"
done
HOOK_SCRIPT="$LONELY/pretool-review.sh" HOOK_PATH="$SCRUBBED" \
  run_hook "$(hook_json "git commit -m x")"
assert_eq "hook exits 0 when review-gate cannot be located" 0 "$RH_EXIT"
assert_eq "hook emits no deny JSON when review-gate is missing" "" "$RH_OUT"
assert "hook says why it allowed when review-gate is missing" \
  bash -c 'printf %s "$1" | grep -q "review-gate not found"' _ "$RH_ERR"
unset HOOK_SCRIPT HOOK_PATH

# a non-Bash tool call is never a commit
run_hook '{"tool_name": "Edit", "tool_input": {"file_path": "/tmp/x"}}'
assert_eq "hook exits 0 for a non-Bash tool call" 0 "$RH_EXIT"
assert_eq "hook emits no deny JSON for a non-Bash tool call" "" "$RH_OUT"


# --- bypass regressions: the key covers what the commit WOULD contain --------
# `git commit -a` and `git commit --amend` both produce a commit from content
# the index does not hold, so keying on the index alone let them through.
BR="$TMP/bypass"
mkdir -p "$BR"
git -C "$BR" init -q
git -C "$BR" config user.email t@e.com
git -C "$BR" config user.name t
echo one > "$BR/f.txt"
git -C "$BR" add -A
git -C "$BR" commit -qm first

gate_in() { # gate_in <cwd> <args...>
  local cwd="$1"; shift
  ( cd "$cwd" && "$GATE" "$@" 2>/dev/null )
}
hook_in() { # hook_in <cwd> <command>
  local cwd="$1" cmd="$2"
  RH_OUT="$( jq -nc --arg cmd "$cmd" --arg cwd "$cwd" \
      '{tool_name:"Bash", tool_input:{command:$cmd}, cwd:$cwd}' \
    | ( cd "$cwd" && "$HOOK" 2>/dev/null ) )"
}

echo two > "$BR/f.txt"
assert_eq "plain key is empty when nothing is staged" "" "$(gate_in "$BR" key)"
assert "--all key is non-empty for tracked-but-unstaged changes" \
  test -n "$(gate_in "$BR" key --all)"
hook_in "$BR" 'git commit -am wip'
assert_eq "commit -a is denied despite an empty index" "deny" "$(hook_decision)"

git -C "$BR" checkout -q -- f.txt
assert "--amend key is non-empty on a clean index" \
  test -n "$(gate_in "$BR" key --amend)"
hook_in "$BR" 'git commit --amend --no-edit'
assert_eq "commit --amend is denied on a clean index" "deny" "$(hook_decision)"

printf 'reviewed' | ( cd "$BR" && "$GATE" record --amend ) >/dev/null 2>&1
hook_in "$BR" 'git commit --amend --no-edit'
assert_eq "amend allowed once its own review is recorded" "" "$(hook_decision)"
echo three > "$BR/f.txt"
git -C "$BR" add -A
hook_in "$BR" 'git commit -m other'
assert_eq "an amend review does not authorize a different staged commit" "deny" "$(hook_decision)"


# --- `-a` key must equal HEAD..worktree, not index..worktree ----------------
# Staged content is part of what `git commit -a` writes, so a review recorded
# against only the unstaged hunk must not authorize it.
MX="$TMP/mixed"
mkdir -p "$MX"
git -C "$MX" init -q
git -C "$MX" config user.email t@e.com
git -C "$MX" config user.name t
printf 'base\n' > "$MX/f.txt"
printf 'base\n' > "$MX/g.txt"
git -C "$MX" add -A
git -C "$MX" commit -qm first

printf 'SECRET_BACKDOOR\n' > "$MX/f.txt"
git -C "$MX" add f.txt          # staged
printf 'harmless\n' > "$MX/g.txt"  # unstaged

assert_ne "key --all differs from key when both staged and unstaged exist" \
  "$(gate_in "$MX" key)" "$(gate_in "$MX" key --all)"
# Coverage, not mere non-emptiness: the --all key is the digest of the whole
# HEAD..worktree diff, which contains both the staged and the unstaged file.
MX_ALL_DIFF="$( cd "$MX" && git diff HEAD )"
assert "the HEAD..worktree diff holds the staged file" \
  grep -q 'SECRET_BACKDOOR' <<<"$MX_ALL_DIFF"
assert "the HEAD..worktree diff holds the unstaged file" \
  grep -q 'harmless' <<<"$MX_ALL_DIFF"
assert_eq "key --all is the digest of that whole diff" \
  "$( cd "$MX" && git diff HEAD | shasum -a 256 | cut -c1-16 )" \
  "$(gate_in "$MX" key --all)"

# Record a review of the unstaged hunk only, then attempt `git commit -a`.
printf 'reviewed the harmless change' | ( cd "$MX" && "$GATE" record ) >/dev/null 2>&1
hook_in "$MX" 'git commit -am wip'
assert_eq "a review of the staged-only diff does not authorize commit -a" \
  "deny" "$(hook_decision)"

# And with a clean worktree but a staged change, commit -a must still be gated.
MX2="$TMP/mixed2"
mkdir -p "$MX2"
git -C "$MX2" init -q
git -C "$MX2" config user.email t@e.com
git -C "$MX2" config user.name t
printf 'base\n' > "$MX2/f.txt"
git -C "$MX2" add -A
git -C "$MX2" commit -qm first
printf 'staged-only\n' > "$MX2/f.txt"
git -C "$MX2" add f.txt
hook_in "$MX2" 'git commit -am wip'
assert_eq "commit -a with a staged change and clean worktree is denied" \
  "deny" "$(hook_decision)"


# --- `git -C <other>` is decided against <other>, not the hook's cwd --------
OTHER="$TMP/other repo"
mkdir -p "$OTHER"
git -C "$OTHER" init -q
git -C "$OTHER" config user.email t@e.com
git -C "$OTHER" config user.name t
echo seed > "$OTHER/s.txt"
git -C "$OTHER" add -A
git -C "$OTHER" commit -qm seed
# $OTHER has nothing staged, so a commit there needs no review even though the
# hook's own cwd repo has an unreviewed staged diff.
RH_OUT="$( jq -nc --arg cmd "git -C \"$OTHER\" commit -m x" --arg cwd "$REPO" \
    '{tool_name:"Bash", tool_input:{command:$cmd}, cwd:$cwd}' \
  | "$HOOK" 2>/dev/null )"
assert_eq "a clean -C target is not denied because of the cwd repo" \
  "" "$(hook_decision)"
# Stage something in $OTHER: now it must be denied, on ITS key.
echo change > "$OTHER/s.txt"
git -C "$OTHER" add -A
RH_OUT="$( jq -nc --arg cmd "git -C \"$OTHER\" commit -m x" --arg cwd "$REPO" \
    '{tool_name:"Bash", tool_input:{command:$cmd}, cwd:$cwd}' \
  | "$HOOK" 2>/dev/null )"
assert_eq "a dirty -C target is denied" "deny" "$(hook_decision)"
OTHER_KEY="$(cd "$OTHER" && "$GATE" key 2>/dev/null)"
assert "the deny names the -C target's own key" \
  grep -qF "$OTHER_KEY" <<<"$(hook_reason)"
refute "the deny does not name the hook cwd repo's key" \
  grep -qF "$(cd "$REPO" && "$GATE" key 2>/dev/null)" <<<"$(hook_reason)"
# Following the deny's own instructions must land the marker in $OTHER, not in
# whatever directory the agent happens to stand in.
assert "the record command in the deny cds into the -C target" \
  grep -qF "cd \"$OTHER\" &&" <<<"$(hook_reason)"

# --- pathspec commits bypass the index entirely ------------------------------
# `git commit -m x f.txt` takes content from the worktree, so `git diff --cached`
# is empty and the gate would key on nothing. Such commits are never gated.
PS="$TMP/pathspec"
mkdir -p "$PS"
git -C "$PS" init -q
git -C "$PS" config user.email t@e.com
git -C "$PS" config user.name t
printf 'base\n' > "$PS/f.txt"
git -C "$PS" add -A
git -C "$PS" commit -qm first
printf 'unreviewed\n' > "$PS/f.txt"   # worktree only; the index stays clean

pathspec_denies() { # pathspec_denies <description> <command>
  hook_in "$PS" "$2"
  assert_eq "$1: denied" "deny" "$(hook_decision)"
  assert "$1: reason explains the pathspec" \
    grep -qi "pathspec" <<<"$(hook_reason)"
}

no_pathspec_allows() { # no_pathspec_allows <description> <command>
  hook_in "$PS" "$2"
  assert_eq "$1: allowed (flag value is not a pathspec)" "" "$(hook_decision)"
}

pathspec_denies "trailing pathspec" "git commit -m x f.txt"
pathspec_denies "pathspec after --" "git commit -m x -- f.txt"
pathspec_denies "bare commit with only a pathspec" "git commit f.txt"
pathspec_denies "amend with a pathspec" "git commit --amend --no-edit f.txt"
pathspec_denies "attached short value then pathspec" "git commit -mwip f.txt"
pathspec_denies "pathspec with a quoted space" "git commit -m x \"sub dir/f.txt\""

no_pathspec_allows "-m value" "git commit -m x"
no_pathspec_allows "--message value" "git commit --message x"
no_pathspec_allows "-F value" "git commit -F msg.txt"
no_pathspec_allows "--file value" "git commit --file msg.txt"
no_pathspec_allows "--author value" "git commit --author \"A U <a@u>\" -m x"
no_pathspec_allows "--date value" "git commit --date 2020-01-01 -m x"
no_pathspec_allows "-C reuse-message value" "git commit -C HEAD"
no_pathspec_allows "-c reedit-message value" "git commit -c HEAD"
no_pathspec_allows "--squash value" "git commit --squash HEAD"
no_pathspec_allows "--fixup value" "git commit --fixup HEAD"
no_pathspec_allows "-t template value" "git commit -t tpl.txt"
no_pathspec_allows "--cleanup value" "git commit --cleanup strip -m x"
no_pathspec_allows "--pathspec-from-file value" "git commit --pathspec-from-file list.txt"
no_pathspec_allows "-S with no value" "git commit -S -m x"
no_pathspec_allows "--gpg-sign with attached value" "git commit --gpg-sign=KEYID -m x"
no_pathspec_allows "-u with no value" "git commit -u -m x"
no_pathspec_allows "--untracked-files attached" "git commit --untracked-files=no -m x"
no_pathspec_allows "trailing -- with nothing after it" "git commit -m x --"
no_pathspec_allows "--message= attached value" "git commit --message=x"

# A bundled `-am wip` message value must not be read as a pathspec: the deny
# there is the ordinary review deny.
hook_in "$PS" 'git commit -am wip'
assert_eq "commit -am is denied on unstaged tracked changes" "deny" "$(hook_decision)"
refute "the -am deny is a review deny, not a pathspec deny" \
  grep -qi "pathspec" <<<"$(hook_reason)"

# --- heredoc bodies are data, not commands -----------------------------------
# A script being WRITTEN by a heredoc may contain the text `git commit`; that is
# not a commit. A real commit after the heredoc terminator still is.
HD="$TMP/heredoc"
mkdir -p "$HD"
git -C "$HD" init -q
git -C "$HD" config user.email t@e.com
git -C "$HD" config user.name t
printf 'base\n' > "$HD/f.txt"
git -C "$HD" add -A   # staged and unreviewed: a real commit here denies

hd_allows() { # hd_allows <description> <command>
  hook_in "$HD" "$2"
  assert_eq "$1: allowed" "" "$(hook_decision)"
}
hd_denies() { # hd_denies <description> <command>
  hook_in "$HD" "$2"
  assert_eq "$1: denied" "deny" "$(hook_decision)"
}

hd_denies "plain commit in the heredoc fixture" 'git commit -m x'
hd_allows "unquoted heredoc body mentioning git commit" \
  "$(printf 'cat > setup.sh <<EOF\ngit commit -m x\nEOF\n')"
hd_allows "single-quoted heredoc delimiter" \
  "$(printf "cat > setup.sh <<'EOF'\ngit commit -m x\nEOF\n")"
hd_allows "double-quoted heredoc delimiter" \
  "$(printf 'cat > setup.sh <<"EOF"\ngit commit -m x\nEOF\n')"
hd_allows "<<- heredoc with a tab-indented terminator" \
  "$(printf 'cat > setup.sh <<-EOF\n\tgit commit -m x\n\tEOF\n')"
hd_allows "heredoc whose body holds the delimiter as a substring" \
  "$(printf 'cat > setup.sh <<MARK\ngit commit -m MARKER\nMARK\n')"
hd_denies "a real commit after a heredoc block" \
  "$(printf 'cat > setup.sh <<EOF\nhello\nEOF\ngit commit -m x\n')"
hd_denies "a real commit after a quoted-delimiter heredoc block" \
  "$(printf "cat > setup.sh <<'EOF'\nhello\nEOF\ngit commit -m x\n")"
hd_denies "a real commit after a <<- heredoc block" \
  "$(printf 'cat > setup.sh <<-EOF\n\thello\n\tEOF\ngit commit -m x\n')"
hd_denies "a here-string is not a heredoc" 'git commit -m x <<<data'

# --- "cannot compute" is not "nothing to review" -----------------------------
# A repository with no HEAD, and a machine with no digest tool, both used to
# turn the gate off silently.
INIT="$TMP/initial commit"
mkdir -p "$INIT"
git -C "$INIT" init -q
git -C "$INIT" config user.email t@e.com
git -C "$INIT" config user.name t
printf 'first\n' > "$INIT/f.txt"
git -C "$INIT" add -A

assert "key --all is non-empty before any commit exists" \
  test -n "$(gate_in "$INIT" key --all)"
hook_in "$INIT" 'git commit -am initial'
assert_eq "the very first commit -am is denied" "deny" "$(hook_decision)"
printf 'reviewed the initial import' | \
  ( cd "$INIT" && "$GATE" record --all ) >/dev/null 2>&1
hook_in "$INIT" 'git commit -am initial'
assert_eq "the very first commit -am is allowed once reviewed" "" "$(hook_decision)"

# A PATH with neither shasum nor sha256sum: the gate cannot compute a key, so
# it must say so and deny rather than allow everything machine-wide.
stock_path_dir() { # stock_path_dir <dir> <binary...>
  local dir="$1" b src; shift
  mkdir -p "$dir"
  for b in "$@"; do
    src="$(command -v "$b" 2>/dev/null)" && ln -sf "$src" "$dir/$b"
  done
  ln -sf /bin/bash "$dir/bash"
}

NODIGEST="$TMP/nodigest"
stock_path_dir "$NODIGEST" git cut dirname mkdir cat basename head awk jq
( cd "$INIT" && PATH="$NODIGEST" "$GATE" check ) \
  >"$TMP/.nd_out" 2>"$TMP/.nd_err"
ND_EXIT=$?
assert_ne "check does not exit 0 when no digest tool exists" 0 "$ND_EXIT"
assert "check names the missing digest tool on stderr" \
  grep -Eq "sha256sum|shasum" "$TMP/.nd_err"

HOOK_PATH="$NODIGEST" run_hook "$(hook_json "git commit -m x")"
assert_eq "the hook denies when the key cannot be computed" \
  "deny" "$(hook_decision)"
unset HOOK_PATH

# The digest falls back to sha256sum when shasum is missing.
SHA256ONLY="$TMP/sha256only"
stock_path_dir "$SHA256ONLY" git cut dirname mkdir cat basename head awk sha256sum
if [ ! -e "$SHA256ONLY/sha256sum" ]; then
  printf '#!/bin/sh\nexec %s -a 256 "$@"\n' "$(command -v shasum)" \
    > "$SHA256ONLY/sha256sum"
  chmod 755 "$SHA256ONLY/sha256sum"
fi
assert_eq "key falls back to sha256sum when shasum is absent" \
  "$(gate_in "$INIT" key)" \
  "$( cd "$INIT" && PATH="$SHA256ONLY" "$GATE" key 2>/dev/null )"

# --- checking must not have side effects -------------------------------------
FRESH="$TMP/fresh probe"
mkdir -p "$FRESH"
git -C "$FRESH" init -q
git -C "$FRESH" config user.email t@e.com
git -C "$FRESH" config user.name t
printf 'x\n' > "$FRESH/f.txt"
git -C "$FRESH" add -A
run_gate check "" "$FRESH"
assert_eq "check exits 1 in the fresh probe repo" 1 "$RG_EXIT"
refute "check creates no marker directory" test -e "$FRESH/.git/agentic-review"

# An unwritable marker location must allow rather than wedge the repository.
UNWRITABLE="$TMP/unwritable"
mkdir -p "$UNWRITABLE"
git -C "$UNWRITABLE" init -q
git -C "$UNWRITABLE" config user.email t@e.com
git -C "$UNWRITABLE" config user.name t
printf 'x\n' > "$UNWRITABLE/f.txt"
git -C "$UNWRITABLE" add -A
run_gate check "" "$UNWRITABLE"
assert_eq "check denies while the marker location is writable" 1 "$RG_EXIT"
chmod 500 "$UNWRITABLE/.git"
run_gate check "" "$UNWRITABLE"
assert_eq "check allows when the marker cannot be written" 0 "$RG_EXIT"
chmod 700 "$UNWRITABLE/.git"

# --- REVIEW_GATE=0 is the deliberate bypass ----------------------------------
run_gate_env() { # run_gate_env <env-assignment> <subcommand> <cwd>
  ( cd "$3" && env "$1" "$GATE" "$2" ) >/dev/null 2>&1
  RG_EXIT=$?
}
run_gate check "" "$FRESH"
assert_eq "check denies the fresh probe repo without the bypass" 1 "$RG_EXIT"
run_gate_env "REVIEW_GATE=0" check "$FRESH"
assert_eq "REVIEW_GATE=0 makes check exit 0" 0 "$RG_EXIT"

hook_bypassed() { # hook_bypassed <description> <cwd> <command>
  RH_OUT="$( jq -nc --arg cmd "$3" --arg cwd "$2" \
      '{tool_name:"Bash", tool_input:{command:$cmd}, cwd:$cwd}' \
    | ( cd "$2" && REVIEW_GATE=0 "$HOOK" 2>/dev/null ) )"
  assert_eq "$1" "" "$(hook_decision)"
}
hook_bypassed "REVIEW_GATE=0 bypasses the hook's review deny" "$FRESH" 'git commit -m x'
hook_bypassed "REVIEW_GATE=0 bypasses the hook's pathspec deny" "$PS" 'git commit -m x f.txt'

# --- `git commit -a --amend` is keyed on HEAD^..worktree ---------------------
AA="$TMP/amend all"
mkdir -p "$AA"
git -C "$AA" init -q
git -C "$AA" config user.email t@e.com
git -C "$AA" config user.name t
printf 'one\n' > "$AA/f.txt"
git -C "$AA" add -A
git -C "$AA" commit -qm first
printf 'two\n' > "$AA/f.txt"   # tracked, unstaged
hook_in "$AA" 'git commit -a --amend --no-edit'
assert_eq "commit -a --amend is denied" "deny" "$(hook_decision)"
assert "the -a --amend deny names both gate flags" \
  grep -qF "record --all --amend" <<<"$(hook_reason)"
printf 'reviewed the amended tree' | \
  ( cd "$AA" && "$GATE" record --all --amend ) >/dev/null 2>&1
hook_in "$AA" 'git commit -a --amend --no-edit'
assert_eq "commit -a --amend is allowed once its own review is recorded" \
  "" "$(hook_decision)"
hook_in "$AA" 'git commit -am wip'
assert_eq "an -a --amend review does not authorize a plain commit -a" \
  "deny" "$(hook_decision)"

# --- the escape hatch is documented where it is needed -----------------------
assert "bin/review-gate's usage block documents REVIEW_GATE=0" \
  bash -c 'sed -n "1,/^set -u/p" "$1" | grep -q "REVIEW_GATE=0"' _ "$GATE"
hook_in "$FRESH" 'git commit -m x'
assert "the review deny names the REVIEW_GATE=0 bypass" \
  grep -qF "REVIEW_GATE=0" <<<"$(hook_reason)"
hook_in "$PS" 'git commit -m x f.txt'
assert "the pathspec deny names the REVIEW_GATE=0 bypass" \
  grep -qF "REVIEW_GATE=0" <<<"$(hook_reason)"

README="$TOOLKIT_DIR/hooks/review-gate/README.md"
assert "hooks/review-gate/README.md exists" test -f "$README"
assert "the README documents the REVIEW_GATE=0 bypass" \
  grep -qF "REVIEW_GATE=0" "$README"
assert "the README has a Known gaps section" \
  grep -q '^## Known gaps' "$README"
for gap in "bash -c" "sh -c" "xargs" "eval"; do
  assert "the README's Known gaps names the $gap evasion" \
    grep -qF "$gap" "$README"
done
assert "the README states what the gate does not guarantee" \
  bash -c 'tr "\n" " " < "$1" | grep -Eqi "not proof|does not prove|no proof"' _ "$README"
assert "the README documents installing the hook" \
  grep -q '^## Install' "$README"
assert "the README documents uninstalling the hook" \
  grep -q '^## Uninstall' "$README"

# --- Summary -----------------------------------------------------------------

echo "pass: $pass, fail: $fail"
[ "$fail" -eq 0 ]

