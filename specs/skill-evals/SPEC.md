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
is three files: a fixture builder, a prompt, and an assertion script; the
runner executes the skill headlessly against the fixture and the
assertions grade the artifacts.

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
  the runner provides), `prompt.txt` (the user turn, may reference
  fixture paths), `assert.sh` (runs inside `$EVAL_DIR` after the session;
  exit 0 = pass, non-zero output explains what failed). An optional
  `allowed-tools.txt` overrides the runner's default allowlist.
- R3: `evals/run.sh` (committed, `bash -n`-clean) takes an optional skill
  name filter; for each matching scenario it creates a fresh temp
  `$EVAL_DIR`, runs `setup.sh`, invokes
  `claude -p "$(cat prompt.txt)" --permission-mode dontAsk --max-turns 40`
  with the scenario's allowlist (default:
  `Read,Edit,Write,Glob,Grep,Bash(git *)` plus Task for skills that fan
  out), runs `assert.sh`, and prints a one-line pass/fail per scenario
  plus a summary; exits non-zero if any scenario failed.
- R4: one working evalset ships: `evals/breakdown/01-small-spec/` whose
  fixture contains a 2-requirement SPEC.md; assertions check that
  `tasks/NN-*.md` files were created, each has `Status:`, `Depends on:`,
  and an `## Acceptance` section containing at least one backticked
  command, and the SPEC.md gained a `Parallelization` section.
- R5: exact runner script and example scenario contents live in
  `.claude/skills/evals/reference.md` (config JSON/scripts stay out of
  SKILL.md bodies per CLAUDE.md conventions); the committed
  `evals/run.sh` and the reference copy must not drift — the reference
  points at the file rather than duplicating it in full.
- R6: CLAUDE.md's Testing changes section gains one sentence pointing to
  /evals as the repeatable complement to fresh-session testing; README's
  table gains an /evals row.
- R7: the skill states where artifacts go (`evals/<skill>/…`, committed)
  and the next pipeline step (run before committing any skill change;
  /distill a failure's lesson if it exposed a skill-authoring gap).
- R8: antigravity port: `antigravity/.agents/workflows/evals.md` — same
  scenario layout and assertions, but the run step hands the user Agent
  Manager launches instead of headless `claude -p` (Antigravity has no
  headless CLI).

## Out of scope

- Trajectory assertions (transcript greps) — v2, per scope decision.
- CI wiring (GitHub Actions) — the runner is CI-ready but wiring is the
  consuming repo's business.
- Evalsets for every skill — one reference evalset (/breakdown) ships;
  others accrete via /distill when regressions bite.
- plugin.json version (owned by the hardening-quick-wins spec).

## Acceptance criteria

- [ ] `grep -q "disable-model-invocation: true" .claude/skills/evals/SKILL.md` (R1)
- [ ] `test -x evals/run.sh && bash -n evals/run.sh` (R3)
- [ ] `test -f evals/breakdown/01-small-spec/setup.sh && test -f evals/breakdown/01-small-spec/prompt.txt && test -f evals/breakdown/01-small-spec/assert.sh` (R2, R4)
- [ ] `bash -n evals/breakdown/01-small-spec/setup.sh && bash -n evals/breakdown/01-small-spec/assert.sh` (R4)
- [ ] `grep -q "evals" CLAUDE.md && grep -q "/evals" README.md` (R6)
- [ ] `grep -qi "evals" .claude/skills/evals/reference.md` and it references `evals/run.sh` rather than duplicating it (R5)
- [ ] `test -f antigravity/.agents/workflows/evals.md` (R8)
- [ ] End to end: `./evals/run.sh breakdown` completes with a pass verdict on a machine with the `claude` CLI authenticated (requires a real headless run; this is the check that gates calling the harness done).

## Open questions

(none)
