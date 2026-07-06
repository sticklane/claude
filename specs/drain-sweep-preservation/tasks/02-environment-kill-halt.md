# Task 02: Environment-kill routing + run-wide halt (R2)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01
Priority: P0
Budget: 6 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md

## Goal

reference.md gains an "Environment kill" subsection (near the "Sweep-race
BLOCKED verdict" note) and SKILL.md step 3 cites it next to the sweep-race
routing. The subsection covers, per SPEC R2: the drain-side detection signal
(the harness failure notification's termination-cause text, or an API error
drain's own session hits, naming an account-wide condition — usage/weekly
limit, auth/billing failure, persistent 429/5xx surviving harness retries;
one agent erroring while others proceed is NOT an environment kill); routing
(never counts toward slot machine or tournament; the stale-lock grace window
does not apply — the death signal is definitive); and the run-wide halt
(sweep EVERY currently-live run drain owns with task 01's R1-preserving
procedure, write each `## Progress` entry stating "environment kill, does not
count as an attempt", flip each to `pending`, commit and push, then halt: no
further dispatch, no slot-machine relaunch, no baton self-relaunch; report
names the reset time when the error carries one; foreign-owned tasks per any
committed partition/owner record are left alone — absent any such record,
every live run is drain's own and is swept).

## Touch

Only the two drain skill files. The R1 sweep language this section cites is
task 01's — depend on it, don't restate the snapshot mechanics beyond a
citation. No worker-prompt edits (task 03), no version bump (task 03).

## Steps

1. Confirm task 01's amended rescue procedure is present (this section cites
   it as "the R1-preserving sweep" / "the rescue procedure").
2. Write the "Environment kill" subsection in reference.md with the three
   parts above; include the literal phrases "account-wide", "grace window
   does not apply" (or "window does not apply"), and "no baton self-relaunch".
3. Add the SKILL.md step 3 citation line next to the sweep-race BLOCKED
   routing, using the phrase "environment kill".
4. Run the acceptance commands from the repo root.

## Acceptance

- [ ] `grep -qi 'environment kill' .claude/skills/drain/reference.md && grep -qi 'environment kill' .claude/skills/drain/SKILL.md` → both match
- [ ] `grep -qi 'account-wide' .claude/skills/drain/reference.md` → match
- [ ] `grep -Eqi 'grace window does not apply|window does not apply' .claude/skills/drain/reference.md` → match
- [ ] `grep -qi 'no baton self-relaunch' .claude/skills/drain/reference.md` → match
- [ ] `claude plugin validate .` → green
- [ ] `./specs/status.sh` → parses, no errors
