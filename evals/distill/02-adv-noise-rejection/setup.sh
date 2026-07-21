#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo plus a planted session transcript (session-context.md) that
# mixes TWO findings /distill must tell apart:
#   (1) a GENUINE durable convention — `make lint` must run with LINT_STRICT=1
#       or it silently skips the security lints (non-obvious, generalizes) →
#       belongs in a doctrine file.
#   (2) ONE-OFF NOISE — a throwaway scratch path unique to this run
#       (/tmp/wt-zpopulk-7731), phrased as a "jot it down to reuse" note. It
#       fails /distill's routing gate ("would removing this line cause a
#       future agent to make a mistake?" — no; the path won't exist next
#       session), so it must be captured NOWHERE.
# assert.sh passes only if the durable item landed in a doctrine file AND the
# noise sentinel (zpopulk-7731) appears in no doctrine file. The seed CLAUDE.md
# omits both so any match is the run's own writing.
# bash 3.2 compatible: no `declare -A`, no bash-4+ syntax.
set -eu

cd "$EVAL_DIR"
git init -q

cat > CLAUDE.md <<'EOF'
# Project conventions

- Prefer small, focused commits.
EOF

cat > session-context.md <<'EOF'
# Session transcript (harvest target for /distill)

user: The lint step passed but CI still flagged a security issue.
assistant: I ran `make lint` and it reported no problems.
user: Right — bare `make lint` silently skips the security lints. You have to
  set LINT_STRICT=1 (run it as `LINT_STRICT=1 make lint`). Always do that in
  this repo; it is not obvious from the Makefile. Remember it.
assistant: Understood — `LINT_STRICT=1 make lint` now reports the issue.

user: Also, for this run I stashed the build scratch in a throwaway worktree
  at /tmp/wt-zpopulk-7731 — jot that down to reuse next time.
assistant: Noted.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: session mixing a durable convention with one-off noise"
