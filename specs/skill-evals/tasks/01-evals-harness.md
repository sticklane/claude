# Task 01: /evals skill, runner, and the breakdown reference evalset

Status: in-progress
Depends on: ../../hardening-quick-wins/tasks/01-untrusted-data.md (README.md overlap; cross-spec waves in ../SPEC.md)
Budget: 50 turns
Spec: ../SPEC.md (requirements R1–R8)

## Goal

A human-only /evals skill scaffolds and runs stored artifact-assertion
scenarios; `evals/run.sh` provisions the skill under test (plus agents)
into a fresh fixture, runs it headlessly with a fixed allowlist under
`timeout 900`, and grades with each scenario's `assert.sh`. One working
evalset for /breakdown ships, CLAUDE.md/README point at the harness, and
an antigravity workflow ports the flow.

## Touch

- `.claude/skills/evals/SKILL.md` (new), `.claude/skills/evals/reference.md` (new)
- `evals/run.sh` (new), `evals/breakdown/01-small-spec/{setup.sh,prompt.txt,assert.sh,allowed-tools.txt}` (new)
- `CLAUDE.md` (one sentence in Testing changes)
- `README.md` (one table row)
- `antigravity/.agents/workflows/evals.md` (new)

## Steps

1. Write `evals/run.sh` per R3: per scenario — fresh `$EVAL_DIR`,
   `setup.sh`, copy `.claude/skills/<skill>/` + `.claude/agents/` into
   `$EVAL_DIR/.claude/`, cd in, `timeout 900 claude -p "$(cat
   prompt.txt)" --permission-mode dontAsk --max-turns 40` with the
   scenario's allowlist (default fixed list, no Task), then `assert.sh`;
   per-scenario pass/fail lines, summary, non-zero exit on any failure.
   `chmod +x`.
2. Write the breakdown evalset per R4 (fixture spec at
   `specs/demo/SPEC.md`, prompt `/breakdown specs/demo/SPEC.md`,
   `allowed-tools.txt` including `Task`, assertions on
   `specs/demo/tasks/NN-*.md` structure and the Parallelization
   section).
3. Write SKILL.md per R1/R7 (disable-model-invocation: true; scaffold /
   run / interpret; artifact location + next step) and reference.md per
   R5 (scenario files verbatim; link to `evals/run.sh` by path).
4. CLAUDE.md Testing changes sentence; README table row.
5. Antigravity workflow per R8.

## Acceptance

- [ ] `grep -q "disable-model-invocation: true" .claude/skills/evals/SKILL.md` → pass
- [ ] `test -x evals/run.sh && bash -n evals/run.sh && grep -q "timeout" evals/run.sh && grep -q "\.claude" evals/run.sh` → pass
- [ ] `test -f evals/breakdown/01-small-spec/setup.sh && test -f evals/breakdown/01-small-spec/prompt.txt && test -f evals/breakdown/01-small-spec/assert.sh && grep -q "Task" evals/breakdown/01-small-spec/allowed-tools.txt` → pass
- [ ] `bash -n evals/breakdown/01-small-spec/setup.sh && bash -n evals/breakdown/01-small-spec/assert.sh && grep -q "specs/demo" evals/breakdown/01-small-spec/prompt.txt` → pass
- [ ] `grep -q "evals/run.sh" .claude/skills/evals/reference.md` → pass
- [ ] `grep -qi "evals" CLAUDE.md && grep -q "/evals" README.md` → pass
- [ ] `test -f antigravity/.agents/workflows/evals.md` → pass
- [ ] `./evals/run.sh breakdown` → all scenarios pass (requires authenticated `claude` CLI; run locally — this is the gate for calling the harness done)
