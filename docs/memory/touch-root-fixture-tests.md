# Tasks that change parser fixtures must Touch the root-level cmd tests too

When to read: authoring (`/breakdown`) or reviewing a task that changes a
parser's sample/fixture output, or debugging a worker mechanically forced to
edit a file outside its declared `Touch:`.

## The incident

Task 01 of `agentprof-instrumentation` declared
`Touch: agentprof/internal/, agentprof/testdata/`. But adding tool-call
samples (R7 forces a tool sample into every transcript) changed the parsed
sample count for the shared root fixture, so
`agentprof/cmd_claude_test.go`'s sample-count assertion (`10 → 13`) had to be
updated to keep `go test ./...` green. That file sits at the package root,
outside both declared `Touch:` paths — the worker was mechanically forced out
of its declared scope to land a passing task.

## The rule

A task that changes what a parser emits (new sample types, changed counts,
new value keys) must list the root-level test files that assert fixture
**sample counts** in `Touch:` — not just the parser package and its
`testdata/`. The count assertions live wherever the CLI's end-to-end fixture
test lives, typically a root-level `*_test.go` such as
`agentprof/cmd_claude_test.go`, not under the parser's `internal/` package.
Leaving them implicit forces the worker outside its declared `Touch:` to keep
the suite green.

## How to author around it

- Before writing `Touch:`, grep the fixture's expected sample-count
  assertions (`grep -rn 'len(.*[Ss]ample' agentprof`) and add every file that
  will need its count bumped.
- If a count-asserting file genuinely must stay out of `Touch:`, give the
  task an explicit note (as task 01's `## Discovered` did) so the drift is
  visible rather than a silent forced edit.
