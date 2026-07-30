# Adversarial repair review

Date: 2026-07-26

## Scope

The final review covered the complete pre-registration source bundle for the
Mardi Gras integration:

- `SPEC.md`, `HUMAN.md`, and all 43 immutable task definitions;
- the bootstrap and migration controllers, schemas, manifests, and tests;
- the surface-inventory records and project gates;
- dependency, supersession, workset-extension, same-file parallelism, and
  release-gating semantics; and
- the distinction between Mardi Gras repository/drain monitoring and the
  session-wide, cross-repository `fleet` view.

The reviewed design keeps Beads as the durable ledger, uses programmatic
coordination, runs Touch-overlapping implementation tasks concurrently in
isolated Git worktrees when their dependency edges permit it, and serializes
only deterministic integration and landing.

## Findings repaired

The first frozen-bundle review was **NOT READY**. Follow-up reviews remained
**NOT READY** until each material finding below was repaired:

1. Resume and post-publication provider actions could rely on a stale claim.
   The controller now freshly observes the exact claim before every
   not-yet-committed provider action; committed recovery remains idempotent.
2. Provider receipts did not prove exact terminal state. Receipts now bind
   closed response schemas, per-primitive evidence, authority snapshots,
   metadata, revisions, notes, edges, history, and terminal snapshot digests.
3. R8 storage could be redirected or confused by symlinks, ancestor swaps,
   weak ownership, or ambiguous temporary heads. Both controllers now use
   descriptor-relative, no-follow operations, owned modes, owner-bound
   recovery, and exact sequenced-and-digested temporary-head protocols.
4. Migration recovery did not prove every primitive or canonical bootstrap
   authority. It now records prepared/committed evidence per primitive, uses
   closed complete snapshots, and accepts only the canonical external
   terminal bootstrap receipt under R8.
5. An inventory disposition contradicted the repair. The migration test is
   explicitly classified as `repair`; the retained bootstrap test remains
   `retain`.
6. The proposed workset validator could accept a lossy summary and could
   confuse duplicate historical/replacement numeric task prefixes. It now
   derives the complete structured envelope from the authored UTF-8/LF task
   bytes and resolves exact task paths; ambiguity fails closed.
7. Terminal observation could combine a torn snapshot. Authority cursors now
   bracket two identical captures, the terminal evidence binds their digest,
   and drift before receipt observation or creation prevents certification.

The workset-changing correction is explicit in the source and task graph:
registered definitions remain immutable provenance, but genuinely new
mandatory scope is represented by a new immutable dependent task through the
guarded coordinator. Registered task files and live acceptance text are not
rewritten.

## Independent results

- Replacement graph oracle: **PASS**. The 27-task replacement DAG is exact
  and acyclic; all 11 supersessions, external rewires, staged replacement
  dependencies, public-JSON chain, HUMAN blockers, workset split, `fleet`
  preservation, and same-file worktree parallelism checks passed.
- Bootstrap controller re-audit: **READY**, including 36 focused tests.
- Migration controller: 49 focused tests passed; one future real-provider
  test is intentionally skipped until the attested provider exists.
- Combined focused controls: **85 passed, 1 skipped**.
- Full repository check: **PASS**, with only the repository's documented
  quarantine for `tests/test_eval_coverage_lint.sh`.
- Manifest/config validation, Python compilation, inventory classification,
  and `git diff --check`: **PASS**.

## Final verdict

**READY.**

The critic's final whole-bundle verdict was `READY` for source bundle SHA-256
`381cb06eb04ef0fa733bfa5ad593022533db68ea438de03547faeef5233d9020`;
the reviewed `SPEC.md` SHA-256 was
`b9f184dd32a38494829dedfc62df105ed103b2d34caeed6fc2abad97fc5c5690`.

After that verdict, the sole administrative change to reviewed behavior
source was `Breakdown-ready: false` to `Breakdown-ready: true`. This review
record documents the completed audit and was not part of the behavior bundle
the critic hashed. Registration and live migration still require the
specified source-commit and direct-child attestation boundary; readiness does
not bypass it.
