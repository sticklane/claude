# Task 06: frame denylist scrub at sample-emit time

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 04, 05
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R6)
Touch: agentprof/internal/claude/, agentprof/cmd_claude.go, agentprof/testdata/, agentprof/README.md

## Goal

If `~/.config/agentprof/frame-denylist` exists (one string per line;
path override via `--frame-denylist`), any frame containing a listed
string is replaced by `(redacted)` — applied to EVERY emitted frame
string (project, turn, skill, agent, role/stage markers, model) at
sample-emit time. Hooking only the existing turn-prompt secret scrub
(`internal/claude/scrub.go`) does NOT satisfy this: skill frames flow
from `normalizeSkillFrame` unscrubbed and are the documented leak vector.
The denylist file itself is never committed. README documents the
mechanism and the repo rule: evidence profiles pinned under specs/ must
be generated with the denylist active.

## Touch

Runs last — after tasks 01–05 settle the emit paths it wraps. The
denylist test fixture must use an invented name (e.g. a fake skill
`skill:zz-test-private`), never any real local skill name.

## Steps

1. Failing tests first: with a denylist listing a substring of a fixture
   SKILL name → the `skill:` frame becomes `(redacted)` and the substring
   appears nowhere in the emitted JSONL; a project-frame match also
   redacts; no denylist file → output unchanged.
2. Implement as a final frame-rewrite pass at emit time; add the flag.
3. README section + pinned-evidence rule.

## Acceptance

- [x] `cd agentprof && go test ./internal/claude/` → pass including the
  skill-frame and project-frame redaction fixtures and the
  substring-absent assertion
  — verifier PASS; denylist_test.go covers skill-frame + project-frame
  redaction and substring-absent-in-JSONL (evidence/06-frame-denylist.md).
- [x] `grep -qi 'denylist' agentprof/README.md` → hits (MANUAL: includes
  the pinned-evidence repo rule)
  — README "Frame denylist" section documents the mechanism and the
  "Pinned-evidence repo rule" (evidence/06-frame-denylist.md).
- [x] `bash agentprof/scripts/check.sh` → green
  — format-check ok, lint ok, tests ok (evidence/06-frame-denylist.md).

## Decisions

- Rewrite-pass location: Touch excludes internal/output/, so the pass lives in
  internal/claude/ (ScrubFrames) and is applied in cmd_claude.go before every
  output.Write. Reverse: move into output.Write if Touch is later widened.
- Redaction marker `(redacted)` (parens) chosen distinct from scrub.go's
  `[redacted]` so the two mechanisms stay separable in output. Reverse: change
  the denylistMarker const.
- Denylist applied at three points (after Collect; after nameTurns; over the
  merged set) so merge/summary/unlinked/renamed-turn paths are all covered; the
  merge-path scrub was added after a pre-commit critic finding that the rolling
  cache re-emitted unscrubbed. Reverse: consolidate if emit paths are unified.
