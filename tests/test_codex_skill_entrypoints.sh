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
grep -q "Workspace: 'branch'.*writers" "$repo_root/runtimes/antigravity.md"
grep -q 'Codex serializes isolated' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'parallel read-only barrier' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'acceptance commands plus directly relevant targeted tests' "$repo_root/.claude/skills/drain/SKILL.md"
grep -Eq 'canonical project gate (exactly )?once' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'Drain-mode: true' "$repo_root/.claude/skills/drain/SKILL.md"
grep -q 'Drain-mode' "$repo_root/.claude/agents/verifier.md"
grep -q "NOT spawn build's verifier" "$repo_root/.claude/skills/drain/reference.md"
grep -q 'Drain-worker exception' "$repo_root/.claude/skills/build/SKILL.md"
echo "CODEX SKILLS OK"
