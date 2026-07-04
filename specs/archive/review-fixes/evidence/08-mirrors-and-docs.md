# Verification evidence — Task 08: Mirror and docs fixes

Verified: 2026-07-03, branch `task/08-mirrors-and-docs`, worktree
`/Users/sjaconette/claude/.claude/worktrees/agent-a151ec10c8964e75e`,
HEAD df15e0a (changes unstaged in working tree). Verifier: independent
(did not write this code). All commands run from the repo root.

## Verdict: PASS

## Criterion 1 — evals.md provisions assert.sh

```
grep -qE "cp .*assert|absolute path" antigravity/.agents/workflows/evals.md
```
exit=0 ✓

Diff check: grade step now reads "invoke the scenario's assert.sh by
absolute path from the toolkit repo — the fixture does not contain it —
e.g. `(cd <fixture> && bash <toolkit>/evals/<skill>/<NN-name>/assert.sh)`,
the same shape the Claude Code runner uses." Substantive fix, not
keyword-stuffing.

## Criterion 2 — build.md unattended exception + verdict, no "restart fresh"

```
grep -q "unless launched unattended" antigravity/.agents/workflows/build.md \
  && ! grep -q "restart fresh" antigravity/.agents/workflows/build.md \
  && grep -qi "verdict" antigravity/.agents/workflows/build.md
```
exit=0 ✓

Diff check: step 2 adds "unless launched unattended by a workflow, in
which case plan as a comment block and proceed"; step 4 now ends with a
verdict — DONE (all acceptance passing), DEFERRED (a question a human
must answer), or BLOCKED (stuck after the fix attempts) — replacing
"restart fresh".

## Criterion 3 — external-playbooks ranking attribution

```
grep -q "drain ranks the survivors mechanically" docs/external-playbooks.md \
  && ! grep -q "verifier ranks the survivors" docs/external-playbooks.md
```
exit=0 ✓

Line ~48 now reads "drain ranks the survivors mechanically."

## Criterion 4 — README Option C copies rules/ and caveat names both rules

```
grep -q "agentic-toolkit/.claude/rules" README.md \
  && sed -n '/Option C/,/Option D/p' README.md | grep -q "untrusted-data"
```
exit=0 ✓

Diff check: Option C block adds `~/.claude/rules` to mkdir and
`cp -r ~/agentic-toolkit/.claude/rules/* ~/.claude/rules/`; caveat now
names both token-discipline and untrusted-data and says to fold both
into `~/.claude/CLAUDE.md` for global use.

## Criterion 5 — drain-tournament SPEC grep fixed (PATH DRIFT NOTED)

The task file's literal path `specs/drain-tournament/SPEC.md` no longer
exists — the spec was archived to `specs/archive/drain-tournament/SPEC.md`
in commit 7504280, before this task ran. Per caller direction, the
criterion was run against the archived path; the literal-path failure is
expected path drift, not an implementation failure.

Literal path (expected fail, file absent):
```
! grep -qF '\-t1\|t1' specs/drain-tournament/SPEC.md \
  && grep -qF -- "-t1" specs/drain-tournament/SPEC.md
```
exit=2 (grep: specs/drain-tournament/SPEC.md: No such file or directory)

Archived path:
```
! grep -qF '\-t1\|t1' specs/archive/drain-tournament/SPEC.md \
  && grep -qF -- "-t1" specs/archive/drain-tournament/SPEC.md
```
exit=0 ✓

Diff check: SPEC line ~99 R6 criterion now uses
`grep -qF -- "-t1" antigravity/.agents/workflows/drain.md` in place of
the broken-escape `grep -q "\-t1\|t1"`.

Sanity check (replaced grep still validates tournament naming):
```
grep -qF -- "-t1" antigravity/.agents/workflows/drain.md
```
exit=0 ✓

## Standard gates

No package.json/Makefile. Repo test scripts all pass:

- `bash tests/test_hook_templates.sh` → exit=0, "pass: 77, fail: 0"
- `bash tests/test_install_gates.sh` → exit=0, "pass: 156 fail: 0"
- `bash tests/test_sync_skills.sh` → exit=0, "passed: 24, failed: 0"

No `.claude/skills/` files changed, so the /evals-before-skill-commit
convention does not apply.

## Scope creep

`git diff main --stat`:
```
 README.md                              | 11 +++++++----
 antigravity/.agents/workflows/build.md | 11 +++++++----
 antigravity/.agents/workflows/evals.md |  9 ++++++---
 docs/external-playbooks.md             |  2 +-
 specs/archive/drain-tournament/SPEC.md |  2 +-
```
Exactly the five permitted files (Touch list modulo the archive path
drift). No version bumps, formatting sweeps, or unrelated edits. Full
diff reviewed: every hunk maps to a task step; no overfitting to the
acceptance greps.

## Summary

- C1 ✓ evals grade step invokes assert.sh by absolute path
- C2 ✓ build.md unattended exception, verdict, no "restart fresh"
- C3 ✓ external-playbooks credits drain's mechanical ranking
- C4 ✓ README Option C copies rules/, caveat names both rules
- C5 ✓ (at archived path; literal path is pre-existing drift) broken
  escape replaced with `grep -qF -- "-t1"`, sanity grep exit 0

Verdict: PASS
