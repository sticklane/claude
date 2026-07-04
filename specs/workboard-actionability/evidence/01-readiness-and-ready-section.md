# Evidence: Task 01 — Readiness computation + "Ready to start" section

VERDICT: PASS

Repo: /Users/sjaconette/claude — verified against working tree.

## Criterion 1 — `bash tests/test_workboard_actionability.sh`
Command: `bash tests/test_workboard_actionability.sh`
Result: PASS
```
workboard: 1 repos · 5 open specs · 6 open tasks · 0 active sessions · 1 need attention → .../wb.html
PASS: workboard actionability (R1-R3 subset)
EXIT: 0
```
Test quality: hermetic — exports HOME + CLAUDE_CONFIG_DIR to a tmp tree
(lines 18-20), copies fixtures, `git init`s each fixture repo, passes the
fixture repo as an EXPLICIT positional root (lines 26-33). Assertions are
non-tautological and map to computed output, verified against fixtures:
- single-ready: 01 `done`, 02 `pending` deps `01` (bare-numeric same-spec,
  satisfied) ⇒ asserts `/build specs/single-ready/tasks/02-build-it.md`
  (fully-resolved filename, not a glob).
- cross-spec: 01 `pending` deps `../../single-ready/tasks/01-foundation.md`
  (done) ⇒ asserts `/build specs/cross-spec/tasks/01-consume.md` (cross-spec).
- pending-dep: deps `../../multi-ready/tasks/02-beta.md` (pending) ⇒
  `absent '/build specs/pending-dep'` + `absent '/drain specs/pending-dep'`.
- unresolvable: deps `99` (no sibling) ⇒ absent build/drain + `has 'unresolved
  dependency'` + `has '>99</code>'` (offending id surfaced).
- multi-ready: 01+02 both pending, no deps ⇒ `has '/drain specs/multi-ready'`
  (one spec-level item, not per-task builds).
The `absent`/`has` pairs would fail if readiness were broken; no tautological
greps found.

## Criterion 2 — AST parse main workboard.py
Command: `python3 -c "import ast; ast.parse(open('.claude/skills/workboard/workboard.py').read())"`
Result: PASS — exit 0.

## Criterion 3 — AST parse antigravity mirror
Command: `python3 -c "import ast; ast.parse(open('antigravity/.agents/skills/workboard/workboard.py').read())"`
Result: PASS — exit 0.

## Criterion 4 — smoke run + "Ready to start" header
Command: `python3 .claude/skills/workboard/workboard.py --out /tmp/vwb.html --actions-out /tmp/vwb.actions.sh --quiet`
Result: PASS — exit 0; `grep -c "Ready to start" /tmp/vwb.html` = 1.
```
workboard: 9 repos · 27 open specs · 114 open tasks · 6 active sessions · 5 need attention → /tmp/vwb.html
EXIT: 0
```
(--actions-out accepted as an unused arg — correct per task 01 scope; the
actions script body is task 02.)

## Criterion 5 — modified files + version bump + mirror identity
Command: `git status --short`, `git diff -- .claude-plugin/plugin.json`,
`diff -q <two workboard.py>`
Result: PASS
```
 M .claude-plugin/plugin.json
 M .claude/skills/workboard/workboard.py
 M antigravity/.agents/skills/workboard/workboard.py
-  "version": "0.7.0",
+  "version": "0.7.1",
BYTE-IDENTICAL
```
Both workboard.py paths modified; plugin.json version 0.7.0 → 0.7.1; the two
workboard.py files are byte-identical (mirror matches).

## Correctness / scope findings
- R1 resolve_dep (:248-278): bare-numeric ⇒ sibling glob; `<slug>/NN` ⇒
  `../<slug>/tasks/NN-*.md`; path forms resolved task-dir-relative, `specs/`-
  rooted also tried against repo_root; satisfied ⇔ Status:done (:281-283);
  unresolvable ⇒ blocked_unresolved with offending id (:314-318). Kiro/
  Antigravity excluded via `kind != "toolkit"` (:297).
- R2 cmd (:322-336): `cd {shlex.quote(repo_path)} && claude "/build {file}"`
  for single ready; `.../drain specs/{slug}"` for ≥2 ready. Matches spec.
- R8 no regression: `git diff --stat` = 172 insertions, 0 deletions on
  workboard.py — purely additive; attention-inbox cmd strings, click-to-copy
  JS, and default --out write are unchanged (no lines removed/modified).
- plugin.json diff is version-bump only. No scope creep detected; all changes
  fall within the task Touch list.

## Standard gates
No `scripts/check.sh` in this repo. The task's own acceptance commands are the
gate; all pass. (evals/lint-ultra-gate.sh not applicable — workboard is not an
ultra-path skill, per SPEC Notes.)
