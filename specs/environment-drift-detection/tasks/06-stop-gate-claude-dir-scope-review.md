Status: done
Depends on: 04
Priority: P3
Budget: 10 turns
Discovered-from: specs/environment-drift-detection/tasks/04-docs-only-diff-scoping.md
Spec: ../SPEC.md
Touch: templates/stop-gate.sh, tests/test_hook_templates.sh

# Review whether the local Stop-gate's docs-only skip should exempt .claude/** in this toolkit repo

## Answers

Human decision (2026-07-14, asked directly): carve `.claude/**` out of the
docs-only skip set for repos where `.claude/` is the shipped product, not
incidental config. Implemented via a generic signal — a `.claude-plugin/`
directory at the repo root (the existing convention this toolkit already
uses to distribute itself as a Claude Code plugin) — rather than a
toolkit-specific hardcode, so the carve-out applies to any repo shaped like
this one without a bespoke marker file. Every other docs-only path
(`**.md`, `docs/**`, `specs/**`) is unaffected and stays skippable
regardless of this marker.

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

- [x] `grep -n "claude_is_product" templates/stop-gate.sh` → at least 1 hit
      (returns 1: the `.claude-plugin/`-detection carve-out) — verifier PASS (2026-07-16 sweep)
- [x] `bash tests/test_hook_templates.sh` exits 0, including new cases for
      a `.claude/**`-only diff in a repo WITH a `.claude-plugin/` marker
      (check runs in full) and WITHOUT one (still docs-only, skipped) —
      91 pass, 0 fail — verifier PASS (2026-07-16 sweep)
- [x] `bash tests/test_install_gates.sh` exits 0 (no regression) — 168
      pass, 0 fail — verifier PASS (2026-07-16 sweep)
