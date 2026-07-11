# Task 06: frame denylist scrub at sample-emit time

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 04, 05
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R6)
Touch: agentprof/internal/claude/, agentprof/cmd_claude.go, agentprof/testdata/, agentprof/README.md

<!-- PLAN (worker, task/06-frame-denylist):
Touch excludes internal/output/, so the rewrite pass lives in internal/claude/
and is wired in cmd_claude.go before output.Write. All enumerated frames
(project, turn, skill, stage, main, model, role, agent) are Sample.Stack
elements (claude.go:418-452); schema.MarshalLine emits Stack — scrubbing Stack
covers every enumerated frame.
Files:
1. internal/claude/denylist.go — LoadDenylist(path) ([]string,error): one
   substring per line, trim, skip blanks; missing file -> nil,nil. ScrubFrames(
   samples, denied): any Stack frame containing a denied substring -> "(redacted)"
   (marker with parens, distinct from scrub.go's [redacted]).
2. internal/claude/denylist_test.go — RED first: skill-frame redaction +
   substring-absent-in-JSONL; project-frame redaction; empty/nil denylist ->
   unchanged; LoadDenylist blank-line skip + missing-file. Invented name
   skill:zz-test-private.
3. cmd_claude.go — add --frame-denylist flag (default ~/.config/agentprof/
   frame-denylist via defaultFrameDenylist()); load once, ScrubFrames after
   Collect (covers merge/summary/unlinked) and again after nameTurns before the
   direct output.Write (covers renamed turn frames).
4. README.md — denylist mechanism + pinned-evidence repo rule.
-->

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

- [ ] `cd agentprof && go test ./internal/claude/` → pass including the
  skill-frame and project-frame redaction fixtures and the
  substring-absent assertion
- [ ] `grep -qi 'denylist' agentprof/README.md` → hits (MANUAL: includes
  the pinned-evidence repo rule)
- [ ] `bash agentprof/scripts/check.sh` → green
