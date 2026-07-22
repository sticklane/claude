Status: in-progress
Discovered-from: spec-completion review (2026-07-21)
Spec: ../SPEC.md
Blocking: no

# `suggested_check`'s grep is not fixed-string, so regex-metacharacter symbols mismatch

The suggested bounded-grep command interpolates the raw symbol name as a
`grep` pattern (not `grep -F`), so a symbol containing regex
metacharacters isn't matched literally. The module's own test symbol
`a$b'c` renders as the regex `a$b'c` (`$` anchors end-of-line) and would
never match the literal text it's meant to check; a symbol containing
`(`/`[` could make grep error outright. Shell metacharacters are already
escaped; regex metacharacters are not. Low impact for plain identifiers
(the common case) — left unfixed by the reviewing worker because
plain-grep may be the intended behavior and changing it edits a shipped
acceptance shape.

## Acceptance

<!-- draft: needs runnable criteria before promotion. Likely shape: add
`-F` to the suggested command (or otherwise escape regex metachars) and
a regression test asserting a symbol with `$`/`(`/`[` in it produces a
suggested command that actually matches. -->
