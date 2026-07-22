Status: done
Discovered-from: spec-completion review (2026-07-21)
Spec: ../SPEC.md
Blocking: no

# JSON no-match output omits the "did you mean" candidates text mode emits

Text-mode `sig`/`refs` no-match prints near-miss candidates before the
boundary note (task 02), but the `--json`/MCP no-match object carries
only `boundary_note` + `suggested_check`, not the candidate list — a JSON
consumer has no way to surface the same R4 suggestion. This may be an
intentional text-mode-only scoping of R4 (task 02's own JSON tests assert
only the two existing keys, not a new candidates key), or an unintended
parity gap. Left unfixed by the reviewing worker pending a decision on
whether JSON parity was intended.

## Decision

Resolved as an unintended parity gap, fixed per shape (b): the `--json`/MCP
no-match object is EXTENDED with a `did_you_mean` array mirroring the
text-mode candidate list. The key is present (a non-empty JSON array of
symbol names) exactly when text mode would print its `did you mean:` line,
and OMITTED when no near-miss exists — so the no-candidate object stays
byte-identical to today's `error`/`symbol`/`boundary_note`/`suggested_check`
shape and every task-01/02 JSON golden (R2) survives unchanged. Additive and
reversible; the shared `render()` core carries it to the MCP surface for
free. Scope: `sig` and `refs` no-match JSON only — the two surfaces that emit
the text-mode candidate list.

## Acceptance

- `cd context-tree && cargo test --test query
  sig_no_match_json_includes_did_you_mean_candidates` passes — a
  `sig --json` no-match whose query is a case variant of an indexed symbol
  returns a `did_you_mean` array containing that candidate, alongside the
  unchanged legacy/boundary keys.
- `cargo test --test query sig_no_match_json_omits_did_you_mean_when_no_near_miss`
  passes — a `sig --json` no-match with nothing close has NO `did_you_mean`
  key, and `sig_no_match_json_extends_error_object` (the R2 golden) still
  passes.
- `cargo test --test query refs_no_match_json_includes_did_you_mean_candidates`
  passes — the `refs --json` surface carries the same array (parity with its
  text-mode candidate list).
- `cargo test --test mcp sig_no_match_via_mcp_carries_did_you_mean` passes —
  the candidate array arrives through the MCP path (shared `render()` core).
- `cd context-tree && cargo test` is green and the project gate
  (`bash scripts/check.sh`) passes.
