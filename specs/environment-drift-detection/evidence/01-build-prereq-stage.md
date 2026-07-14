# Verification: 01-build-prereq-stage

Verdict: PASS

## Criteria

1. `grep -c "build/dist prerequisite" bin/install-gates` → 2 (>0). PASS.

2. `bash tests/test_install_gates.sh` → `pass: 168 fail: 0`, exit 0. Confirmed
   the three new R1 cases are present in the diff (node .scripts.build,
   .claude/build-prereq marker, neither-signal regression guard) and all
   pass. PASS.

3. MANUAL — Node repo with `package.json` `.scripts.build`: created scratch
   repo, ran `bin/install-gates .`, generated `scripts/check.sh` contains:

   ```
   run_stage "build" npm run build
   run_stage "lint" npm run lint
   run_stage "tests" npm run test
   ```

   Build stage is first, ahead of lint/tests. PASS.

4. MANUAL — repo with `.claude/build-prereq` marker (python stack, content
   `make compile-protos`): generated `scripts/check.sh` contains:

   ```
   run_stage "build" make compile-protos
   run_stage "lint" ruff check .
   ```

   Literal marker command runs first as the build stage. PASS.

5. MANUAL — repo with neither signal (python stack, no marker, no node
   .scripts.build): generated `scripts/check.sh` contains only
   `run_stage "lint" ruff check .` — no build stage line at all. PASS.

## Gates

`bash tests/test_install_gates.sh` is this repo's relevant test suite for
this change; ran green above (168/168). No separate scripts/check.sh
present at repo root to run additionally (this repo doesn't self-install
gates in this worktree — not required by the task's acceptance list beyond
the test suite).

## Scope / diff check

`git diff 01c50cc --name-only`:

- bin/install-gates (in Touch)
- tests/test_install_gates.sh (in Touch)
- specs/environment-drift-detection/tasks/01-build-prereq-stage.md (task
  file itself — allowed)

`templates/check.sh.tmpl` (also listed in Touch) was NOT modified — task
notes this is expected ("template unchanged (@STAGES@ already ordered)").
No out-of-Touch files changed.

## Task-file append-only check

`git diff 01c50cc -- specs/environment-drift-detection/tasks/01-build-prereq-stage.md`
shows only a `<!-- PLAN (build) ... -->` HTML-comment block inserted between
the header fields and `## Goal`. Goal/Steps/Touch/Budget/acceptance-criterion
text is byte-identical to base. Status line remains `in-progress`; acceptance
checkboxes remain unticked (`- [ ]`). This is within the allowed edit set
(plan comment block).

## Overfitting check

Test fixtures use distinct literal commands from what I exercised manually
(test uses `pnpm -r build` marker / `tsc -b` build script; my manual repros
used `make compile-protos` / default `npm run build`), and both passed via
the same generic code path — no evidence of hardcoding to exact test
strings. Tests assert structural presence + ordering of `run_stage` lines,
not full check.sh text equality.

## Commands run (abbreviated)

- `grep -c "build/dist prerequisite" bin/install-gates`
- `bash tests/test_install_gates.sh`
- `git diff 01c50cc --stat` / `--name-only`
- `git diff 01c50cc -- specs/environment-drift-detection/tasks/01-build-prereq-stage.md`
- Three scratch-repo manual installs under
  `/private/tmp/claude-501/.../scratchpad/verify-install-gates/{node-repo,marker-repo,neither-repo}`
  running `bin/install-gates .` and inspecting generated `scripts/check.sh`.
