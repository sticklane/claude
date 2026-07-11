# Task 03: Gemini pricing table (`PriceGemini`)

Status: pending
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (Solution item 3; R3)
Touch: agentprof/internal/pricing/gemini_table.go, agentprof/internal/pricing/gemini_table_test.go, agentprof/internal/pricing/testdata/

## Goal

`internal/pricing` gains a `PriceGemini(displayName string, usage Usage)
(int64, bool)` sibling to the existing `Price`, keyed by an explicit map
from known Gemini model display strings (currently just
`"Gemini 3.5 Flash (Medium)"`, the only one observed in this spec's
fixture inspection) to a rate row sourced from Google's published Gemini
API pricing. An unmapped display string returns `priced=false` with no
cost value — same convention as `Price`. This is independent of the
Antigravity `.db` fixture (Task 01) and the protobuf walker (Task 02): it
only needs the display string, already confirmed in SPEC.md's text, and a
committed pricing-fixture of its own.

## Touch

New files only, under `internal/pricing/`. Do not modify
`internal/pricing/table.go` or `internal/pricing/pricing.go`'s existing
`Price`/Claude rate table (Out of scope) — `PriceGemini` is a new sibling
function, not a change to the existing one. Final package placement
(`internal/pricing/gemini_table.go` vs. a new `internal/geministypes`
package) is this task's call per SPEC.md Solution item 3 ("decided in
review, not gating this spec") — default to `internal/pricing` unless
review says otherwise, since it's the smaller diff.

## Steps

1. Write the failing tests first in a new `gemini_table_test.go`:
   - `PriceGemini("Gemini 3.5 Flash (Medium)", usage)` with known token
     counts returns the expected `cost_microusd` and `priced=true`,
     computed against the committed rate figures (Google's published
     Gemini API pricing for that model, converted to microUSD-per-token
     the same way `internal/pricing/table.go` already converts its rates —
     read `table.go`'s existing conversion for the exact microUSD
     arithmetic convention to mirror).
   - An unmapped display string (e.g. `"Gemini Unknown Model"`) returns
     `priced=false` and no cost value.
2. Confirm the tests fail (no implementation yet).
3. Commit the sourced rate figures as fixture data under
   `internal/pricing/testdata/` (e.g. a small JSON or Go-literal table
   documenting the source/date of Google's published price used, so the
   test is hermetic and not dependent on a live pricing page).
4. Implement `PriceGemini` in `gemini_table.go`, keyed by the exact display
   strings in the map (starting with the one confirmed string), mirroring
   `Price`'s prefix-match-vs-explicit-map shape as closely as makes sense
   for a small, hand-maintained list (an explicit map is fine here — Solution
   item 3 doesn't require prefix matching).
5. Get tests green.

## Acceptance

- [ ] `cd agentprof && go test ./internal/pricing/... -v` → passes, including the mapped `"Gemini 3.5 Flash (Medium)"` case and the unmapped-string `priced=false` case
- [ ] `cd agentprof && go build ./...` → succeeds
- [ ] `git show HEAD:internal/pricing/testdata/` (or equivalent) → shows the committed rate fixture with its pricing source/date noted
