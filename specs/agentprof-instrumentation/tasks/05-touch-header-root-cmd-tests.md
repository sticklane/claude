Status: draft
Discovered-from: 01-tool-and-model-durations.md
Spec: ../SPEC.md
Blocking: no

# Root-level cmd tests assert fixture sample counts outside declared Touch

Task 01 needed a one-line edit to `agentprof/cmd_claude_test.go` (a
sample-count assertion, 10→13) even though its `Touch:` header listed only
`agentprof/internal/, agentprof/testdata/`. The edit was mechanically
forced by R7 (tool samples are added "in every transcript," including the
root-level cmd test that runs the fixture). Future task authoring for this
spec (and similar parser-fixture work) should list the root-level test
files that assert fixture sample counts (e.g. `cmd_claude_test.go`) in
`Touch:` rather than leaving them implicit.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
