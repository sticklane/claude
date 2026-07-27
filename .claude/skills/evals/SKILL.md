---
name: evals
description: Scaffolds and runs stored artifact-assertion and trigger evals for the toolkit's own skills - each scenario builds a fixture repo, runs the skill under test headlessly inside it, and grades what it produced or whether it activated at all. Heavyweight - every scenario is a paid headless session, so a run is scoped to one skill, priced against a budget ceiling, and ledgered.
argument-hint: "[skill-name]"
---

**Cost contract.** Every scenario spawns a paid headless session at the
runtime profile's session model, so this
skill is launched only when a specific question needs it — never to check that
things still work. An agent may launch it when a skill's trigger or behavior
is actually in question (a description was just changed, a census shows a
skill that never fires, a review found a routing failure), and only under all
four of: scope the run to one skill (`evals/run.sh <skill>`); state the budget
and the last run's observed per-scenario cost before launching; leave
`EVAL_BUDGET_USD` in force so the runner stops rather than overruns; report
the spend the run reported afterward. Anything broader than one skill, or any
run that would exceed the budget, is the human's call. Prior runs' costs are
in `evals/cost-ledger.jsonl`.

Run (or first scaffold) the stored evalset for the skill named in
$ARGUMENTS. The runner (`evals/run.sh`) and the fixture scenarios it
consumes ship in the toolkit repo, not with installs — /evals is not
usable from plugin installs. Grading has two layers: v1 artifact
assertions (what a run produced) stay primary, and v2 adds opt-in
trajectory assertions (how the run got there) via `EVAL_TRANSCRIPT`
(specs/archive/skill-evals/SPEC.md, specs/trajectory-evals/SPEC.md). A
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
- `max-turns.txt` (optional) — one integer, capping the session's turns for
  this scenario. A trigger scenario needs only enough turns to observe the
  routing decision; an explicit `MAX_TURNS` overrides the file.

## Trigger scenarios

An artifact scenario grades what a run produced after being told which skill
to use. A **trigger** scenario grades the decision instead: its `prompt.txt`
describes the task in a user's words and never names the skill, and its
`assert.sh` calls the shared grader —

```
bash "$EVALS_LIB/assert-trigger.sh" fired     <skill>   # it should have fired
bash "$EVALS_LIB/assert-trigger.sh" not-fired <skill>   # a neighbour's job
```

Activation is read from `EVAL_TRANSCRIPT`: Claude Code emits a `Skill` tool
call, Codex and Antigravity leave a read of the skill's `SKILL.md`, and the
grader accepts either — so one scenario grades the same under any runtime.

**Every evalset with trigger coverage carries negative cases.** A positive-only
set cannot catch the failure that costs the most: a description broad enough to
pull the skill into a neighbour's work. Pair each `fired` case with a
`not-fired` case drawn from the nearest skill's charter — the
critique/prose-review split is the worked example (`evals/critique/03-` and
`04-`). Trigger failures are description failures: fix the `description`
frontmatter, not the body.

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

## Coverage policy and the adversarial-scenario convention

Which skills need an evalset — and to what bar — is set by the tier table in
[evals/COVERAGE.md](../../../evals/COVERAGE.md), enforced model-free by
`bash evals/lint-eval-coverage.sh` (invoked directly, never wired into
`run.sh`, which spawns paid sessions at the runtime profile's session model).
Read that table rather than restating
it here: Tier A skills require ≥2 scenarios including at least one
adversarial — a scenario whose correct outcome is to refuse, flag, or not act,
named with the `NN-adv-*` directory convention so the lint can spot it without
executing anything. Tier B skills stand on a named model-free test; Tier C
skills are waived with a recorded reason. A new skill missing from the table
fails the lint.

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
`.claude/agents/` from this checkout into `$EVAL_DIR/.claude/`, provisions
the same skill and declared dependencies under Codex's active
`.agents/skills/` discovery layout, and runs
the prompt under the scenario's `timeout-seconds.txt` value (default 900)
with a fixed allowlist — a
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
