#!/usr/bin/env bash
# Tests for bin/janitor's per-candidate report (agentic-hzr1).
#
# A dry run has to name every worktree it would destroy, so these assertions
# read the reported records rather than the summary counts. The fixtures
# duplicate tests/test_janitor_worktree_sweep.sh's because that suite is
# frozen by a retain-pinned surface-inventory fragment and cannot host a
# shared helper.
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
contains() { case "$1" in *"$2"*) echo 0 ;; *) echo 1 ;; esac; }
differ() { { [ "$1" != "$2" ] && [ -n "$1" ] && [ -n "$2" ]; } && echo 0 || echo 1; }
parses_as_json() { printf '%s' "$1" | jq -e . >/dev/null 2>&1 && echo 0 || echo 1; }
jq_true() { printf '%s' "$1" | jq -e "$2" >/dev/null 2>&1 && echo 0 || echo 1; }
line_for() { # line_for <output> <worktree-path>
  printf '%s\n' "$1" | grep -F "path=$2 " | head -n 1
}
reason_for() { line_for "$1" "$2" | sed -n 's/.* reason=//p'; }

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
printf '%s\n' '[{"id":"agentic-4444"}]' > "$STATE/in_progress.json"
printf '%s\n' '[{"id":"agentic-1111"},{"id":"agentic-2222"},{"id":"agentic-3333"}]' \
  > "$STATE/closed.json"

cleanup() { chmod -R u+w "$TMP" 2>/dev/null; rm -rf "$TMP"; }
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

# --- fixture: one worktree per reported category -----------------------------
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

git -C "$REPO" worktree add -q -b drain/agentic-4444 "$WT/in-progress" main
commit_in "$WT/in-progress" "live worker output" "live worker output"

# git reports worktree paths with symlinks resolved, so the fixture roots are
# resolved the same way before any reported path is matched against them.
WTR="$(cd "$WT" && pwd -P)"
REPOR="$(cd "$REPO" && pwd -P)"

DRY="$(run_janitor "$REPO" --dry-run)"

# --- the plan names what it would destroy ------------------------------------
assert "dry run: names the reclaimable worktree's own path" \
  "$(contains "$DRY" "path=$WTR/clean-closed ")"

CLEAN_LINE="$(line_for "$DRY" "$WTR/clean-closed")"
assert "dry run: clean worktree classified as clean" "$(contains "$CLEAN_LINE" "category=clean")"
assert "dry run: clean worktree action is remove" "$(contains "$CLEAN_LINE" "action=remove")"
assert "dry run: clean worktree names its owning issue" \
  "$(contains "$CLEAN_LINE" "issue=agentic-1111")"
assert "dry run: clean worktree names its issue status" \
  "$(contains "$CLEAN_LINE" "status=closed")"

RECON_LINE="$(line_for "$DRY" "$WTR/reconstructible")"
assert "dry run: reconstructible worktree classified as reconstructible" \
  "$(contains "$RECON_LINE" "category=reconstructible")"
assert "dry run: reconstructible worktree action is remove" \
  "$(contains "$RECON_LINE" "action=remove")"

UNIQUE_LINE="$(line_for "$DRY" "$WTR/unique")"
assert "dry run: unique worktree classified as unique" "$(contains "$UNIQUE_LINE" "category=unique")"
assert "dry run: unique worktree action is salvage-then-remove" \
  "$(contains "$UNIQUE_LINE" "action=salvage-then-remove")"

DETACHED_LINE="$(line_for "$DRY" "$WTR/detached")"
assert "dry run: detached worktree classified as detached" \
  "$(contains "$DETACHED_LINE" "category=detached")"
assert "dry run: detached worktree action is skip" "$(contains "$DETACHED_LINE" "action=skip")"

# --- a skip says why, and the reasons are told apart -------------------------
LIVE_REASON="$(reason_for "$DRY" "$WTR/in-progress")"
SHARED_REASON="$(reason_for "$DRY" "$REPOR")"
assert "dry run: live-session skip states its reason" "$(contains "$LIVE_REASON" "in progress")"
assert "dry run: shared-checkout skip states its reason" \
  "$(contains "$SHARED_REASON" "shared checkout")"
assert "dry run: the two skip reasons are distinguishable" \
  "$(differ "$LIVE_REASON" "$SHARED_REASON")"

# --- selection is unchanged by the reporting ---------------------------------
assert "dry run: three removals planned" "$(contains "$DRY" "reclaimed_worktrees=3")"
assert "dry run: three candidates skipped" "$(contains "$DRY" "skipped_or_ambiguous=3")"

# --- the machine-readable plan carries the same records ----------------------
DRYJ="$(run_janitor "$REPO" --dry-run --json)"
assert "dry run --json: output parses as JSON" "$(parses_as_json "$DRYJ")"
WT_COUNT="$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')"
assert "dry run --json: one candidate record per worktree" \
  "$(is "$(printf '%s' "$DRYJ" | jq -r '.candidates | length' 2>/dev/null || echo 0)" "$WT_COUNT")"
assert "dry run --json: every candidate carries the report keys" \
  "$(jq_true "$DRYJ" 'all(.candidates[]; has("path") and has("branch") and has("issue") and has("status") and has("category") and has("action"))')"

# --- the ledger has the same shape as the plan -------------------------------
APPLY="$(run_janitor "$REPO" --apply)"
assert "apply: the ledger reports the removed worktree in the same shape" \
  "$(contains "$(line_for "$APPLY" "$WTR/clean-closed")" "action=remove")"
assert "apply: the ledger names the salvage the unique worktree got" \
  "$(contains "$(reason_for "$APPLY" "$WTR/unique")" "salvage/agentic-3333")"

printf '\n%s: %d passed, %d failed\n' "$(basename "$0")" "$pass" "$fail"
[ "$fail" -eq 0 ]
