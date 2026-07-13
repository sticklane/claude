# Verification: Task 03 — worker-commits-and-bump

Verdict: PASS

## Acceptance criteria

1. `[ "$(grep -c 'at each completed TDD step' .claude/skills/drain/reference.md)" -eq 2 ]`
   - Exit: 0 (true). Grep found the fragment at reference.md:253 (Worker prompt)
     and reference.md:499 (Headless fallback `claude -p "..."` string).

2. `[ "$(grep -c 'before spawning any verifier' .claude/skills/drain/reference.md)" -eq 1 ]`
   - Exit: 0 (true). Single occurrence at reference.md:255, inside the Worker
     prompt blockquote only:
     > Always commit the full implementation before spawning any verifier or
     > review pass — never hold the full implementation uncommitted at
     > close-out.
   - Confirmed absent from the Headless fallback prompt (lines 493-518):
     that block contains only "...commit code to the branch you are on at
     each completed TDD step (test → feat → refactor); do not push." with
     no verifier-sentence.

3. `grep -q '"version"' .claude-plugin/plugin.json && ! grep -q '"version": "0.8.8"' .claude-plugin/plugin.json`
   - Exit: 0 (true). Current value: `"version": "0.8.15"`. Confirmed via
     `git status --short` that plugin.json is one of only two files modified
     since base commit dc3afca (drain: task 03 in-progress), consistent with
     "0.8.15 = one patch above pre-task 0.8.14."

4. `claude plugin validate .`
   - Exit: 0.
   - Output: "Validating marketplace manifest: .../\n✔ Validation passed"

5. `./specs/status.sh`
   - Exit: 0. Parsed all 41 tasks across 10 specs with no errors; task 03
     itself listed as `in-progress` (Status line unchanged by worker, per
     caller's note that this may be normal at verification time).

## Substantive Goal inspection (.claude/skills/drain/reference.md)

- Worker prompt blockquote (lines 245-272, header "## Worker prompt
  (verbatim, fill the <>)" at line 232) contains BOTH:
  - "at each completed TDD step" (line 253)
  - "before spawning any verifier" (line 255), in a sentence about
    committing the implementation before any verifier/review pass — matches
    intent exactly.
- Headless fallback prompt (the `claude -p "..."` string starting line 496)
  contains "at each completed TDD step" (line 499) and does NOT contain
  "before spawning any verifier" — confirmed by the single-occurrence grep
  above and by reading lines 490-519 directly.
- plugin.json version confirmed as `0.8.15` (one patch above stated pre-task
  0.8.14).

## Append-only task-file check

Command: `git diff dc3afca2e52625b4630cf54c2c8d6a7ae4732453 -- specs/`
Output: empty (no diff at all under specs/ relative to base).

`git diff dc3afca2e52625b4630cf54c2c8d6a7ae4732453 --stat` (whole tree) shows
only:
```
 .claude-plugin/plugin.json        | 2 +-
 .claude/skills/drain/reference.md | 9 ++++++++-
 2 files changed, 9 insertions(+), 2 deletions(-)
```
No task file (any spec) has been touched since base — satisfies the
append-only requirement trivially (base commit dc3afca itself is titled
"drain: task 03 in-progress", i.e. already reflects the in-progress Status
line; no further task-file edits exist to check).

## Scope-creep check

Modified files (via `git status --short` / diff-stat) are exactly:
- `.claude-plugin/plugin.json` (in Touch list)
- `.claude/skills/drain/reference.md` (in Touch list)

`README.md` (also in Touch list) was left untouched. Verified this is
consistent with repo convention: `git log --oneline -- README.md` shows
README updates are NOT paired with every plugin.json version bump (e.g.
bump commits 96a34cc, 253dd17, 3b93694, 60fddcf, 604b272, 78a06cc all lack
a corresponding README change), so skipping README here is not a criterion
violation — matches the task's own guidance to "add a README note only if
the repo's release convention... shows one."

No edits found to the rescue procedure (task 01) or Environment kill
subsection (task 02) within reference.md diff region; no SKILL.md changes.
No antigravity mirror file was touched — outside this task's Touch list,
and not flagged as scope creep since nothing extra was touched, only a
possible open question for the spec closer (not this task's job per its
Touch list, which the task's own text explicitly enumerates without an
antigravity entry).

## Verdict

PASS — all 5 mechanical acceptance commands pass, the substantive intent
(Worker prompt has both fragments, Headless fallback has only the TDD-step
fragment, version bumped 0.8.14→0.8.15) is verified by direct inspection,
the append-only task-file constraint holds (no specs/ diff at all vs base),
and no scope creep beyond the Touch list was found.
