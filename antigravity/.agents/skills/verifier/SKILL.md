---
name: verifier
description: Independent verification discipline for finished work. Use after implementing a task to check the result against its written acceptance criteria, or when asked to verify, validate, or confirm work is actually done.
---

Verify finished work against its written acceptance criteria without
trusting the implementer's claims — including "verified ✓" notes in the
task file. Best run in a FRESH Agent Manager conversation so there's no
memory of the implementation to rationalize shortcuts.

Process:
1. Read the acceptance criteria. If one isn't concretely checkable, report
   that as a finding — don't improvise a weaker substitute silently.
2. For each criterion, EXERCISE it: run the command, run the tests, hit the
   endpoint. Reading the code and concluding "looks right" doesn't count.
3. Run the project's standard gates (build, lint, tests — see AGENTS.md).
4. Check the diff for scope creep: changes not required by any criterion.
   The task file's Touch list is binding — convention-driven edits outside
   it (version bumps, formatting sweeps) are scope creep even when a repo
   rule motivates them; report the convention instead of accepting the
   edit.
5. Check for overfitting to the checks: were test files modified after the
   failing tests were committed? Does the implementation special-case the
   exact test inputs? Gaming the acceptance criteria is a FAIL even if
   every command passes.
6. Append-only task-file check (mechanical): run
   `git diff <base> -- '*/tasks/*.md'` — path-scoped to every spec's tasks/
   dir, so edits to OTHER tasks' files are visible. The base is defined, not
   guessed: the base commit the caller passed, or in a drain/tournament
   worktree the worktree's merge-base with the default branch. Changes must
   appear only in the worker's own task file and only in the allowed set —
   the Status line, checkbox ticks, evidence-citation lines, the plan
   comment block. Anything else — criterion text, another task's file, a
   worker-written `## Progress` section — is an automatic FAIL finding.

Hard tool-call ceiling: ~20, EXEMPTING the acceptance commands themselves from
the count — you must exercise every criterion regardless. If you hit the
ceiling before exercising every criterion, your verdict is `INCOMPLETE` —
never `PASS` — listing the criteria you did not exercise.

Evidence file (caller-directed): when the caller provides an evidence file
path (e.g. `specs/<slug>/evidence/<name>.md`), write the FULL report there,
creating parent directories — verdict line, per-criterion entry with the
exact command and an output tail (last ~10 lines), gate results,
scope-creep findings. A re-verify overwrites the file: latest verdict wins;
stale PASS evidence must not survive a FAIL. When no path is provided,
write nothing — never derive a path yourself.

Output, under a page (the budget applies to this message, not the file):
- Verdict line: `PASS` / `FAIL` / `INCOMPLETE`.
- Per criterion: ✓/✗, the exact command run, one line of evidence (test
  count, observed output). Failures include the actual output.
- Scope-creep or gate failures as separate findings.
- If an evidence file was written, end with a pointer to its path.
Attach the evidence in the walkthrough artifact too — it complements the
committed file, it doesn't replace it.
