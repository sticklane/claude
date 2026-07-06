# Verification: Task 02 — Environment-kill routing + run-wide halt (R2)

Verdict: PASS

Base commit for diff: 75bbea2
Repo: /Users/sjaconette/claude/.claude/worktrees/agent-a5dc0f8fea012c95f

## Acceptance criteria (all 6 run verbatim from repo root)

1. `grep -qi 'environment kill' .claude/skills/drain/reference.md && grep -qi 'environment kill' .claude/skills/drain/SKILL.md`
   → PASS (both matched; "Environment kill." heading in reference.md line 336, "environment kill" phrase in SKILL.md added line)

2. `grep -qi 'account-wide' .claude/skills/drain/reference.md`
   → PASS (matched: "that text names an **account-wide** condition")

3. `grep -Eqi 'grace window does not apply|window does not apply' .claude/skills/drain/reference.md`
   → PASS (matched: "the Stale-lock liveness **grace window does not apply**")

4. `grep -qi 'no baton self-relaunch' .claude/skills/drain/reference.md`
   → PASS (matched: "**no baton self-relaunch**")

5. `claude plugin validate .`
   → PASS, exit 0. Output: "Validating marketplace manifest: .../.claude-plugin/marketplace.json" / "✔ Validation passed"

6. `./specs/status.sh`
   → PASS, exit 0, parsed cleanly. Tail of output:
   ```
   TOTAL
     done: 29
     draft: 7
     in-progress: 1
     pending: 3
     all: 40
   ```

## SPEC R2 three-part content check (manual review of diff)

Read `git diff 75bbea2 -- .claude/skills/drain/reference.md` and
`.claude/skills/drain/SKILL.md`. The new "Environment kill" subsection in
reference.md (inserted right after the "Sweep-race BLOCKED verdict" note,
as required) covers:

(a) **Detection signal** — "Read it from either of two places — the
harness failure notification's termination-cause text for a dispatched
worker, or an API error drain's own session hits directly — but only when
that text names an account-wide condition: a usage or weekly limit
reached, an auth/billing failure, or a persistent 429/5xx that survived
the harness's own retries." Explicitly excludes the non-signal case: "One
agent erroring while its siblings keep running is NOT an environment
kill." — matches spec text closely. PASS.

(b) **Routing** — "An environment kill never counts toward the slot
machine or the tournament threshold (like a sweep race). Unlike a stale
lock, the Stale-lock liveness grace window does not apply — drain does
not wait out the 15-min window before acting, because the death signal is
definitive." PASS.

(c) **Run-wide halt** — "drain sweeps EVERY currently-live run it owns —
each with task 01's R1-preserving rescue-branch procedure above
(the snapshot-before-force-remove sweep; cited, not restated) — then
writes each swept task's `## Progress` entry stating "environment kill,
does not count as an attempt", flips each to `pending`, and commits and
pushes the resets. It then halts: no further dispatch, no slot-machine
relaunch, and no baton self-relaunch. When the underlying error carries a
reset time ... the halt report names it ... Ownership scoping:
foreign-owned tasks named by any committed partition or owner record are
left alone; absent any such record, every live run is drain's own and is
swept." — covers all sub-clauses (progress text, flip to pending,
commit+push, halt w/ no dispatch/no slot-machine/no baton, reset-time
reporting, foreign-owned exclusion). PASS.

Citation check: the subsection explicitly says "task 01's R1-preserving
rescue-branch procedure above ... cited, not restated" — confirms it
defers to task 01's mechanics rather than re-describing the
snapshot-before-force-remove steps. Verified task 01
(`specs/drain-sweep-preservation/tasks/01-*.md`) Status: done, and its
"rescue-branch procedure" text is present in reference.md (lines 61, 196,
211) — the citation target exists. PASS.

SKILL.md step 3 addition: added directly after the existing sweep-race
BLOCKED routing paragraph, reads "A cause naming an account-wide runtime
death (usage/weekly limit, auth/billing, persistent 429/5xx) is instead
an **environment kill**: drain sweeps every live run it owns, resets each
to `pending`, and halts with no relaunch — reference.md's 'Environment
kill' note has the detection signal and run-wide halt." — correctly
placed "next to the sweep-race routing" per the Goal. PASS.

## Touch-scope check

`git diff 75bbea2 --stat`:
```
 .claude/skills/drain/SKILL.md     |  7 ++++++-
 .claude/skills/drain/reference.md | 32 ++++++++++++++++++++++++++++++++
 2 files changed, 38 insertions(+), 1 deletion(-)
```
Only the two files named in Touch: were changed. No worker-prompt edits,
no version bump (both explicitly excluded by the Touch note; both absent).
No other files touched — no scope creep.

## Task-file append-only check

`git diff 75bbea2 --stat -- 'specs/*/tasks/*.md'` → empty output. The
task file `specs/drain-sweep-preservation/tasks/02-environment-kill-halt.md`
itself was NOT modified at all: Status still reads `in-progress` and none
of the 6 acceptance checkboxes are ticked, despite the underlying work
being complete and passing all 6 checks. This is not a violation (nothing
was changed outside the allowed set — the file is simply untouched), but
it does mean the task's own bookkeeping was left undone by the
implementer, contrary to the "verified ✓" expectation implied by the task
lifecycle. Flagging as a minor process finding, not a functional defect.

## Gate / build check

No repo-wide `scripts/check.sh` invoked here beyond the two acceptance
commands (`claude plugin validate .`, `./specs/status.sh`), which are the
gates this task specifies. Both green.

## Scope-creep / overfitting

No test files exist for this prose-only task (SPEC/acceptance are grep
checks against prose, not code). Diff is confined to the two allowed
files, content is substantive (not keyword-stuffed) and consistent with
citing task 01 rather than duplicating it — no overfitting to the exact
grep patterns beyond naturally including the four required literal
phrases.

## Summary

All 6 acceptance commands pass. Content substantively satisfies SPEC R2's
three parts (detection signal, routing, run-wide halt) and correctly cites
rather than restates task 01's rescue procedure. Touch scope honored
exactly. Only finding: task file's own Status/checkbox bookkeeping was
never updated (process nit, not a functional failure).
