#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty dir the runner provides): a git
# repo with a bd (beads) store seeded with a tiny executable dependency graph:
# two dependency-free ready issues (alpha, beta) and one (gamma) blocked by
# alpha. Each issue owns one disjoint file and has a runnable acceptance
# command, so a real drain run can implement, verify, merge, and close it.
set -eu

cd "$EVAL_DIR"
git init -q -b master
git config user.email eval@example.com
git config user.name eval

command -v bd >/dev/null 2>&1
bd init >/dev/null 2>&1
A="$(bd create "alpha artifact" --priority 0 \
  --description "Create alpha.txt containing exactly alpha and a trailing newline." \
  --acceptance 'test "$(od -An -t x1 alpha.txt | tr -d " \n")" = 616c7068610a' \
  --metadata '{"touch":["alpha.txt"],"rigor":"small"}' \
  --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')"
B="$(bd create "beta artifact" --priority 1 \
  --description "Create beta.txt containing exactly beta and a trailing newline." \
  --acceptance 'test "$(od -An -t x1 beta.txt | tr -d " \n")" = 626574610a' \
  --metadata '{"touch":["beta.txt"],"rigor":"small"}' \
  --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')"
C="$(bd create "gamma artifact after alpha" --priority 0 \
  --description "After alpha closes, create gamma.txt containing exactly gamma and a trailing newline." \
  --acceptance 'test "$(od -An -t x1 gamma.txt | tr -d " \n")" = 67616d6d610a' \
  --metadata '{"touch":["gamma.txt"],"rigor":"small"}' \
  --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')"
bd dep add "$C" --blocked-by "$A" >/dev/null
printf '%s %s %s\n' "$A" "$B" "$C" > .eval-drain-seed

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
  alpha.txt|beta.txt|gamma.txt) ;;
  *) echo "gate expected exactly one artifact diff, got: $changed" >&2; exit 1 ;;
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
git commit -qm "fixture: executable rolling-window dependency graph"
git tag eval-drain-base
