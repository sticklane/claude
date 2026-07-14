Status: draft
Discovered-from: specs/environment-drift-detection/tasks/04-docs-only-diff-scoping.md
Spec: ../SPEC.md
Blocking: no

# Review whether the local Stop-gate's docs-only skip should exempt .claude/** in this toolkit repo

In this toolkit repo specifically, `.claude/` is the product, not incidental
config — a SKILL.md-only edit classifies as docs-only under the docs-only
diff skip rules, so a local Stop-gate run now skips the full
`scripts/check.sh` (including `evals/lint-ultra-gate.sh`) for a change that
could actually break the ultra-gate lint. This is the intended
`paths-ignore`-style convention applied consistently, not a correctness bug
— but the CI-cost rationale for treating `.claude/**` as docs-only (avoiding
billed runner minutes) doesn't fully transfer to a free local gate. Worth a
human decision on whether `.claude/**` should stay in the docs-only skip set
for this repo's own local Stop hook, or be carved out as product-like.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
