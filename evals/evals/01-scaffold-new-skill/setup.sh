#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo containing one small toolkit-shaped skill (greet) with
# no evals/greet/ evalset yet, so /evals is exercised on its scaffold path
# (SKILL.md step 1) rather than its run path (step 2). The run path fires a
# nested paid headless session from inside this already-headless eval —
# expensive and timeout-fragile — so this scenario checks the cheaper,
# fully artifact-checkable half of the skill's contract instead.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p .claude/skills/greet
cat > .claude/skills/greet/SKILL.md <<'EOF'
---
name: greet
description: Prints a friendly greeting to a named person. Trigger phrases - "/greet", "say hi to someone".
argument-hint: "[name]"
---

Print `hello $ARGUMENTS` to the user.
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo greet skill, no evalset yet"
