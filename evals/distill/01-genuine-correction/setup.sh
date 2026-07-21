#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo plus a planted session transcript (session-context.md) that
# /distill is told to harvest. The transcript records ONE genuine, non-obvious
# correction the user made and asked to remember — the exact integration-test
# invocation `./run-tests.sh --db=memory`, without which the suite hangs. A
# competent /distill routes this durable command gotcha into a doctrine file
# (CLAUDE.md / .claude/rules / docs/memory); assert.sh greps for the literal
# flag there. The seed CLAUDE.md deliberately omits it so any match is the
# run's own writing (capture is real, not pre-seeded).
# bash 3.2 compatible: no `declare -A`, no bash-4+ syntax.
set -eu

cd "$EVAL_DIR"
git init -q

cat > CLAUDE.md <<'EOF'
# Project conventions

- Prefer small, focused commits.
EOF

cat > run-tests.sh <<'EOF'
#!/usr/bin/env bash
# Integration suite. Needs a database; --db=memory uses an in-process store.
set -eu
db="postgres"
for a in "$@"; do case "$a" in --db=*) db="${a#--db=}" ;; esac; done
echo "running integration tests against db=$db"
EOF
chmod +x run-tests.sh

cat > session-context.md <<'EOF'
# Session transcript (harvest target for /distill)

user: Run the integration tests.
assistant: Running ./run-tests.sh …
  [the run hangs for minutes waiting for a database, then times out]
user: Stop — that hangs forever. This repo has no Postgres running, so the
  integration suite blocks waiting for one. You have to pass --db=memory.
  Always invoke it as `./run-tests.sh --db=memory`. Remember this for next
  time — it is not discoverable from the code.
assistant: Understood — re-running as `./run-tests.sh --db=memory` … the
  suite passes now.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: session with a genuine test-invocation correction"
