---
description: Scaffold and run stored artifact-assertion evals for the toolkit's skills - each scenario builds a fixture repo, runs the skill under test headlessly inside it via evals/run.sh, and grades what it produced. Human-only because every run spawns paid headless sessions.
---

Run (or first scaffold) the stored evalset for the named skill. Same
scenario layout and assertions as the Claude Code toolkit — a scenario
is `evals/<skill>/<NN-name>/` containing `setup.sh` (builds a fixture
repo in `$EVAL_DIR`), `prompt.txt` (the user turn, a slash command with
fixture-relative paths, no `$EVAL_DIR` variables), `assert.sh` (runs
with CWD the fixture; exit 0 = pass, non-zero with output explaining
what failed). Both scripts run under bare `bash`, and macOS's system bash
is 3.2 — write them to bash 3.2 (no `declare -A` or other bash-4+ syntax),
or they misbehave silently rather than erroring. Antigravity's headless
CLI (`agy -p --new-project ...`, the `antigravity-cli` package's binary)
is confirmed safe to drive this runner as of 2026-07-13 (see
`runtimes/antigravity.md`'s Headless section — `--new-project` fixed a
workspace-isolation defect that previously made this unsafe);
`allowed-tools.txt` still has no Antigravity equivalent and is ignored
here (no per-tool allowlist flag exists — see the Headless section's
`<allowlist>` note).

1. **Scaffold if no evalset exists.** Create `evals/<skill>/01-<name>/`
   with the three files: a minimal fixture the skill can act on, the
   smallest honest prompt, assertions on the artifact contract the
   skill's SKILL.md promises — not incidental wording. Keep each
   `assert.sh` failure message under ~10 lines — that is the whole budget
   the grader returns to the orchestrator, never a transcript. Model it on
   the existing `/breakdown` scenario under `evals/breakdown/`, copying its
   file shapes. `chmod +x` both scripts.
2. **Run.** `./evals/run.sh <skill>` with `.claude/runtime.md` pointed at
   `antigravity` (no argument runs every evalset). Per scenario the runner
   builds a fresh fixture, copies `.agents/skills/<skill>/` plus the
   helper skills (`scout`, `critic`, `verifier`) and `.agents/workflows/`
   into the fixture so slash commands resolve, then runs the prompt there
   under a timeout via `agy -p --new-project ...` and grades with the
   scenario's `assert.sh` — same shape the Claude Code runner uses.
3. **Interpret failures.** Skill regression → fix the skill, scenario
   untouched. Intentional behavior change → update the scenario in the
   same commit as the skill change. Never loosen an assertion just to go
   green.

Artifacts: scenarios live in `evals/<skill>/<NN-name>/`, committed. If a
failure exposed a skill-authoring gap, apply the distill skill to capture
the lesson. Next step: run the affected evalset before committing any skill
change.
