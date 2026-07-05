# Verification: 01-owner-protocol-test

Verdict: PASS

Base commit: c710adcbaa4d7a380ead79ae88e072e559cd60c6
Branch: task/01-owner-protocol-test
File under test: tests/test_drain_owner_protocol.sh (staged `A`, not yet committed)

## Acceptance criteria (task file)

1. `bash tests/test_drain_owner_protocol.sh` → exit 0, names all five cases PASS
   ```
   PASS: (a) CAS flip
   PASS: (b) owner lifecycle
   PASS: (c) path-scoped commit
   PASS: (d) losing claim
   PASS: (e) baton adoption predicate
   pass: 13 fail: 0
   EXIT:0
   ```
   Result: PASS.

2. `grep -c "Run-token" tests/test_drain_owner_protocol.sh` → ≥ 2
   Result: `18`. PASS.

3. `for t in tests/test_*.sh; do bash "$t" || exit 1; done` → exit 0
   Result: all suites in the repo ran (owner-protocol, plus siblings: 55/0,
   14/0, 13/0, 77/0, 159/0, 9/0, workboard checks, etc.), overall
   `SWEEP EXIT:0`. PASS.

4. `git diff --name-only main` → only `tests/test_drain_owner_protocol.sh`
   (plus task file, not yet edited per the caller's note)
   Result:
   ```
   tests/test_drain_owner_protocol.sh
   ```
   Only the new test file. `git status --short` shows `A  tests/test_drain_owner_protocol.sh`
   (staged, not committed — see Findings). PASS on scope; NOTE below on
   commit state.

## Independent judgment of the five cases (read + mutation-tested)

Read `tests/test_drain_owner_protocol.sh` in full and cross-checked each
case's letter claim against SPEC.md R9 and the DRAIN-OWNER.md format
paragraph. To rule out vacuous/tautological assertions, mutated the live
(uncommitted) file to break the specific behavior each case claims to
prove, confirmed the case then FAILs, then restored the original file
byte-for-byte from a copy taken before mutation (never used `git
checkout`/`git restore`, since the file isn't committed and that would
have destroyed it). Restoration verified via `diff` (no output = identical)
and a final green re-run (13/0) before finishing.

- **(a) CAS flip** — commits a seed task, then simulates a *foreign*
  writer flipping `Status: pending` → `Status: in-progress` and
  committing. It then re-reads the file and greps for the literal
  `^Status: pending$` line to represent "would an exact-match CAS edit
  precondition still succeed?" and asserts it would NOT (0), plus asserts
  exactly one `^Status: in-progress$` line exists. Mutation test: with
  the foreign-flip block removed, the case correctly FAILs (`expected:
  '0', got: '1'`) — proving the assertion is checking real post-commit
  file content, not scaffolding. Faithful to R9(a).

- **(b) owner lifecycle** — claim commit (Generation: 1), in-place baton
  Generation update + commit (Generation: 2), then `git rm` + commit for
  release, asserting the file is gone from disk and absent at `HEAD` via
  `git show HEAD:...` (non-zero exit). Straightforward; matches R9(b)
  and the pinned format. Not mutation-tested (low risk of vacuity —
  asserts real file-existence/git-show state at each of three real
  commits) but plainly non-tautological.

- **(c) path-scoped commit** — seeds a repo with a task file and
  `other.txt`, then modifies both, stages only `other.txt` (the
  "foreign" file), and creates the queue-state commit as
  `git commit -m ... -- specs/demo/tasks/01-demo.md` (a real, if
  slightly different, git-native mechanism for path-scoping vs.
  add-then-commit, but a valid implementation of "commit limited to
  those paths"). Asserts `git show --name-only HEAD` names only the
  task file, and that `other.txt`'s staged change is still uncommitted
  (`git diff --cached` non-empty). Mutation test: removing the `--
  <path>` pathspec (bare `git commit`) makes the case FAIL as expected
  (`expected: 'specs/demo/tasks/01-demo.md', got: 'other.txt'` — i.e.
  the foreign file rode along). Confirms the case truly exercises git's
  path-scoping mechanics rather than the test's own scaffolding.

- **(d) losing claim** — two sequential claim commits with distinct
  random (`openssl rand -hex 8`) tokens; asserts `HEAD` (via
  `git show HEAD:...`) carries only writer B's token and exactly one
  `Run-token:` line, and that writer A's token string is absent from the
  live file. Real git commits, real distinct random tokens — not
  hardcoded, so equality/inequality isn't tautological. Matches R9(d).

- **(e) baton adoption predicate** — writes three real files (owner +
  matching-token baton + independently-random mismatched-token baton)
  and implements the predicate itself, `adopt() { [ "$(grep
  '^Run-token:' "$1")" = "$(grep '^Run-token:' "$2")" ]; }` — an exact
  reimplementation of the "documented one-liner" R2 describes (compare
  the two `Run-token:` lines verbatim). Asserts match passes, mismatch
  (independently random token) fails. This is inherently a local
  reimplementation rather than a call into the actual (not-yet-written,
  task 02/03-owned) skill text — expected and explicitly licensed by the
  task file ("must not depend on skill text existing... stays green
  regardless of task 02-04 ordering") and by R9(e)'s own framing. It
  cannot catch a *future* bug in the real skill's implementation of the
  predicate, but that is by design for this task, not a verification gap
  in it.

No case was found to be tautological or scaffolding-only; two
representative cases (a, c) were mutation-tested and both correctly
flipped to FAIL, giving confidence the other three (whose failure modes
are structurally identical file/commit-state assertions) are equally
real.

## Gate / diff scope

- `git diff --name-only main` → `tests/test_drain_owner_protocol.sh`
  only. No skill files, no other tests, no gate wiring touched — matches
  the task's Touch list.
- Full `for t in tests/test_*.sh` sweep green (see criterion 3 above).

## Findings

- **Uncommitted work**: `git status --short` shows
  `A  tests/test_drain_owner_protocol.sh` — the file is staged but not
  committed. The task's Steps section step 3 says "commit" once all
  five cases are green and the sweep passes; that hasn't happened yet.
  This doesn't fail any of the four written acceptance criteria (none
  of them check commit state), but it is a gap against the task's own
  documented plan and the repo's commit-discipline rules
  (`.claude/rules/quality-discipline.md`: "never leave finished work
  uncommitted"). Flagging for the caller to decide whether to commit
  before marking the task DONE.
- No scope creep found: diff against `main` touches only the one file
  in the Touch list.
- Task file (`specs/multi-session-coordination/tasks/01-owner-protocol-test.md`)
  is unedited so far (Status still `in-progress`, no boxes ticked) —
  consistent with the caller's note that they have not yet updated it.
