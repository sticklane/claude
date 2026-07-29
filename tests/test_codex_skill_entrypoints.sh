#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
claude_skills="$repo_root/.claude/skills"
portable_skills="$repo_root/.agents/skills"

failures=0
for skill_md in "$claude_skills"/*/SKILL.md; do
  skill_dir="$(dirname "$skill_md")"
  skill_name="$(basename "$skill_dir")"
  portable_entry="$portable_skills/$skill_name"



  if [[ ! -L "$portable_entry" ]]; then
    echo "Codex/Antigravity entrypoint is not a symlink: $skill_name" >&2
    failures=$((failures + 1))
    continue
  fi

  resolved="$(cd "$(dirname "$portable_entry")" && realpath "$portable_entry")"
  if [[ "$resolved" != "$skill_dir" ]]; then
    echo "Codex/Antigravity entrypoint targets $resolved, expected $skill_dir" >&2
    failures=$((failures + 1))
  fi

  [[ -f "$portable_entry/SKILL.md" ]] || {
    echo "broken Codex/Antigravity entrypoint: $skill_name" >&2
    failures=$((failures + 1))
  }
done

for portable_entry in "$portable_skills"/*; do
  skill_name="$(basename "$portable_entry")"
  [[ -f "$claude_skills/$skill_name/SKILL.md" ]] || {
    echo "orphaned Codex/Antigravity entrypoint: $skill_name" >&2
    failures=$((failures + 1))
  }
done

[[ "$failures" -eq 0 ]]

# The same source is a native installable package in Claude Code and Codex.
# Antigravity consumes the open Agent Skills entrypoints above.
"$repo_root/bin/generate-codex-skill-entrypoints"
python3 - "$repo_root" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
antigravity = json.loads((root / "plugin.json").read_text())
marketplace = json.loads(
    (root / ".agents/plugins/marketplace.json").read_text()
)

assert codex["name"] == claude["name"] == "agentic"
assert antigravity["name"] == codex["name"]
assert set(antigravity) == {"$schema", "name", "description"}
assert codex["version"] == claude["version"]
assert codex["skills"] == "./skills/"
plugin_skills = root / codex["skills"]
source_skills = root / ".claude/skills"
expected = {
    path.name
    for path in source_skills.iterdir()
    if (path / "SKILL.md").is_file()
}
actual = {path.name for path in plugin_skills.iterdir()}
assert actual == expected
for name in actual:
    entry = plugin_skills / name
    assert entry.is_dir() and not entry.is_symlink(), (
        f"{entry} must be a real packaging directory; Codex omits symlinks "
        "when it populates the plugin cache"
    )
    wrapper = (entry / "SKILL.md").read_text()
    source = (source_skills / name / "SKILL.md").read_text()
    assert "$ARGUMENTS" not in source, (
        f"{name}: Claude-only argument placeholder leaked into shared procedure"
    )
    assert "/clear" not in source, (
        f"{name}: Claude-only session-reset command leaked into shared procedure"
    )
    for field in ("name", "description"):
        source_line = next(
            (line for line in source.splitlines() if line.startswith(f"{field}:")),
            None,
        )
        wrapper_line = next(
            (line for line in wrapper.splitlines() if line.startswith(f"{field}:")),
            None,
        )
        portable_source_line = source_line.replace("<", "[").replace(">", "]")
        assert wrapper_line == portable_source_line, (
            f"{name}: generated wrapper field {field!r} is stale"
        )
    assert "argument-hint:" not in wrapper, (
        f"{name}: Claude-only argument-hint leaked into portable frontmatter"
    )
    canonical = f"../../.claude/skills/{name}/SKILL.md"
    assert canonical in wrapper, f"{name}: wrapper does not load {canonical}"
assert "agents" not in codex, "Codex manifest must not carry Claude agent pins"
eval_policy = (source_skills / "evals/agents/openai.yaml").read_text()
assert (plugin_skills / "evals/agents/openai.yaml").read_text() == eval_policy
assert "allow_implicit_invocation: false" in eval_policy
assert "priced against a budget ceiling, and ledgered" in (
    source_skills / "evals/SKILL.md"
).read_text()
assert "Root `AGENTS.md`" in (source_skills / "distill/SKILL.md").read_text()
assert "AGENTS.md: a single line" in (
    source_skills / "design/SKILL.md"
).read_text()
assert marketplace["name"] == "agentic-toolkit"
entry = next(p for p in marketplace["plugins"] if p["name"] == "agentic")
assert entry["source"] == {"source": "local", "path": "."}
assert entry["policy"]["installation"] == "AVAILABLE"
assert entry["policy"]["authentication"] == "ON_INSTALL"
PY

# Shared skill instructions may describe all three backends, but executable
# Claude CLI recipes do not belong in them. They live in runtimes/claude-code.md
# so Codex or Antigravity cannot accidentally follow a Claude launch command.
python3 - "$claude_skills" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
command = re.compile(
    r"\bclaude\s+(?:-p\b|mcp\b|plugin\b|setup-token\b|[\"'])"
)
paths = []
for path in root.rglob("*"):
    if not path.is_file():
        continue
    if path.name not in {"SKILL.md", "reference.md", "workboard.py"}:
        continue
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if command.search(line):
            paths.append(f"{path.relative_to(root)}:{lineno}:{line.strip()}")
if paths:
    raise SystemExit(
        "shared skills contain executable Claude CLI recipes:\n" + "\n".join(paths)
    )
PY

# A non-Claude package resolution failure must stop locally. In particular,
# neither Codex nor Antigravity may use the legacy Claude Code cache probe.
resolver_root="$(mktemp -d)"
mkdir -p "$resolver_root/bin"
cp "$repo_root/bin/resolve-skill-path" "$resolver_root/bin/resolve-skill-path"
cat > "$resolver_root/bin/claude" <<EOF
#!/bin/sh
touch "$resolver_root/claude-was-called"
exit 0
EOF
chmod +x "$resolver_root/bin/resolve-skill-path" "$resolver_root/bin/claude"
for runtime in codex antigravity; do
  resolver_error="$(
    AGENTIC_RUNTIME="$runtime" PATH="$resolver_root/bin:$PATH" \
      "$resolver_root/bin/resolve-skill-path" \
      .claude/skills/missing/SKILL.md 2>&1 >/dev/null || true
  )"
  grep -q "$runtime" <<<"$resolver_error"
  test ! -e "$resolver_root/claude-was-called"
done
rm -rf "$resolver_root"

# The dashboard must keep read-side CLI queries and write-side commands on the
# selected runtime. Construct the native argv without spawning a paid session.
python3 - "$repo_root/agent-console/agent-console.py" <<'PY'
import importlib.util
import os
import sys
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("agent_console", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for runtime, env_name, binary, marker in (
    ("codex", "AGENT_CONSOLE_CODEX_BIN", "/stub/codex", "exec"),
    ("antigravity", "AGENT_CONSOLE_ANTIGRAVITY_BIN", "/stub/agy", "-p"),
):
    with (
        patch.dict(
            os.environ,
            {"AGENTIC_RUNTIME": runtime, env_name: binary},
        ),
        patch.object(module.subprocess, "run") as run,
    ):
        assert module._claude_json("agents") is None
        try:
            module._claude_run_bg(["-p", "test"], "/tmp")
        except RuntimeError as error:
            assert f"active {runtime} runtime" in str(error)
        else:
            raise AssertionError(f"{runtime}: Claude background launch allowed")
        argv = module._runtime_start_argv("test")
        assert argv[0] == binary
        assert marker in argv
        assert "claude" not in " ".join(argv)
        run.assert_not_called()
PY

grep -q "same workflow skills" "$repo_root/antigravity/README.md"
grep -q "native skill invocation" "$repo_root/.claude/skills/build/SKILL.md"
grep -q "native question UI" "$repo_root/.claude/skills/idea/SKILL.md"
grep -q "native live-agent inventory" "$repo_root/.claude/skills/fleet/SKILL.md"
grep -q "native awaited-agent coordinator" "$repo_root/.claude/skills/work/SKILL.md"
grep -q "portable orchestration skill" \
  "$repo_root/.claude/skills/workflow-author/SKILL.md"
grep -q "EVAL_RUNTIME=<active-runtime>" \
  "$repo_root/.claude/skills/evals/SKILL.md"
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
missing_runtime_rc=0
missing_runtime_output="$(EVALS_ROOT="$dry_root" EVAL_DRY_RUN=1 \
  "$repo_root/evals/run.sh" drain 2>&1)" || missing_runtime_rc=$?
[ "$missing_runtime_rc" -ne 0 ]
grep -q 'EVAL_RUNTIME is required' <<<"$missing_runtime_output"
! grep -q 'DRY-RUN \[claude-code\]' <<<"$missing_runtime_output"
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
