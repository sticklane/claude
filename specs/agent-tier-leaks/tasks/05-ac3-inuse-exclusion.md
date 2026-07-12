Status: pending
Discovered-from: specs/agent-tier-leaks/tasks/01-verifier-leak-trace.md
Spec: ../SPEC.md
Blocking: no
Promotion-ready: true
Promoted-by-run: e83f34f07094a4fa
Depends on: none
Budget: 2 turns
Touch: specs/agent-tier-leaks/SPEC.md

# Task 05: Record the .in_use PID-marker false positive on AC3's plugin-cache check

## Goal

Add a note to `specs/agent-tier-leaks/SPEC.md` documenting that AC3's
plugin-cache-untouched mtime check has a known false positive: transient
`.in_use/<pid>` runtime markers written by any live `claude` process can make
the mtime-based count read greater than zero even when no cached content
changed. The note states the fix a future reader should apply — filtering
those markers out with `-not -path '*/.in_use/*'` — so the criterion is not
mistaken for a real regression.

## Acceptance

- [ ] `grep -q 'in_use' specs/agent-tier-leaks/SPEC.md` succeeds (the note is
  present in the spec).
- [ ] `grep -q "not -path '\*/.in_use" specs/agent-tier-leaks/SPEC.md`
  succeeds (the note carries the exclusion flag as guidance).
- [ ] MANUAL: the note sits with AC3 / task-01's plugin-cache criterion so a
  reader of that check finds it (reviewer confirms placement).
