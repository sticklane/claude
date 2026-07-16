---
name: evals
description: Scaffolds and runs stored artifact-assertion evals for the toolkit's own skills - each scenario builds a fixture repo, runs the skill under test headlessly inside it, and grades what it produced. Human-only because every run spawns paid headless sessions.
argument-hint: "[skill-name]"
disable-model-invocation: true
---

Run (or first scaffold) the stored evalset for the skill named in
$ARGUMENTS. The runner (`evals/run.sh`) and the fixture scenarios it
consumes ship in the toolkit repo, not with installs — /evals is not
usable from plugin installs. Grading has two layers: v1 artifact
assertions (what a run produced) stay primary, and v2 adds opt-in
trajectory assertions (how the run got there) via `EVAL_TRANSCRIPT`
(specs/skill-evals/SPEC.md, specs/trajectory-evals/SPEC.md). A
scenario is a directory
`evals/<skill>/<NN-name>/` containing exactly:

- `setup.sh` — builds a fixture repo in `$EVAL_DIR`, an empty directory
  the runner provides.
- `prompt.txt` — the user turn; invokes the skill as a slash command with
  fixture-relative paths (e.g. `/breakdown specs/demo/SPEC.md`). No
  `$EVAL_DIR` variables — the runner does not expand them.
- `assert.sh` — runs with CWD `$EVAL_DIR` after the session; exit 0 =
  pass, non-zero with output explaining what failed.
- `allowed-tools.txt` (optional) — one flag value on one line, replacing
  the runner's default allowlist for this scenario (fan-out skills add
  `Task` here; the default deliberately lacks it).
- `teardown.sh` (optional) — reverses external live-service state the
  scenario seeded (scratch tasks, notes). Runs whenever setup.sh was
  attempted, pass or fail; a teardown failure fails the scenario, since
  leaked scratch state must be loud.

For a v2 trajectory assertion, `assert.sh` may also read `EVAL_TRANSCRIPT`
— an environment variable the runner sets to the absolute path of the
run's JSONL transcript — to grade _how_ a run behaved, not only the
artifacts it produced. It is opt-in and purely additive: a scenario that
ignores it keeps grading artifacts exactly as before, so no existing
`assert.sh` needs editing. The runner leaves it empty and warns when no
transcript is locatable, so a trajectory assertion guards for an empty
value first, then greps the JSONL — e.g.
`grep -q '"subagent_type":"scout"' "$EVAL_TRANSCRIPT"` to confirm the skill
delegated to a scout rather than reading the codebase directly. Trajectory
failure messages respect the same ~10-line budget as artifact ones (below).

## 1. Scaffold if no evalset exists

If `evals/<skill>/` has no scenario, create `evals/<skill>/01-<name>/`
with the four files above: a minimal fixture the skill can act on, the
smallest honest prompt, and assertions on the artifact contract the
skill's SKILL.md promises — not on incidental wording a model might vary.
Keep each `assert.sh` failure message under ~10 lines — that is the whole
budget the grader returns to the orchestrator, never a transcript.
Copy the shapes in [reference.md](reference.md) (the /breakdown scenario,
verbatim). `chmod +x` both scripts.

## 2. Run

`./evals/run.sh <skill>` (no argument runs every evalset). Per scenario
the runner builds a fresh fixture, copies `.claude/skills/<skill>/` and
`.claude/agents/` from this checkout into `$EVAL_DIR/.claude/` (plus the
`.agents/skills/<skill>/` layout Antigravity/Codex discover from, so the
same fixture is runtime-portable — see `runtimes/README.md`), and runs
the prompt there under `timeout 900` with a fixed allowlist — a
deliberate, documented exception to the toolkit's self-contained-prompt
rule, because exercising the real skill text is the entire point.

External repos host their own evalsets by overriding the source roots:
`EVALS_ROOT=<repo>/evals SKILLS_ROOT=<repo>/skills ./evals/run.sh` —
agents provision from SKILLS_ROOT's sibling `agents/` when present
(`AGENTS_ROOT` overrides). `MAX_TURNS` raises the claude-code turn cap
(default 40) for MCP-heavy skills.

## 3. Interpret failures

- Skill regression → fix the skill; the scenario stays untouched.
- Intentional behavior change → update the scenario in the same commit
  as the skill change. Never loosen an assertion just to go green.

Artifacts: scenarios live in `evals/<skill>/<NN-name>/`, committed; the
runner is `evals/run.sh`. If a failure exposed a skill-authoring gap,
/distill the lesson. Close with:
`Next stage: /evals <skill> before committing any change to that skill
(human-launched)`.
