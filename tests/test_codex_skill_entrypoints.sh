#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
claude_skills="$repo_root/.claude/skills"
codex_skills="$repo_root/.agents/skills"

failures=0
for skill_md in "$claude_skills"/*/SKILL.md; do
  skill_dir="$(dirname "$skill_md")"
  skill_name="$(basename "$skill_dir")"
  codex_entry="$codex_skills/$skill_name"



  if [[ ! -L "$codex_entry" ]]; then
    echo "Codex entrypoint is not a symlink: $skill_name" >&2
    failures=$((failures + 1))
    continue
  fi

  resolved="$(cd "$(dirname "$codex_entry")" && realpath "$codex_entry")"
  if [[ "$resolved" != "$skill_dir" ]]; then
    echo "Codex entrypoint targets $resolved, expected $skill_dir" >&2
    failures=$((failures + 1))
  fi

  [[ -f "$codex_entry/SKILL.md" ]] || {
    echo "broken Codex entrypoint: $skill_name" >&2
    failures=$((failures + 1))
  }
done

for codex_entry in "$codex_skills"/*; do
  skill_name="$(basename "$codex_entry")"
  [[ -f "$claude_skills/$skill_name/SKILL.md" ]] || {
    echo "orphaned Codex entrypoint: $skill_name" >&2
    failures=$((failures + 1))
  }
done

[[ "$failures" -eq 0 ]]
grep -q 'fork_turns: "none"' "$repo_root/runtimes/codex.md"
grep -q 'Ultra orchestration does' "$repo_root/runtimes/codex.md"
grep -q 'Drain sandbox requirement' "$repo_root/runtimes/codex.md"
grep -q -- '--sandbox danger-full-access' "$repo_root/runtimes/codex.md"
grep -q 'Codex it is the collaboration' "$repo_root/.claude/rules/concurrent-sessions.md"
grep -q 'Codex uses `list_agents`' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'Under Codex, use `list_agents`' "$repo_root/.claude/skills/build/SKILL.md"
grep -q "Workspace: 'branch'.*writers" "$repo_root/runtimes/antigravity.md"
grep -q 'Codex serializes isolated' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'do not create a `-r2`/retry worktree' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'transient prompt' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'checkout tests the unmerged base' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'parallel read-only barrier' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'acceptance commands plus directly relevant targeted tests' "$repo_root/.claude/skills/drain/SKILL.md"
grep -Eq 'canonical project gate (exactly )?once' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'Drain-mode: true' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'Drain-mode' "$repo_root/.claude/agents/verifier.md"
grep -q "NOT spawn build's verifier" "$repo_root/.claude/skills/drain/reference.md"
grep -q 'Drain-worker exception' "$repo_root/.claude/skills/build/SKILL.md"

# An explicit Codex drain eval must resolve to the trusted-fixture sandbox
# without launching a paid session under EVAL_DRY_RUN.
dry_root="$(mktemp -d)"
trap 'rm -rf "$dry_root"' EXIT
mkdir -p "$dry_root/drain/01-codex-sandbox"
printf '%s\n' 'cd "$EVAL_DIR"; git init -q' > "$dry_root/drain/01-codex-sandbox/setup.sh"
printf '%s\n' 'drain the empty queue' > "$dry_root/drain/01-codex-sandbox/prompt.txt"
printf '%s\n' 'exit 0' > "$dry_root/drain/01-codex-sandbox/assert.sh"
dry_output="$(EVALS_ROOT="$dry_root" EVAL_RUNTIME=codex EVAL_DRY_RUN=1 \
  "$repo_root/evals/run.sh" drain)"
grep -q 'DRY-RUN \[codex\] runner:' <<<"$dry_output"
grep -q -- 'codex exec --json' <<<"$dry_output"
grep -q -- '--sandbox danger-full-access' <<<"$dry_output"
! grep -q 'thread.started' <<<"$dry_output"

# Codex's checked-in headless profile emits JSONL, so the live runner must
# export session.log as EVAL_TRANSCRIPT just as the Claude branch does.
transcript_evals="$dry_root/transcript-evals"
fake_bin="$dry_root/bin"
mkdir -p "$transcript_evals/drain/01-codex-transcript" "$fake_bin"
printf '%s\n' 'cd "$EVAL_DIR"; git init -q' > "$transcript_evals/drain/01-codex-transcript/setup.sh"
printf '%s\n' 'inspect the empty drain queue' > "$transcript_evals/drain/01-codex-transcript/prompt.txt"
printf '%s\n' build > "$transcript_evals/drain/01-codex-transcript/skill-deps.txt"
cat > "$transcript_evals/drain/01-codex-transcript/assert.sh" <<'EOF'
set -eu
[ "$EVAL_TRANSCRIPT" = "$PWD/session.log" ]
grep -q '"type":"thread.started"' "$EVAL_TRANSCRIPT"
[ -f .agents/skills/drain/SKILL.md ]
[ -f .agents/skills/build/SKILL.md ]
[ -f .claude/rules/untrusted-data.md ]
[ -f hooks/review-gate/README.md ]
EOF
cat > "$fake_bin/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"type":"thread.started","thread_id":"fixture"}'
EOF
chmod +x "$fake_bin/codex"
transcript_output="$(PATH="$fake_bin:$PATH" EVALS_ROOT="$transcript_evals" \
  EVAL_RUNTIME=codex "$repo_root/evals/run.sh" drain 2>&1)"
grep -q '^PASS  drain/01-codex-transcript' <<<"$transcript_output"
! grep -q 'no locatable transcript' <<<"$transcript_output"

# External evalsets source Codex entrypoints, dependencies, rules, and hooks
# from the external repository rather than silently falling back to this one.
external_root="$dry_root/external"
external_evals="$dry_root/external-evals"
mkdir -p "$external_root/skills/drain" "$external_root/skills/build" \
  "$external_root/agents" "$external_root/rules" \
  "$external_root/hooks/review-gate" \
  "$external_root/.agents/skills/drain" "$external_root/.agents/skills/build" \
  "$external_evals/drain/01-external-source"
printf '%s\n' 'name: external-drain' > "$external_root/skills/drain/SKILL.md"
printf '%s\n' 'name: external-build' > "$external_root/skills/build/SKILL.md"
printf '%s\n' external-rule > "$external_root/rules/untrusted-data.md"
printf '%s\n' external-hook > "$external_root/hooks/review-gate/README.md"
printf '%s\n' external-codex-drain > "$external_root/.agents/skills/drain/SKILL.md"
printf '%s\n' external-codex-build > "$external_root/.agents/skills/build/SKILL.md"
printf '%s\n' 'cd "$EVAL_DIR"; git init -q' > "$external_evals/drain/01-external-source/setup.sh"
printf '%s\n' 'inspect external source provisioning' > "$external_evals/drain/01-external-source/prompt.txt"
printf '%s\n' build > "$external_evals/drain/01-external-source/skill-deps.txt"
cat > "$external_evals/drain/01-external-source/assert.sh" <<'EOF'
set -eu
grep -q external-codex-drain .agents/skills/drain/SKILL.md
grep -q external-codex-build .agents/skills/build/SKILL.md
grep -q external-rule .claude/rules/untrusted-data.md
grep -q external-hook hooks/review-gate/README.md
EOF
external_output="$(PATH="$fake_bin:$PATH" EVALS_ROOT="$external_evals" \
  EVAL_RUNTIME=codex SKILLS_ROOT="$external_root/skills" \
  AGENTS_ROOT="$external_root/agents" RULES_ROOT="$external_root/rules" \
  "$repo_root/evals/run.sh" drain 2>&1)"
grep -q '^PASS  drain/01-external-source' <<<"$external_output"

# Repeated wait timeouts alone are not review evidence. The trajectory grader
# requires issue-specific successful worker/reviewer receipts interleaved with
# waits and tied to the same branches whose worktree gates passed.
trajectory_log="$dry_root/trajectory.jsonl"
printf '%s\n' \
  '{"type":"item.completed","item":{"type":"command_execution","status":"completed","command":"sed .agents/skills/drain/SKILL.md","aggregated_output":"name: drain","exit_code":0}}' \
  > "$trajectory_log"
for issue in alpha beta gamma; do
  printf '%s\n' \
    '{"type":"item.completed","item":{"type":"collab_tool_call","tool":"wait","status":"completed"}}' \
    "{\"type\":\"item.completed\",\"item\":{\"type\":\"agent_message\",\"text\":\"DRAIN_EVAL_WORKER $issue DONE\"}}" \
    '{"type":"item.completed","item":{"type":"collab_tool_call","tool":"wait","status":"completed"}}' \
    "{\"type\":\"item.completed\",\"item\":{\"type\":\"agent_message\",\"text\":\"DRAIN_EVAL_REVIEW $issue verifier=PASS critic=READY\"}}" \
    "{\"type\":\"item.completed\",\"item\":{\"type\":\"command_execution\",\"status\":\"completed\",\"exit_code\":0,\"command\":\"git worktree add -b drain/$issue .wt/$issue master\",\"aggregated_output\":\"\"}}" \
    "{\"type\":\"item.completed\",\"item\":{\"type\":\"command_execution\",\"status\":\"completed\",\"exit_code\":0,\"command\":\"git merge --no-ff drain/$issue\",\"aggregated_output\":\"\"}}" \
    "{\"type\":\"item.completed\",\"item\":{\"type\":\"command_execution\",\"status\":\"completed\",\"exit_code\":0,\"command\":\"git worktree remove .wt/$issue\",\"aggregated_output\":\"\"}}" \
    "{\"type\":\"item.completed\",\"item\":{\"type\":\"command_execution\",\"status\":\"completed\",\"exit_code\":0,\"command\":\"scripts/check.sh\",\"aggregated_output\":\"gate-worktree=drain/$issue artifact=$issue.txt\"}}" \
    >> "$trajectory_log"
done
python3 "$repo_root/evals/drain/assert_codex_trajectory.py" "$trajectory_log" rolling
wait_only_log="$dry_root/wait-only.jsonl"
grep -v 'DRAIN_EVAL_\\(WORKER\\|REVIEW\\)' "$trajectory_log" > "$wait_only_log"
! python3 "$repo_root/evals/drain/assert_codex_trajectory.py" "$wait_only_log" rolling \
  >/dev/null 2>&1

echo "CODEX SKILLS OK"
