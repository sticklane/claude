#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a scratch git repo with a seeded bd store (bd is installed on PATH —
# specs/beads-daily-skill/SPEC.md) plus stub-worker.sh, a deterministic
# stand-in for a compliant /work session.
#
# This scenario runs stub-CLI tier (AGENTS.md line 46: "stub CLI, no model
# calls"), same convention evals/stub-cli.sh and evals/runner-selftest.sh
# use, applied here as a permanent scenario instead of a throwaway one. Its
# sibling runner-cmd.txt names this stub as the default RUNNER_CMD, so the
# plain documented invocation already runs it deterministically:
#
#   bash evals/run.sh work
#
# (an explicit RUNNER_CMD env var still overrides runner-cmd.txt, per
# evals/run.sh's header comment, e.g. to promote this to a live-model run.)
#
# stub-worker.sh (not a live model) plays the RUNNER_CMD role and performs
# the mechanical contract .claude/skills/work/SKILL.md describes — claim
# before work (step 2), implement (step 3), close + unclaim as one unit
# (step 4), then author a tiered fan-out workflow (step 7) — so assert.sh
# can grade the ordering and artifacts without spend. Promoting this to a
# live-model Tier A scenario later only means dropping the RUNNER_CMD
# override; prompt.txt is already written for that case.
#
# bash 3.2 compatible (macOS system bash): no `declare -A` or bash-4 syntax.
set -eu

cd "$EVAL_DIR"
git init -q

BD_NON_INTERACTIVE=1 bd init -q . >/dev/null 2>&1

# Seed one ready issue shaped like genuinely parallel fan-out work, so a
# compliant /work session would author a tiered workflow for it (SKILL.md
# step 7) rather than doing it inline.
id="$(BD_NON_INTERACTIVE=1 bd create "Review five modules for style drift" \
  --description "Genuinely parallel: five independent modules, same check." \
  --json 2>/dev/null \
  | python3 -c 'import json, sys
d = json.load(sys.stdin)
d = d[0] if isinstance(d, list) else d
print(d["id"])')"
[ -n "$id" ] || { echo "setup: bd create did not return an id" >&2; exit 1; }
printf '%s\n' "$id" > .beads/seed-id

# The stub worker: see its own header for the behavior it performs and why.
cat > stub-worker.sh <<'SCRIPT'
#!/usr/bin/env bash
# stub-worker.sh — deterministic, no-model stand-in for a /work session
# (evals/stub-cli.sh's "no API key, no network, deterministic output"
# convention). Invoked per the RUNNER_CMD contract: cwd is this fixture
# dir, the scenario prompt is its final argument (ignored here — the
# sequence below is the fixed behavior this eval grades, not a reaction
# to prompt content). ALLOWED_TOOLS is exported by run.sh; ignored, same
# as evals/stub-cli.sh.
#
# Performs, in order, the mechanical contract
# .claude/skills/work/SKILL.md describes for one issue: claim before work
# (step 2), implement (step 3), close + unclaim as one unit (step 4), then
# author a tiered fan-out workflow (step 7). Every step is echoed to
# stdout first, so the ordering is recoverable from run.sh's session.log
# (tee'd regardless of which runner produced it).
set -eu

id="$(cat .beads/seed-id)"

echo "session: claiming $id"
bd update "$id" --claim >/dev/null
printf '%s\n' "$id" >> .beads/session-claims

echo "session: implementing"
mkdir -p src
printf 'reviewed modules A-E for queue-discipline eval\n' > src/REVIEW-NOTES.md

echo "session: closing $id"
bd close "$id" --reason "queue-discipline eval: modules reviewed" >/dev/null
grep -vF -x "$id" .beads/session-claims > .beads/session-claims.tmp 2>/dev/null || true
mv .beads/session-claims.tmp .beads/session-claims

echo "session: authoring fan-out workflow"
mkdir -p .claude/workflows
cat > .claude/workflows/review-modules.js <<'JS'
// Native workflow authored by /work for a genuinely parallel review
// (.claude/rules/token-discipline.md tiering: mechanical/scouting stages
// carry a cheap-tier model option; judgment stages inherit the session
// model by omitting it).
module.exports = {
  name: "review-modules",
  stages: [
    { name: "scout-modules", kind: "scout", model: "haiku", returnBudget: 300 },
    { name: "synthesize-findings", kind: "judgment" }
  ]
};
JS

echo "session: done"
SCRIPT
chmod +x stub-worker.sh

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: seeded bd store + stub worker for /work queue-discipline eval"
