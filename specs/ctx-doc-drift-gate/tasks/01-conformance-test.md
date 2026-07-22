# Task 01: docs↔binary conformance test with waiver list + coverage report

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (requirements R1, R3)
Touch: context-tree/tests/doc_conformance.rs, context-tree/tests/fixtures/doc_conformance/

## Goal

A cargo integration test extracts every backtick-quoted
`ctx <subcommand> [--flag …]` invocation from
`.claude/skills/ctx/SKILL.md`, `antigravity/.agents/skills/ctx/SKILL.md`,
and `docs/guides/ctx-cujs.md` (read via `CARGO_MANIFEST_DIR/../`) and
asserts each subcommand and flag exists per the binary's clap definitions
(`env!("CARGO_BIN_EXE_ctx")` + recursive `--help` parsing). It carries a
shape-keyed waiver list seeded with `map --limit`, emits a non-gating
reverse-coverage report section, and warns (never fails) on stale waiver
entries.

## Touch

New test file + fixtures only. Do NOT edit the three doc files (task 02
and sibling specs own them) or the waiver seed's target rows. P1 because
it proves the spec's riskiest assumption (tokenizer over real doc prose).

## Steps

1. Write the failing test first against the CURRENT docs: with the
   waiver list empty, the test must fail on the `map --limit` row in
   both skill files — capture that failure output once for evidence,
   then seed the waiver and go green (SPEC R1's demonstration).
2. Implement the extractor per SPEC R1's tokenizer contract: recurse
   nested subcommands (`ctx notes list --help`, `ctx notes add --help` —
   `--file`/`--kind` live on the nested commands); strip `<...>`
   placeholders, `"..."` quoted args, `a|b|c` enum values, and the
   `at <file>:<line>` colon form; validate flags inside `[...]` optional
   groups.
3. Waiver list: shape-keyed (subcommand + flag), matching across all
   three files; one seeded entry `map --limit`. Stale entry (matches no
   doc row) → WARNING in the report section, never a failure; add a test
   for the warning path using a fixture waiver.
4. Reverse-coverage report (R3): emit binary subcommands/flags absent
   from all three doc surfaces; assert the report section is present and
   well-formed even when empty.
5. `cargo fmt` + `cargo clippy` clean per the crate's conventions.

## Acceptance

- [x] `cd context-tree && cargo test --test doc_conformance` → exit 0 (green with the seeded waiver) — verifier: "test result: ok. 5 passed; 0 failed"
- [x] Evidence captured in this task's Progress notes: the test output failing on `map --limit` in BOTH skill files with the waiver removed (run once, then re-seed) — RED reproduced (worker + verifier): drift on `map [--limit N]` in both `.claude/skills/ctx/SKILL.md` and `antigravity/.agents/skills/ctx/SKILL.md`; captured in the verdict/Progress and evidence/01-conformance-test.md
- [x] `cd context-tree && cargo test --test doc_conformance -- --nocapture 2>&1 | grep -c 'reverse-coverage'` → ≥1 (report section emitted) — verifier: grep -c → 1
- [x] Stale-waiver warning path has a passing test (assert warning emitted, exit still 0) — `stale_waiver_warns_without_failing` passes (asserts drift empty AND WARNING text present)
- [x] `grep -c 'map --limit' context-tree/tests/doc_conformance.rs` → ≥1 (seeded waiver present until task 03 retires it) — grep -c → 4
- [x] `cd context-tree && cargo clippy --tests -- -D warnings` → exit 0 — verifier: clean, exit 0 (also `context-tree/scripts/check.sh` green)

## Decisions

- 2026-07-21: Seeded a second waiver (`show`, flag: `None`) beyond the
  spec's single `map --limit` entry. `docs/guides/ctx-cujs.md:70`
  documents `ctx show <symbol>` as a live "Sequence" step for a subcommand
  the same guide says (line 75) is not yet shipped — genuine
  documented-but-absent drift the tokenizer catches, which would keep the
  gate RED against acceptance criterion 1. Waiving is the spec's own
  designed escape hatch for known drift. Reversible: delete the
  `Waiver { subcommand: "show", flag: None }` entry to un-waive; doing so
  re-reds the gate on the `show` row until `show` ships or the guide is
  corrected.

## Discovered

- Reverse-coverage report (R3, non-gating) lists universal clap built-ins
  `--help`/`--version` as "undocumented" on every subcommand — cosmetic
  noise diluting the real under-claimed capabilities (e.g. `tree --depth`,
  `refs --limit`, `map --doc`, `--no-sync`). See task 04.
- `docs/guides/ctx-cujs.md` documents an unshipped `ctx show` command as a
  live "Sequence" step (line 70), not just a future note — a latent
  adoption trap the drift gate now waives rather than fixes. See task 05.
