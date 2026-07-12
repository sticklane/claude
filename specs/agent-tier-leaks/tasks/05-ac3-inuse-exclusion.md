Status: done
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

- [x] `grep -q 'in_use' specs/agent-tier-leaks/SPEC.md` succeeds (the note is
  present in the spec).
  - Evidence: grep → exit 0 (match at SPEC.md ~line 66). Verifier PASS. See evidence/05-ac3-inuse-exclusion.md.
- [x] `grep -q "not -path '\*/.in_use" specs/agent-tier-leaks/SPEC.md`
  succeeds (the note carries the exclusion flag as guidance).
  - Evidence: grep → exit 0 (match at SPEC.md ~line 68). Verifier PASS. See evidence/05-ac3-inuse-exclusion.md.
- [x] MANUAL: the note sits with AC3 / task-01's plugin-cache criterion so a
  reader of that check finds it (reviewer confirms placement).
  - Evidence: note block sits directly under R1's requirement bullet (SPEC.md lines 62-69), labeled "Note (AC3 plugin-cache-untouched false positive)"; accurately describes the mtime scan, the `.in_use/<pid>` false positive, and the `-not -path '*/.in_use/*'` fix. Verifier PASS. See evidence/05-ac3-inuse-exclusion.md.
