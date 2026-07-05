# Evidence: task 03 — repo wiring (AGENTS.md, skill pointers, mirror, plugin bump)

Worker branch `task/03-repo-wiring-and-pointers` (69ea7e5); verdict was
BLOCKED solely on criterion 6's pre-existing `tests/test_workboard_render.sh`
regression (reproduced on unmodified main at b92f98f and 592a8cc). Criteria
1–5 verified by the worker on the branch:

1. `grep -c "agentprof/" AGENTS.md` → 2; `grep -c "agent-console/" AGENTS.md` → 2 — PASS
2. `grep -rn "~/agent-console/agent-console.py" .claude/skills/ antigravity/ | wc -l` → 0 — PASS
3. `grep -c "~/claude/agent-console/agent-console.py" .claude/skills/workboard/SKILL.md` → 2 — PASS
4. `grep -c "~/claude/agent-console/agent-console.py" antigravity/.agents/skills/workboard/SKILL.md` → 2 — PASS
5. `git diff main -- .claude-plugin/plugin.json | grep -c "version"` → 2 — PASS

Criterion 6 resolved attended (2026-07-05, orchestrator session): the
regression was fixed on main first — `render_actions` now emits its bash
invocation via `cmd_html` (adjacent copy button), tests updated to accept
the `bash /` cwd-independent form and the cmd-wrap markup, antigravity
mirror synced, plugin bumped 0.8.6 (commit "fix(workboard): actions
invocation rendered via cmd_html"). Post-merge on main: full suite —
`for t in tests/test_*.sh` (all), `./bin/check-agent-model-pins`,
`./evals/runner-selftest.sh`, `./specs/status.sh`,
`claude plugin validate .`, plus `agent-console/scripts/check.sh` and
`agentprof/scripts/check.sh` — ALL GREEN.
