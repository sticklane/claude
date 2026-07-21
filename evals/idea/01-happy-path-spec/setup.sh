#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a minimal flat-file task-tracker CLI and NO specs/
# directory. The scenario pitches a non-trivial, multi-behavior feature
# (due dates + an overdue-listing command) so /idea produces a real spec
# rather than right-sizing to a one-line diff. /idea CREATES the spec, so
# the fixture deliberately seeds none.
# bash 3.2 compatible: no `declare -A`, no bash-4+ syntax.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p src tests

cat > src/tasks.sh <<'EOF'
#!/usr/bin/env bash
# Minimal flat-file task tracker.
#   src/tasks.sh add "<text>"   append a task line
#   src/tasks.sh list           print every task, one per line
set -eu
STORE="${TASKS_STORE:-tasks.txt}"
cmd="${1:-list}"
case "$cmd" in
  add)  shift; printf '%s\n' "$*" >> "$STORE" ;;
  list) [ -f "$STORE" ] && cat "$STORE" || true ;;
  *)    echo "unknown command: $cmd" >&2; exit 1 ;;
esac
EOF
chmod +x src/tasks.sh

cat > tests/smoke.sh <<'EOF'
#!/usr/bin/env bash
# Smoke test for the current tasks CLI.
set -eu
tmp="$(mktemp)"
TASKS_STORE="$tmp" src/tasks.sh add "buy milk"
out="$(TASKS_STORE="$tmp" src/tasks.sh list)"
[ "$out" = "buy milk" ] || { echo "smoke FAIL: got '$out'" >&2; exit 1; }
echo "smoke OK"
EOF
chmod +x tests/smoke.sh

cat > README.md <<'EOF'
# tasks

A tiny flat-file task tracker. Add tasks and list them back.

    src/tasks.sh add "buy milk"
    src/tasks.sh list

Tasks are plain lines appended to `tasks.txt`.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: minimal tasks CLI"
