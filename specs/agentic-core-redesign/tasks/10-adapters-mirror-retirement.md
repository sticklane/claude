# Task 10: runtime adapters and mirror-machinery retirement

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (statement 12; component "Runtime adapters"; D5, D11; Migration step 5)
Touch: antigravity/, codex/, CLAUDE.md, .claude/rules/mirror-procedure-discipline.md, .claude/rules/mirror-verification.md, tests/test_mirror_procedure_coverage.sh, tests/mirror-procedure-manifest.txt, tests/test_skill_chain_determinism.sh, tests/test_antigravity_parity.sh, tests/test_antigravity_content_parity.sh, tests/test_codex_parity.sh, .claude-plugin/plugin.json

## Goal

PIVOTED SCOPE (2026-07-22 addendum, ../SPEC.md): portability is
data-level — other runtimes read bd's queue, ctx's index, and task
files directly; no procedure adapters are maintained. The
antigravity/ and codex/ trees are DELETED, each replaced by a short
README.md pointing at the data layer (bd/ctx/specs) and this
decision. The mirror machinery dies with them. Original adapter
framing follows for context: per runtime, a small prompt
folder that frames judgment and shells out to `agentic`, native hook
wiring, and an onboarding snippet — no ported procedure. The mirror
machinery is gone: the procedure manifest, its coverage test, the parity
gates, and both mirror rules files are deleted; CLAUDE.md's port-chain
authoring conventions are rewritten to the adapter model. plugin.json
bumps.

## Touch

Adapter prose is a rewrite, not a port — per
docs/memory/workboard-mirror-verbatim.md, prose mirrors were never
byte-identical, so acceptance uses content-coverage checks (the
concepts/commands that must appear), never diff-emptiness.

## Steps

1. Replace each runtime tree's procedure files with adapter prompts
   invoking `agentic ready/claim/compose/loop/verdict` (content-coverage
   list: the verbs, the verdict-file contract, the launch framing).
2. Delete the manifest, coverage test, parity tests, and both mirror
   rules files; remove their references from CLAUDE.md, check scripts,
   and docs.
3. Rewrite CLAUDE.md's port-chain conventions section to the adapter
   model (CLI is source of truth; adapters are per-runtime wiring).
4. Bump plugin.json (base-commit comparison); run everything.

## Acceptance

- [ ] `bash -c 'for t in antigravity codex; do [ -d $t ] && [ $(ls $t | wc -l) -gt 1 ] && echo "tree survives: $t"; done; exit 0'` → no output (each tree reduced to a single README.md pointing at the data layer)
- [ ] `ls tests/mirror-procedure-manifest.txt tests/test_mirror_procedure_coverage.sh tests/test_antigravity_parity.sh tests/test_antigravity_content_parity.sh tests/test_codex_parity.sh .claude/rules/mirror-procedure-discipline.md .claude/rules/mirror-verification.md 2>&1 | grep -c "No such file"` → `7` (the parity gates die with the mirrors they guarded)
- [ ] `grep -c "port chain" CLAUDE.md` → `0` (conventions rewritten, not orphaned)
- [ ] `bash scripts/check.sh` → green with the deleted tests removed from the suite, and `claude plugin validate .claude-plugin` (or the repo's documented equivalent) passes

Depth ceiling: L1 for adapter-prose quality — whether the adapter prompts
read well per runtime is a human judgment; the behavioral complement is
one live smoke session per runtime recorded as manual-pending evidence.
