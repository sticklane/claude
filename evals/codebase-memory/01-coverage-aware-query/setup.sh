#!/usr/bin/env bash
set -eu

cd "$EVAL_DIR"
mkdir -p app
printf '%s\n' \
  'def dispatch(job):' \
  '    return job.run()' \
  > app/dispatch.py
printf '%s\n' \
  'from app.dispatch import dispatch' \
  > app/api.py
git init -q
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture"
