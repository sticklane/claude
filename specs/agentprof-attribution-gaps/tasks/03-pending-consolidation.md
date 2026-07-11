# Task 03: consolidate tool:(pending) samples

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 02
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R3)
Touch: agentprof/internal/claude/, agentprof/testdata/, specs/agentprof-attribution-gaps/evidence/

<!-- PLAN (delete at close-out):
- API: add Options{ReprimeThreshold, KeepPending} + Stats{Skipped, Pending};
  new CollectWithOptions returns Stats; Collect/CollectWithReprime delegate
  (unchanged signatures so ~40 test callsites stay green).
- toolSamples(modelStack, results, sess, turn, keepPending) -> ([]Sample, int):
  unmatched calls consolidate into ONE tool:(pending) sample w/ pending_calls=N;
  keepPending preserves today's per-call empty-values emission. int = unmatched
  count (the parse-stat).
- collect threads opts + accumulates Stats.Pending from both toolSamples sites.
- Update duration_test TestPendingToolUseHasEmptyValues (asserts REPLACED
  behavior) -> pending_calls:1; add pending_test.go for 3-in-one-turn + keep.
- OUT OF TOUCH: cmd_claude.go --keep-pending flag + stderr parse-stat log
  (cmd_claude.go not in Touch) -> Discovered. Library Option + Stats.Pending
  is the in-scope surfacing; all 3 acceptance criteria are internal/claude only.
- Evidence 14-day window + Agent-tool/TaskOutput real-transcript investigation:
  needs $HOME/.claude outside worktree -> manual-pending with run: command.
-->

## Goal

Unmatched tool_use blocks no longer emit one empty-valued sample each
(`toolSamples`, claude.go:~857): they aggregate into a single per-turn
`tool:(pending)` sample carrying a `pending_calls` value, with a
`--keep-pending` flag preserving today's per-call emission for debugging.
A parse-stat logs the pending count. Investigate whether Agent-tool /
TaskOutput result shapes account for the 8,854-sample volume; fix the
matching if so and record the finding in evidence/.

## Touch

Same file as tasks 01/02 — runs after them (serial chain).

## Steps

1. Failing tests first: fixture with 3 unmatched tool_uses in one turn →
   one `tool:(pending)` sample, `pending_calls: 3`, no empty-values
   samples; with `--keep-pending` → today's behavior.
2. Implement aggregation + flag + parse-stat.
3. Investigate the two suspected unmatched shapes against a real
   transcript; fix matching if confirmed; write
   evidence/03-pending-volume.md with the before/after sample counts on
   the local 14-day window (expect ≥8% total-sample drop).

## Acceptance

- [ ] `cd agentprof && go test ./internal/claude/` → pass including the
  aggregation and keep-pending fixtures
- [ ] evidence/03-pending-volume.md records before/after total sample
  counts on the local window showing empty-values pending samples = 0 and
  ≥8% total drop (or documents why the volume was legitimate)
- [ ] `bash agentprof/scripts/check.sh` → green
