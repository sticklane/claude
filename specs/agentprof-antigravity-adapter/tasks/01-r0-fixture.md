# Task 01: R0 fixture — labeled Antigravity `.db` (human-gated)

Status: blocked
Unblock: ask: Please run one short, real Antigravity session with a hand-counted prompt/response pair (know in advance roughly how many prompt tokens and completion tokens you sent/received), using the "Gemini 3.5 Flash (Medium)" model if Antigravity's model picker lets you select it (this is the only display string Task 03's pricing table maps — using it means Task 04's cost_microusd assertion has a rate row to hit; if the session ends up on a different model, that's fine too, just note the exact field-21 display string you observed in the README so a follow-up rate row can be added to Task 03 before Task 04 needs it), then commit the resulting UNMODIFIED `.db` file to `agentprof/internal/antigravity/testdata/conversations/<cascade_id>.db` (find `<cascade_id>` as the `.db`'s own basename under `~/.gemini/antigravity-cli/conversations/`), plus a short `agentprof/internal/antigravity/testdata/README.md` recording the hand-counted ground truth (approx prompt tokens, approx completion tokens, the exact model display string observed, and the wall-clock time of the session) so a later task can confirm which `gen_metadata` field-4 sub-field is which. Reply here once both files are committed.
Priority: P0
Budget: 4 turns
Spec: ../SPEC.md (R0; blocks R2 and all Values-emitting code in Solution item 2)
Touch: agentprof/internal/antigravity/testdata/conversations/*.db, agentprof/internal/antigravity/testdata/README.md

## Goal

A real, committed, unmodified Antigravity conversation `.db` file exists at
`agentprof/internal/antigravity/testdata/conversations/<cascade_id>.db`,
with a README recording the hand-counted ground truth needed to confirm
which `gen_metadata` field-4 sub-field is prompt tokens, which is
completion tokens, and which (if any) is a cache-read count. This is the
single human-gated prerequisite the rest of the spec depends on (Task 04's
token mapping, and the corrupted-copy fixture Task 04 also needs, both
build on this file existing first).

## Touch

Only the testdata fixture and its README. No Go code changes — this task
produces data, not logic. Do not write the field-mapping or the Go tests
that consume the fixture; that belongs to Task 04 once the mapping is
confirmed.

## Steps

This step is NOT executable from spec text alone — no `/build` or `/drain`
worker may attempt it unattended (per R0 and
docs/memory/unattended-worker-tool-limits.md). It requires a human to:

1. Run one short, real Antigravity session, counting (approximately) the
   prompt tokens sent and completion tokens received (e.g. paste a short,
   known prompt and note the response length).
2. Locate the resulting `.db` file under
   `~/.gemini/antigravity-cli/conversations/<cascade_id>.db`.
3. Copy it, unmodified, to
   `agentprof/internal/antigravity/testdata/conversations/<cascade_id>.db`.
4. Write `agentprof/internal/antigravity/testdata/README.md` recording:
   the cascade_id / filename, approximate prompt/completion token counts,
   the model used, and the date the fixture was captured.
5. Commit both files.
6. Reply on this task (or update its Status) once done so Task 04 can
   start.

## Acceptance

- [ ] `test -f agentprof/internal/antigravity/testdata/conversations/*.db` → a real SQLite file exists (verify with `file agentprof/internal/antigravity/testdata/conversations/*.db` reporting "SQLite 3.x database")
- [ ] `test -f agentprof/internal/antigravity/testdata/README.md` → README exists and states approximate prompt/completion token counts and the model used
- [ ] `git log --oneline -- agentprof/internal/antigravity/testdata/` → shows a commit adding both files, unmodified (no extracted-row JSON, no re-encoding)
