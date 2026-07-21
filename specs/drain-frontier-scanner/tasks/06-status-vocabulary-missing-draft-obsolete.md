Status: draft
Discovered-from: drain inventory (orchestrator, this session, 2026-07-21)
Spec: ../SPEC.md
Blocking: no

# Scanner crashes on any in-scope `Status: draft`/`obsolete` task, breaking whole-queue scans

`drain_frontier.py`'s `_KNOWN_STATUS` vocabulary (drain_frontier.py:33-49)
does not include `"draft"` or `"obsolete"`, even though both are
documented, legitimate task states elsewhere in the toolkit: SKILL.md's
own "Stub intake" section treats `Status: draft` as the standard
discovered-work-stub state, and several specs (mirror-procedure-discipline,
orchestrator-share-audit, shared-viz-renderer, skill-doc-size-guards,
spec-completion-review) carry `Status: obsolete` tasks already closed out.
A present-but-unrecognized value raises `FrontierError` and exits non-zero
(`_STATUS_LINE_RE` parse in `_parse_status`), which aborts the ENTIRE
cross-spec scan — not just the one offending spec — the moment a
no-argument (whole-queue) `/drain` launch includes any spec with a draft
or obsolete task anywhere in scope.

Observed live 2026-07-21: a whole-queue frontier scan
(`python3 .claude/skills/drain/drain_frontier.py specs/*/`) failed with
`specs/agentprof-skill-audit/tasks/05-judge-fake-replies-mode.md:
malformed Status value 'draft'` before producing any output, forcing a
manual per-spec header-read fallback across all 45 specs / 207 task
files instead of the intended one-command scan. Scoping the same scanner
call to only the 3 specs with no draft/obsolete tasks succeeded cleanly,
confirming the vocabulary gap (not a corrupt file) as the cause.

## Acceptance

<!-- draft: needs runnable criteria before promotion. Likely shape: add
"draft" and "obsolete" to _KNOWN_STATUS (both excluded from the
dispatchable set, same as today's non-pending/non-done statuses), add a
regression test with a draft-status and an obsolete-status task file in a
scanner-test fixture spec, and confirm a whole-queue scan across specs/*/
in this repo exits 0. -->
