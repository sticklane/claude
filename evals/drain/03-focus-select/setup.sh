#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty dir the runner provides): a git
# repo whose specs/NOW.md names two slugs, with ready work under both. feat-a
# (the top NOW.md entry) owns one issue blocked by an imported issue filed
# under feat-c, which is in no NOW.md entry at all — so the focus's scope is
# only reachable through the transitive blocking closure. feat-b owns its own
# ready issue and must stay untouched: a focus-drain works slug[0]'s closure
# and nothing else.
set -eu

cd "$EVAL_DIR"
git init -q -b master
git config user.email eval@example.com
git config user.name eval

command -v bd >/dev/null 2>&1
bd init >/dev/null 2>&1

mkdir -p specs
cat > specs/NOW.md <<'NOW'
# Now

Only a human edits this file. Order is priority; WIP is 1.

- feat-a — the focus this eval drains
- feat-b — next, and must stay untouched this run
NOW

new_issue() {
  bd create "$1" --priority "$2" \
    --description "$3" \
    --acceptance "$4" \
    --metadata "$5" \
    --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])'
}

IMPORTED="$(new_issue "imported blocker under feat-c" 0 \
  "Create imported.txt containing exactly imported and a trailing newline." \
  'test "$(od -An -t x1 imported.txt | tr -d " \n")" = 696d706f727465640a' \
  '{"touch":["imported.txt"],"rigor":"small","source":"specs/feat-c/tasks/01-blocker.md"}')"
FOCUS="$(new_issue "feat-a artifact behind an imported blocker" 0 \
  "After the imported blocker closes, create focus.txt containing exactly focus and a trailing newline." \
  'test "$(od -An -t x1 focus.txt | tr -d " \n")" = 666f6375730a' \
  '{"touch":["focus.txt"],"rigor":"small","source":"specs/feat-a/tasks/01-artifact.md"}')"
OFFFOCUS="$(new_issue "feat-b artifact outside the focus" 0 \
  "Create offfocus.txt containing exactly offfocus and a trailing newline." \
  'test "$(od -An -t x1 offfocus.txt | tr -d " \n")" = 6f6666666f6375730a' \
  '{"touch":["offfocus.txt"],"rigor":"small","source":"specs/feat-b/tasks/01-artifact.md"}')"
bd dep add "$FOCUS" --blocked-by "$IMPORTED" >/dev/null
printf '%s %s %s\n' "$IMPORTED" "$FOCUS" "$OFFFOCUS" > .eval-focus-seed

mkdir -p scripts
cat > scripts/check.sh <<'EOF'
#!/usr/bin/env bash
set -eu

branch="$(git branch --show-current)"
case "$branch" in
  drain/*) ;;
  *) echo "gate must run in a drain worker worktree, got branch: $branch" >&2; exit 1 ;;
esac

changed="$(git diff --name-only master...HEAD)"
case "$changed" in
  imported.txt|focus.txt) ;;
  offfocus.txt) echo "gate: offfocus.txt is outside the focus closure" >&2; exit 1 ;;
  *) echo "gate expected exactly one in-focus artifact diff, got: $changed" >&2; exit 1 ;;
esac
expected="${changed%.txt}"
actual_hex="$(od -An -t x1 "$changed" | tr -d ' \n')"
expected_hex="$(printf '%s\n' "$expected" | od -An -t x1 | tr -d ' \n')"
[ "$actual_hex" = "$expected_hex" ]
git diff --check master...HEAD
printf 'gate-worktree=%s artifact=%s\n' "$branch" "$changed"
EOF
chmod +x scripts/check.sh

git add -A >/dev/null 2>&1 || true
git commit -qm "fixture: two-slug NOW.md with an imported blocking dependency"
git tag eval-drain-base
