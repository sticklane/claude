# Skill eval harness (/evals)

## Problem

The toolkit's testing story for its own skills is "run it in a fresh
session and watch" (CLAUDE.md, Testing changes) — manual, unrepeatable,
and never re-run when a skill, prompt, or model changes. Both external
playbooks converge on stored evalsets re-run on every change
(docs/external-playbooks.md: ADK trajectory evals, OpenAI eval-driven
development). v1 checks artifacts only — what a skill run produced — per
the maintainer's scope decision; trajectory checks are a later extension.

## Solution

A new human-only skill `.claude/skills/evals/` that scaffolds and runs
stored eval scenarios, plus a committed runner script `evals/run.sh` and
one working evalset for /breakdown as the reference example. A scenario
is three files: a fixture builder, a prompt, and an assertion script.
The runner **provisions the skill under test into the fixture** (copies
`.claude/skills/<skill>/` and `.claude/agents/` from the toolkit checkout
into `$EVAL_DIR/.claude/`), cd's into `$EVAL_DIR`, and runs the session
there — a deliberate, documented exception to the toolkit's
"self-contained headless prompt" rule, because exercising the real skill
text is the entire point of an eval.

## Requirements

- R1: `.claude/skills/evals/SKILL.md` exists with
  `disable-model-invocation: true` (running evals spawns paid headless
  sessions — humans launch it), `argument-hint: "[skill-name]"`, and a
  procedure: scaffold a scenario for the named skill if none exists, run
  the harness, and interpret failures as either a skill regression (fix
  the skill) or an intentional behavior change (update the scenario in
  the same commit as the skill change).
- R2: scenario layout is `evals/<skill>/<NN-name>/` containing exactly:
  `setup.sh` (builds a fixture repo in `$EVAL_DIR`, an empty directory
  the runner provides), `prompt.txt` (the user turn; invokes the skill
  as a slash command with fixture-relative paths, e.g.
  `/breakdown specs/demo/SPEC.md` — no `$EVAL_DIR` variables, since the
  runner does not expand them), `assert.sh` (runs with CWD `$EVAL_DIR`
  after the session; exit 0 = pass, non-zero with output explaining what
  failed). An optional `allowed-tools.txt` (one flag value on one line)
  replaces the runner's default allowlist for that scenario.
- R3: `evals/run.sh` (committed, `bash -n`-clean) takes an optional
  skill-name filter; for each matching scenario it: creates a fresh temp
  `$EVAL_DIR`; runs `setup.sh`; copies `.claude/skills/<skill>/` and the
  whole `.claude/agents/` directory from the toolkit checkout into
  `$EVAL_DIR/.claude/`; cd's into `$EVAL_DIR`; runs
  `timeout 900 claude -p "$(cat prompt.txt)" --permission-mode dontAsk
  --max-turns 40` with the scenario's allowlist (default, a fixed list:
  `Read,Edit,Write,Glob,Grep,Bash(git *)` — no Task; fan-out skills add
  Task via their scenario's `allowed-tools.txt`); then runs `assert.sh`.
  A timeout or non-zero assert is a scenario failure. It prints one
  pass/fail line per scenario plus a summary and exits non-zero if any
  scenario failed.
- R4: one working evalset ships: `evals/breakdown/01-small-spec/` whose
  `setup.sh` writes a 2-requirement spec at `specs/demo/SPEC.md` (no
  open questions), whose `prompt.txt` is `/breakdown specs/demo/SPEC.md`,
  whose `allowed-tools.txt` includes `Task` (breakdown fans out to
  scout/critic agents, which the runner provisioned in R3), and whose
  `assert.sh` checks: `specs/demo/tasks/` contains at least two
  `NN-*.md` files; each has `Status:`, `Depends on:`, and an
  `## Acceptance` section containing at least one backticked command;
  and `specs/demo/SPEC.md` gained a `Parallelization` section.
- R5: `.claude/skills/evals/reference.md` contains the example scenario
  files verbatim (setup.sh / prompt.txt / assert.sh / allowed-tools.txt
  for the breakdown evalset) and links to `evals/run.sh` by path instead
  of duplicating the runner's contents.
- R6: CLAUDE.md's Testing changes section gains one sentence pointing to
  /evals as the repeatable complement to fresh-session testing; README's
  "What's in the box" table gains an /evals row.
- R7: the skill states where artifacts go (`evals/<skill>/…`, committed)
  and the next pipeline step (run before committing any skill change;
  /distill a failure's lesson if it exposed a skill-authoring gap).
- R8: antigravity port: `antigravity/.agents/workflows/evals.md` — same
  scenario layout and assertions, but the run step hands the user Agent
  Manager launches instead of headless `claude -p` (Antigravity has no
  headless CLI), with the skill/agents provisioning done by copying into
  the fixture's `.agents/` instead.

## Out of scope

- Trajectory assertions (transcript greps) — v2, per scope decision.
- CI wiring (GitHub Actions) — the runner is CI-ready (bounded by
  `timeout`) but wiring is the consuming repo's business.
- Evalsets for every skill — one reference evalset (/breakdown) ships;
  others accrete via /distill when regressions bite.
- plugin.json version (owned by the hardening-quick-wins spec).

## Acceptance criteria

- [ ] `grep -q "disable-model-invocation: true" .claude/skills/evals/SKILL.md` (R1)
- [ ] `test -x evals/run.sh && bash -n evals/run.sh` (R3)
- [ ] `grep -q "\.claude" evals/run.sh && grep -q "timeout" evals/run.sh` — provisioning copy and wall-clock bound present (R3)
- [ ] `test -f evals/breakdown/01-small-spec/setup.sh && test -f evals/breakdown/01-small-spec/prompt.txt && test -f evals/breakdown/01-small-spec/assert.sh && grep -q "Task" evals/breakdown/01-small-spec/allowed-tools.txt` (R2, R4)
- [ ] `bash -n evals/breakdown/01-small-spec/setup.sh && bash -n evals/breakdown/01-small-spec/assert.sh && grep -q "specs/demo" evals/breakdown/01-small-spec/prompt.txt` (R4)
- [ ] `grep -q "evals/run.sh" .claude/skills/evals/reference.md` (R5)
- [ ] `grep -qi "evals" CLAUDE.md && grep -q "/evals" README.md` (R6)
- [ ] `test -f antigravity/.agents/workflows/evals.md` (R8)
- [ ] Scaffold branch: in a fresh session, `/evals handoff` (a skill with no evalset) produces `evals/handoff/01-*/setup.sh`, `prompt.txt`, and `assert.sh` (manual check of R1's scaffold path).
- [ ] End to end: `./evals/run.sh breakdown` completes with a pass verdict on a machine with the `claude` CLI authenticated (requires a real headless run; this is the check that gates calling the harness done).

## Open questions

(none)

## Parallelization

Single task (01) — nothing to parallelize within this spec.

### Cross-spec ordering (all four specs on one queue)

Touch lists overlap ACROSS specs (the drain files and README), so when
draining all four together, dispatch in waves:

1. Wave 1 (concurrent): hardening 01, 02, 04
2. Wave 2 (concurrent): hardening 03 (after 01: drain prompts),
   skill-evals 01 (after hardening 01: README)
3. Wave 3: evidence-artifacts 01 (after hardening 03: drain reference)
4. Wave 4: drain-tournament 01 (after evidence: drain SKILL + reference
   — its Tournament section builds on the final prompt wording)
