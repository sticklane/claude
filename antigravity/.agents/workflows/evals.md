---
description: Scaffold and run stored artifact-assertion evals for the toolkit's skills - build a fixture, hand the user an Agent Manager launch per scenario, then grade what the run produced with the scenario's assert.sh.
---

Run (or first scaffold) the stored evalset for the named skill. Same
scenario layout and assertions as the Claude Code toolkit — a scenario
is `evals/<skill>/<NN-name>/` containing `setup.sh` (builds a fixture
repo in `$EVAL_DIR`), `prompt.txt` (the user turn, a slash command with
fixture-relative paths, no `$EVAL_DIR` variables), `assert.sh` (runs
with CWD the fixture; exit 0 = pass, non-zero with output explaining
what failed). Antigravity has no headless CLI, so the run step hands the
user Agent Manager launches instead of `claude -p`; `allowed-tools.txt`
has no Antigravity equivalent and is ignored here.

1. **Scaffold if no evalset exists.** Create `evals/<skill>/01-<name>/`
   with the three files: a minimal fixture the skill can act on, the
   smallest honest prompt, assertions on the artifact contract the
   skill's SKILL.md promises — not incidental wording. Keep each
   `assert.sh` failure message under ~10 lines — that is the whole budget
   the grader returns to the orchestrator, never a transcript. `chmod +x`
   both scripts.
2. **Provision the fixture.** Per scenario: create a fresh empty
   directory, run `EVAL_DIR=<dir> bash setup.sh`, then copy
   `.agents/skills/<skill>/` plus the helper skills that are agents in
   the Claude Code port (`scout`, `critic`, `verifier`) into
   `<dir>/.agents/skills/`, and `.agents/workflows/` into
   `<dir>/.agents/workflows/` so slash commands resolve.
3. **Hand the user the launch.** One Agent Manager launch per scenario:
   a fresh conversation rooted at the fixture directory whose first
   message is the contents of `prompt.txt`. Wait for the user to report
   the session finished — do not grade a run that is still going.
4. **Grade.** With CWD the fixture directory, invoke the scenario's
   assert.sh by absolute path from the toolkit repo — the fixture does
   not contain it — e.g.
   `(cd <fixture> && bash <toolkit>/evals/<skill>/<NN-name>/assert.sh)`,
   the same shape the Claude Code runner uses. Report one pass/fail
   line per scenario and a summary.
5. **Interpret failures.** Skill regression → fix the skill, scenario
   untouched. Intentional behavior change → update the scenario in the
   same commit as the skill change. Never loosen an assertion just to go
   green.

Artifacts: scenarios live in `evals/<skill>/<NN-name>/`, committed. Next
step: run the affected evalset before committing any skill change.
