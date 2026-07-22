Status: done
Discovered-from: specs/ctx-doc-drift-gate/tasks/01-conformance-test.md
Spec: ../SPEC.md
Blocking: no
Priority: P2
Touch: docs/guides/ctx-cujs.md

# docs/guides/ctx-cujs.md documents an unshipped `ctx show` command as a live step

`docs/guides/ctx-cujs.md:70` documents `ctx show <symbol>` as a live
"Sequence" step, while the same guide says at line 75 that `show` is not
yet shipped — a latent adoption trap. Task 01's conformance gate waives
this drift (via a `Waiver { subcommand: "show", flag: None }` entry)
rather than fixing it, since fixing the guide is outside task 01's Touch.
The waiver becomes stale (auto-warns) once the guide drops the invocation
or `show` ships.

## Goal

Make the DIG IN journey (section 3) of `docs/guides/ctx-cujs.md` accurate
about `ctx show`. The journey was internally inconsistent: its "Sequence"
step presented `ctx show <symbol>` as a live command while its "Failure
modes" line claimed `show` is not yet shipped. **Ground-truth check at
authoring time (2026-07-22): `ctx show` HAS shipped** — the binary defines
`ctx show [OPTIONS] <SYMBOL>` (specs/ctx-query-ergonomics/tasks/01, Status
`done`) and resolves symbols live. So the stale half is the "not yet
shipped" caveat, not the Sequence step. Fix: document `ctx show <symbol>` as
the live Sequence step and replace the false caveat with `show`'s real
failure mode (ambiguous resolution → candidate qpaths → rerun with the
`<path>:<name>` selector).

## Design decision (course correction from the stub's premise)

The draft stub described the finding under the assumption that `show` is
unshipped ("an unshipped `ctx show` command"). That premise is now stale:
`show` shipped after the finding was filed. Per the repo's "verify against
CURRENT state" discipline, the guide must match the binary — documenting a
shipped command as unshipped would be worse drift, not a fix. Resolution
direction therefore flips from the stub's implied "demote show" to "document
show as the shipped command it is."

Scope stays `docs/guides/ctx-cujs.md` only (no `doc_conformance.rs` edit,
which sibling task 04 is editing concurrently — no file overlap). Because
`ctx show <symbol>` now validates against the real binary, task 01's
`Waiver { subcommand: "show", flag: None }` is now genuinely stale and the
conformance test reports it as a WARNING (never a failure — gate stays
green). Retiring that stale waiver is a `doc_conformance.rs` edit outside
this task's Touch; see Discovered.

## Acceptance

- [x] The live "Sequence" step of the DIG IN journey documents the shipped
  `ctx show <symbol>` command:
  `sed -n '/^## 3\. DIG IN/,/^## 4\./p' docs/guides/ctx-cujs.md | grep -F '**Sequence:** `ctx show <symbol>`'`
  → exit 0. Verified: matches the Sequence bullet, exit 0.
- [x] The stale "not yet shipped" caveat is gone from the journey (the guide
  no longer contradicts the binary):
  `sed -n '/^## 3\. DIG IN/,/^## 4\./p' docs/guides/ctx-cujs.md | grep -ci 'not yet shipped'`
  → 0. Verified: 0.
- [x] `ctx show` is in fact shipped in the binary (grounds the fix):
  `cd context-tree && cargo run -q -- show --help` → exit 0. Verified: exit 0
  (`Usage: ctx show [OPTIONS] <SYMBOL>`); live `ctx show main` resolved real
  candidate symbols.
- [x] The docs↔binary conformance gate stays green (the now-live
  `ctx show <symbol>` invocation validates against the binary; no new drift):
  `cd context-tree && cargo test --test doc_conformance` → exit 0. Verified:
  "test result: ok. 5 passed; 0 failed". Full `context-tree/scripts/check.sh`
  also green (exit 0).

## Discovered

- Task 01's `Waiver { subcommand: "show", flag: None }` in
  `context-tree/tests/doc_conformance.rs` is now genuinely stale (`show`
  shipped), so the conformance test emits a stale-waiver WARNING for it.
  Retiring it is a one-line delete of the waiver entry + its comment block,
  but that file is outside this task's Touch and is being edited concurrently
  by task 04 (reverse-coverage builtin-noise filter). Follow-up: retire the
  `show` waiver in a `doc_conformance.rs`-scoped commit (mirrors task 03's
  `map --limit` waiver retirement).
- The reverse-coverage report now lists `show --head`, `show --in`,
  `show --json`, `show --no-sync` as undocumented — real under-claiming of
  the shipped `show` flags. Documenting them belongs to an R2-style SKILL.md
  stale-claims sweep (registry-slotted), not this guide-scoped task.
