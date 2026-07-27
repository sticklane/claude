#!/usr/bin/env bash
set -eu

cd "$EVAL_DIR"
mkdir -p generated
printf '%s\n' \
  'export const hiddenCaller = () => dispatch(job);' \
  > generated/caller.ts
git init -q
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture"
