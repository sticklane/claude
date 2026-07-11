# prioritize — script bundle (not a triggerable skill)

This directory is a **script bundle** supporting
`antigravity/.agents/workflows/prioritize.md`, not a model-invocable skill.
It intentionally has **no `SKILL.md`**.

In the source toolkit, `prioritize` is `disable-model-invocation: true`
(`.claude/skills/prioritize/SKILL.md`) — only a human launches it. The
Antigravity mirror preserves that: the human-facing entry point is the
workflow at `antigravity/.agents/workflows/prioritize.md`, and this
directory holds only the scanner it shells out to. Adding a `SKILL.md` here
would make the port model-triggerable, contradicting the source contract.

## Contents

- `prioritize_scan.py` — read-only per-repo scan of reorderable work
  (pending/blocked/deferred/draft tasks plus specs with no `tasks/`
  breakdown yet), printing one markdown table. Invoked by the workflow.
- `test_prioritize_scan.py` — its test suite (`python3 -m pytest -q`).
