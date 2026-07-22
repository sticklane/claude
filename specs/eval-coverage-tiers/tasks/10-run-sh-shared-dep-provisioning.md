Status: done
Discovered-from: specs/eval-coverage-tiers/tasks/02-prioritize-evalset.md
Spec: ../SPEC.md
Blocking: no
Touch: evals/run.sh, evals/prioritize/01-reorder-priorities/setup.sh, evals/prioritize/01-reorder-priorities/skill-deps.txt, evals/prioritize/02-adv-out-of-scope/setup.sh, evals/prioritize/02-adv-out-of-scope/skill-deps.txt, tests/test_run_sh_shared_deps.sh, specs/eval-coverage-tiers/tasks/10-run-sh-shared-dep-provisioning.md

# evals/run.sh should provision shared skill deps for every scenario

run.sh copies only the skill under test into the scenario sandbox, so any
skill whose scripts import sibling dirs (`.claude/skills/_shared`,
`.claude/skills/workboard`, `runtimes/`) crashes unless each scenario's
setup.sh hand-copies them — per-scenario boilerplate the prioritize
evalset (task 02) now carries. Provisioning `_shared` + `runtimes/` (and
script-dep skills) centrally in run.sh would remove it. (Worker-reported
discovery; vet/rewrite before promoting.)

## Approach (vetted)

Discovery confirmed against `evals/run.sh`: the fixture-build block provisions
only the single skill under test into `.claude/skills/` (it copies `_shared`
into the `.agents/skills/` layout, but never into `.claude/skills/`, and never
copies `runtimes/`). So any skill whose scripts import `.claude/skills/_shared`
or the top-level `runtimes/` crashes unless each scenario hand-copies them —
which both `evals/prioritize/*/setup.sh` did (identical `_shared` + `workboard`
+ `runtimes/` boilerplate, since `prioritize_scan.py` loads `workboard.py`,
which in turn imports both).

Fix: `run.sh` provisions the two non-skill shared assets — `.claude/skills/_shared`
(from `SKILLS_ROOT`) and `runtimes/` (from `ROOT`) — into every fixture,
guarded by existence checks so external-repo evals are unaffected. Neither has
a `SKILL.md`, so there is zero skill-listing pollution. Sibling script-dep
*skills* (e.g. `workboard`) are declared per scenario via an optional
`skill-deps.txt` (mirroring the existing `allowed-tools.txt` convention; one
skill dir name per line, blanks/`#`-comments ignored) — keeping the sandbox to
the skill under test plus its named deps rather than provisioning every skill.
The two prioritize scenarios drop the boilerplate and declare `workboard`.

## Acceptance

- [x] `bash tests/test_run_sh_shared_deps.sh` exits 0 — proves `run.sh`
      provisions `.claude/skills/_shared`, top-level `runtimes/`, and a
      `skill-deps.txt`-declared sibling skill into every fixture (written
      RED-first: the assert reported "missing _shared/headers.py" against the
      pre-change runner; `test_run_sh_shared_deps.sh` absent before this task).
- [x] `grep -c 'skill-deps.txt' evals/run.sh` ≥ 1 and
      `grep -c 'SKILLS_ROOT/_shared' evals/run.sh` ≥ 1 — central shared-dep
      provisioning plus the skill-deps mechanism live in the runner (literal
      `skill-deps.txt` absent from `run.sh` before this task).
- [x] `grep -Ec 'cp -R.*(_shared|runtimes|workboard)'` over each of
      `evals/prioritize/01-reorder-priorities/setup.sh` and
      `evals/prioritize/02-adv-out-of-scope/setup.sh` → 0 (boilerplate
      removed), and `grep -c '^workboard$'` over each scenario's
      `skill-deps.txt` → 1 (sibling dep declared).
- [x] `bash evals/runner-selftest.sh` exits 0 — the runner's existing
      RUNNER_CMD/EVALS_ROOT plumbing is unregressed.
