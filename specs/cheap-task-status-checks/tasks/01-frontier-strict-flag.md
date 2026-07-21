# Task 01: `drain_frontier.py --strict` flag, fixtures, three-tree mirror

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/drain/drain_frontier.py, antigravity/.agents/skills/drain/drain_frontier.py, codex/.agents/skills/drain/drain_frontier.py, .claude/skills/drain/test-fixtures/frontier-strict/**

## Goal

`drain_frontier.py` accepts a `--strict` flag. With no
`unresolved-external-dep` diagnostic present, output (exit code, stdout
JSON) is byte-for-byte identical with and without the flag. When one or
more such diagnostics are present, `--strict` emits the same stdout JSON
as today plus prints each offending task path and dangling reference to
stderr, and exits nonzero. The change is copied byte-for-byte into the
`antigravity` and `codex` mirrors of this file (all three are confirmed
identical today via `diff`) — this is a `cp`-and-`diff` step, not a
reimplementation.

## Touch

Only `drain_frontier.py` in its three locations, plus a new
`.claude/skills/drain/test-fixtures/frontier-strict/` fixture directory.
Do not touch `admission.py`, any `SKILL.md`, or `reference.md` — those are
task 02's and the closing task's scope.

## Steps

1. Write the failing test first: add a fixture spec dir under
   `.claude/skills/drain/test-fixtures/frontier-strict/dangling-dep/`
   containing a minimal `tasks/01-x.md` whose header includes
   `Depends on: 99` (a bare number with no task numbered 99 anywhere in
   this fixture spec — this parses successfully as a `number`-kind
   dependency per `_parse_deps`, so it reaches `compute_frontier`'s
   `unresolved-external-dep` branch rather than raising `FrontierError`
   the way an unparseable word-token would). Confirm today, before any
   code change: `python3 .claude/skills/drain/drain_frontier.py
   .claude/skills/drain/test-fixtures/frontier-strict/dangling-dep`
   exits 0 and its JSON `diagnostics` array contains a
   `kind: "unresolved-external-dep"` entry — this proves the diagnostic
   already fires; only the exit-code/stderr behavior is missing (there is
   no `--strict` flag yet, so this step is establishing the "red" baseline
   the new flag must change, not a literal failing pytest).
2. Add a second fixture,
   `.claude/skills/drain/test-fixtures/frontier-strict/valid-deps/`, whose
   task(s) have only resolvable `Depends on:` references (a regression
   fixture for the "no diagnostic present" path).
3. In `.claude/skills/drain/drain_frontier.py`'s `main()`, add a
   `--strict` `argparse` flag. After `compute_frontier` returns, if
   `--strict` is set and any entry in `frontier["diagnostics"]` has
   `kind == "unresolved-external-dep"`, print each such entry's `path` and
   `dep` to stderr (one line each) after the existing stdout JSON dump,
   and set the return code to a nonzero value (2, matching the existing
   `FrontierError` exit code, or another value distinct from 0 — pick one
   and use it consistently). Without `--strict`, or with no such
   diagnostic present, behavior must be identical to today's — do not
   change the no-flag code path at all.
4. Verify against both fixtures (Steps below under Acceptance).
5. Copy the finished file verbatim: `cp
   .claude/skills/drain/drain_frontier.py
   antigravity/.agents/skills/drain/drain_frontier.py && cp
   .claude/skills/drain/drain_frontier.py
   codex/.agents/skills/drain/drain_frontier.py`. Confirm with `diff`
   (Acceptance below) rather than assuming the copy succeeded.

## Acceptance

- [x] `python3 .claude/skills/drain/drain_frontier.py
      .claude/skills/drain/test-fixtures/frontier-strict/dangling-dep`
      (no flag) exits 0 and its stdout JSON contains a
      `"kind": "unresolved-external-dep"` diagnostic — unchanged from
      today. → passed: exit 0, diagnostic present (RED baseline run above).
- [x] `python3 .claude/skills/drain/drain_frontier.py
      .claude/skills/drain/test-fixtures/frontier-strict/dangling-dep
      --strict` exits nonzero, stdout still contains the same JSON as the
      no-flag run, and stderr names the offending task path and the
      dangling reference (`99`). → passed: exit 2, stdout byte-identical to
      no-flag run (`diff` clean), stderr = "…/01-x.md: unresolved
      dependency 99".
- [x] `python3 .claude/skills/drain/drain_frontier.py
      .claude/skills/drain/test-fixtures/frontier-strict/valid-deps
      --strict` exits 0 with stdout identical to the same command without
      `--strict`. → passed: exit 0, stdout `diff` clean, zero stderr bytes.
- [x] `diff .claude/skills/drain/drain_frontier.py
      antigravity/.agents/skills/drain/drain_frontier.py` exits 0. → passed
      (exit 0 after `cp`).
- [x] `diff .claude/skills/drain/drain_frontier.py
      codex/.agents/skills/drain/drain_frontier.py` exits 0. → passed
      (exit 0 after `cp`).
