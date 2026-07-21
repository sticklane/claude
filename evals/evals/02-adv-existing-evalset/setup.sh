#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a `greet` skill that ALREADY has an evalset
# (evals/greet/01-hello/ with the four-file contract, carrying a sentinel).
# Adversarial: /evals only scaffolds "If evals/<skill>/ has no scenario" — so
# with a scenario already present it must NOT scaffold over it. A correct run
# leaves the seeded scenario files byte-unchanged and creates no second
# scenario dir. assert.sh fails loudly if the existing evalset was clobbered.
#
# A no-op evals/run.sh stub is seeded so the skill's run path (step 2) can
# terminate cheaply and hermetically — it must NOT fire a nested paid headless
# session from inside this already-headless eval (the same cost guard
# evals/01-scaffold-new-skill documents). The stub is irrelevant to the
# scaffold-refusal invariant this scenario grades.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p .claude/skills/greet evals/greet/01-hello

cat > .claude/skills/greet/SKILL.md <<'EOF'
---
name: greet
description: Prints a friendly greeting to a named person. Trigger phrases - "/greet", "say hi to someone".
argument-hint: "[name]"
---

Print `hello $ARGUMENTS` to the user.
EOF

cat > evals/greet/01-hello/setup.sh <<'EOF'
#!/usr/bin/env bash
# ADV_SENTINEL_DO_NOT_OVERWRITE — pre-existing seeded scenario.
set -eu
cd "$EVAL_DIR"
git init -q
echo seeded > marker.txt
git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "seeded"
EOF

cat > evals/greet/01-hello/prompt.txt <<'EOF'
/greet Ada
EOF

cat > evals/greet/01-hello/assert.sh <<'EOF'
#!/usr/bin/env bash
# ADV_SENTINEL_DO_NOT_OVERWRITE — pre-existing seeded scenario grader.
set -u
[ -f marker.txt ] || { echo "ASSERT FAIL: marker.txt missing" >&2; exit 1; }
echo "assert: seeded scenario passed"
EOF

chmod +x evals/greet/01-hello/setup.sh evals/greet/01-hello/assert.sh

# Hermetic no-op run harness stub: keeps /evals's run path from firing a
# nested paid session. Never spawns anything.
cat > evals/run.sh <<'EOF'
#!/usr/bin/env bash
# Hermetic fixture stub — a no-op stand-in for the real eval runner so the
# scenario stays hermetic. Prints a line and exits 0 without spawning a session.
echo "run.sh stub: no scenarios executed (hermetic fixture)"
exit 0
EOF
chmod +x evals/run.sh

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: greet skill with an existing evalset"
