# Task 08: Mirror and docs fixes — ag evals/build, external-playbooks, README, tournament SPEC grep

Status: pending
Depends on: 07
Budget: 30 turns
Spec: ../SPEC.md (cluster 08)

## Goal

Five verified doc/mirror drifts fixed: the antigravity evals grade step
runs `bash assert.sh` from the fixture where the file doesn't exist; the
antigravity build workflow pauses for review (deadlocking unattended
launches) and ends with "restart fresh" instead of a verdict; the
external-playbooks ranking sentence credits the verifier for what drain
does mechanically; README Option C copies skills/agents but not rules/ and
its caveat names only one rule; and drain-tournament SPEC's acceptance
grep `grep -q "\-t1\|t1"` is a broken escape that matches almost anything.
(Depends on task 07: both edit the antigravity build/drain workflows —
apply on top.)

## Touch

- `antigravity/.agents/workflows/evals.md` (grade step)
- `antigravity/.agents/workflows/build.md` (steps 2 and 4)
- `docs/external-playbooks.md` (~line 48)
- `README.md` (Option C block + caveat)
- `specs/drain-tournament/SPEC.md` (acceptance grep, ~line 99)

## Steps

1. In the antigravity evals workflow's grade step, provision assert.sh:
   copy the scenario dir into the fixture, or invoke it by absolute path
   like the CC runner does — the fixture CWD does not contain it.
2. In the antigravity build workflow: step 2 drops the unconditional
   "pause for review before executing" — add "unless launched unattended
   by a workflow, in which case plan as a comment block and proceed"
   (matching CC build); step 4 returns a verdict (DONE/DEFERRED/BLOCKED)
   instead of "restart fresh".
3. In docs/external-playbooks.md, change "verifier ranks the survivors"
   to "drain ranks the survivors mechanically".
4. In README Option C: add a `cp -r ~/agentic-toolkit/.claude/rules ...`
   line alongside the skills/agents copies, and reword the caveat to
   mention BOTH rules (token-discipline and untrusted-data) and where
   they land for global use.
5. In specs/drain-tournament/SPEC.md, replace the
   `grep -q "\-t1\|t1"` acceptance grep with the portable task-file form
   (e.g. `grep -qF -- "-t1"` against the branch/task-file naming) so it
   can't match stray "t1" substrings via a broken escape.

## Acceptance

- [ ] `grep -qE "cp .*assert|absolute path" antigravity/.agents/workflows/evals.md` → exit 0 (assert.sh provisioned)
- [ ] `grep -q "unless launched unattended" antigravity/.agents/workflows/build.md && ! grep -q "restart fresh" antigravity/.agents/workflows/build.md && grep -qi "verdict" antigravity/.agents/workflows/build.md` → exit 0
- [ ] `grep -q "drain ranks the survivors mechanically" docs/external-playbooks.md && ! grep -q "verifier ranks the survivors" docs/external-playbooks.md` → exit 0
- [ ] `grep -q "agentic-toolkit/.claude/rules" README.md && sed -n '/Option C/,/Option D/p' README.md | grep -q "untrusted-data"` → exit 0 (rules copied; caveat names both rules)
- [ ] `! grep -qF '\-t1\|t1' specs/drain-tournament/SPEC.md && grep -qF -- "-t1" specs/drain-tournament/SPEC.md` → exit 0 (broken escape replaced with a portable form that still checks tournament naming)
