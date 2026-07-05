#!/usr/bin/env bash
# Canonical check: byte-compile + smoke-test that both views render.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m py_compile agent-console.py
echo "py_compile: ok"

python3 - <<'PY'
import importlib.util
spec = importlib.util.spec_from_file_location("ac", "agent-console.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

model = m.collect()
assert model["total_skills"] > 0, "no skills collected"
skills_html = m.render_skills(model)
assert "<title>" in skills_html and "\U0001f6e0" not in skills_html, "emoji in UI"
low = skills_html.lower()
# banned decorative chrome (not skill descriptions, which may mention "LLM")
assert "no llm" not in low and "no claude usage" not in low, "stray meta-label in UI"

# R4 seam: a workboard.assemble()-shaped fixture through the adapter into
# render_workboard, proving the two are wired correctly without a live scan.
fixture = {
    "repos": [
        {
            "path": "/tmp/fixture-repo",
            "name": "fixture-repo",
            "git": {"branch": "main", "dirty": 1, "ahead": 0, "behind": 0},
            "specs": [],
            "handoffs": [],
            "sessions": [],
        }
    ],
    "orphan_sessions": [],
    "inbox": [
        {
            "severity": "warning",
            "state": "needs-review",
            "repo": "fixture-repo",
            "what": "1 uncommitted change(s), no live session",
            "why": "on branch main — commit (then push) or stash",
            "age_ts": 0,
        }
    ],
    "liveness_unknown": False,
}
board = m._adapt_board(fixture, [], [])
board_html = m.render_workboard(board)
assert "fixture-repo" in board_html, "adapter seam: fixture repo missing from render"

# regression: PID epoch-ms timestamps must parse (not collapse to 0)
assert abs(m._iso(1783172065122) - 1783172065.122) < 1
assert m._iso("junk") == 0.0

print(f"render: ok ({model['total_skills']} skills, adapter seam ok)")
PY

python3 -m unittest discover -s tests -p 'test_*.py' -q
echo "check: PASS"
