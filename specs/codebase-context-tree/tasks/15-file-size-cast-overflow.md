Status: draft
Discovered-from: specs/codebase-context-tree/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# File-size cast overflow in staleness detection

A u64->i64->u64 round-trip for file sizes in context-tree/src/index/mod.rs:291
and context-tree/src/sync/mod.rs:312 overflows above i64::MAX (~9.2
exabytes), which would corrupt size-based staleness detection. Practically
unreachable for any real file, so left unfixed by the spec-completion
review — flagged for a human to judge whether a defensive fix is worth it.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
