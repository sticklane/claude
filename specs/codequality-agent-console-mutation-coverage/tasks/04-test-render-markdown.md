# Task 04: Test render_markdown's structured list/header parsing

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (Approach step 4; Acceptance criterion 4)
Touch: agent-console/tests/test_render_markdown.py

## Goal

`agent-console.py`'s `render_markdown()` — which parses list/header
markdown into HTML and runs on every `/spec/` GET — gains test coverage
that asserts structure, not exact strings, and includes a real mutation
kill: a test that fails if heading-level parsing is stubbed to always
emit `<h1>`.

## Touch

New file only: `agent-console/tests/test_render_markdown.py`. Do not edit
`agent-console/agent-console.py` or any sibling test file another task in
this spec touches.

## Steps

1. Read `render_markdown()` in `agent-console/agent-console.py` (find it
   by name), specifically the heading-level parsing (the line computing
   `level` from the heading match, e.g. `level = len(heading.group(1))`
   or equivalent — find the actual current form, do not assume a
   snapshot).
2. Write the failing tests first (`unittest.TestCase` subclasses): build a
   fixture markdown document exercising headers of at least two different
   levels (e.g. `#`/`##`/`###`), an unordered list, and a fenced code
   block. Parse it with `render_markdown()` and assert on structure (e.g.
   the parsed HTML contains the right heading tags at the right levels,
   list items are present, code fence content is preserved) — not exact
   full-string HTML comparison.
3. Include a mutation-kill test: manually stub the heading-level
   computation to always emit `<h1>` regardless of the source heading's
   level (e.g. temporarily hardcode `level = 1` in place of the real
   computation) and confirm your header-level-assertion test now fails;
   restore the real code and confirm it passes again. Record this
   red-then-green evidence in your final message — do not leave the stub
   applied.
4. Run `bash agent-console/scripts/check.sh` and confirm it exits 0 with
   the new tests included.
5. Commit.

## Acceptance

- [ ] `grep -rln "render_markdown" agent-console/tests/` is non-empty
- [ ] The new heading-level test fails when heading-level parsing is manually stubbed to always emit `<h1>` (demonstrate this red-first, then restore and confirm green — record the evidence in your final message)
- [ ] Every new test is a `unittest.TestCase` subclass: `grep -c "unittest.TestCase" agent-console/tests/test_render_markdown.py` → at least 1
- [ ] `bash agent-console/scripts/check.sh` → exit 0
- [ ] New tests assert on parsed structure (heading levels, list items, code fence content) — not full-string HTML comparison
