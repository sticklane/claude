# Verification: task 09 (task/09-r3-sample-drop-remeasure)

Verdict: PASS

## Criterion 1 — evidence/09-r3-remeasure.md records re-measured numbers

Command: `cat specs/agentprof-attribution-gaps/evidence/09-r3-remeasure.md`
Evidence: File exists, contains reproduction commands (go build both
binaries, `agentprof claude --days 14`, wc -l / grep -c counts) and a table:
b4971fe 131,521 total / 11,663 empty pending; current 131,519 total / 0
empty pending (4 with `pending_calls`). Recomputed independently:
8,854/131,521... actually 11,663/131,521 = 8.868% (matches stated 8.87%);
total drop (131,521-131,519)/131,521 = 0.0015% (matches stated figure);
non-pending diff 131,515-119,858 = 11,657 (matches stated re-attribution
count). Numbers are internally consistent. PASS.

## Criterion 2 — R3 passes as written OR formally amended with maintainer decision

Command: `sed -n '84,103p;134,150p' specs/agentprof-attribution-gaps/SPEC.md`
Evidence: R3 requirement (line 84-90) retains original text unchanged, with
an appended "Maintainer decision 2026-07-13 (task 09)" block (lines 91-103)
that explicitly strikes the ≥8%-drop clause, cites evidence/09-r3-remeasure.md,
gives the actual 0.0015% figure and diagnosis, and states empty-values=0
stands. The R3 acceptance-criterion bullet (lines 142-149) is likewise
amended in place: keeps the empty-values=0 check, appends "The original
... clause is STRUCK by maintainer decision 2026-07-13 (task 09)" citing the
same evidence file. PASS.

## Criterion 3 — go test ./... and check.sh green

Commands:

- `cd agentprof && go test ./...` → all packages `ok` (15 packages, cached
  and fresh both green).
- `bash agentprof/scripts/check.sh` → `check: format-check ok`,
  `check: lint ok`, `check: tests ok`.
  PASS. No parser source changed (confirmed below), consistent with "unchanged
  if no parser fix was needed."

## Scope / diff check

`git diff 2a4ca72 --stat`: only 3 files changed, all `.md`:
`specs/agentprof-attribution-gaps/SPEC.md`,
`specs/agentprof-attribution-gaps/evidence/09-r3-remeasure.md`,
`specs/agentprof-attribution-gaps/tasks/09-r3-sample-drop-remeasure.md`.
No `agentprof/internal/claude/` (or any other source) file touched — matches
Touch list and the "no parser change made" claim.

## Task-file append-only check

`git diff 2a4ca72 -- specs/agentprof-attribution-gaps/tasks/09-r3-sample-drop-remeasure.md`:
only the Status line (in-progress → done) and the three acceptance
checkboxes (unchecked → checked with evidence-citation lines appended).
Goal/Steps/Touch/Budget and criterion text are unchanged. Compliant with
the append-only worker contract.

## Findings

None. No scope creep, no overfitting (the diagnosis is a genuine mechanism
explanation — result-matching re-attributes rather than eliminates pending
samples — not a special-cased fudge of the exact measured numbers), gates
green, evidence self-consistent.
