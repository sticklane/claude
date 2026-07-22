# Task 06: agentic ctx — the code index behind the same front

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: obsolete
Superseded: 2026-07-22 data-portability pivot (maintainer-ratified) — native ultracode is the execution engine; see ../SPEC.md addendum. Keeper fragments (screen, pre-flight budget check, tier doctrine) fold into specs/beads-daily-skill.
Depends on: 02
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (statement 7; component "ctx")
Touch: agentic/ctxcmd.py, tests/test_agentic_ctx.py

## Goal

`agentic ctx <args...>` fronts the existing ctx binary exactly as the
tracker verbs front bd: it resolves the binary (PATH →
`context-tree/target/release/ctx` → `cargo build --release` in
`context-tree/`), passes subcommands and `--json` through unchanged, and
exposes one internal helper `code_map(paths, token_budget)` that returns
a budgeted structure slice for the composer (task 07) built from
`ctx tree`/`ctx map` output restricted to the given paths.

## Touch

Wrapper only — no changes inside `context-tree/`. If the Rust build
fails in the worker's environment, flip to blocked with
`Unblock: run: cd context-tree && cargo build --release 2>&1 | tail -20`
rather than shipping a wrapper tested against nothing.

## Steps

1. Write `tests/test_agentic_ctx.py` failing first: passthrough of
   `tree`/`sig` against a small fixture source dir indexed in a temp
   `.context/`; `--json` passthrough parses; `code_map()` returns ≤ the
   token budget (ceil(bytes/4)) and only symbols under the given paths;
   a missing binary produces the resolution chain in the error.
2. Build ctx once (`cargo build --release`) and implement ctxcmd.py.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_ctx.py -q` → passes against the actually-built ctx binary
- [ ] `agentic ctx tree agentic --depth 1 | head -5` → prints the package's symbol outline (live behavior, this repo's index)
- [ ] `bash scripts/check.sh` → green
