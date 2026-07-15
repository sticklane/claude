# File-level stamp fixture

This is a multi-line intro paragraph that sits between the H1 and the
file-level Verified stamp, mirroring docs/guides/large-codebase-context.md's
actual shape exactly — the stamp is not immediately adjacent to the H1, so
the file-level fallback must tolerate intervening intro prose.

Verified: 2026-05-15

## A heading relying on the file-level stamp

Body content; this heading has no stamp of its own (its next non-blank line
is prose, not a Verified line), so the checker must fall back to the
file-level preamble stamp.
