Status: draft
Discovered-from: drain inventory (orchestrator, this session, 2026-07-21)
Spec: ../SPEC.md
Blocking: no

# Scanner has no way to encode a cross-spec "landing order" serialization gate

`drain_frontier.py` computes dispatchability purely from a task file's own
`Depends on:` header, which only expresses same-spec, task-number
dependencies. Several `ctx-*` specs coordinate edits to the SHARED
`.claude/skills/ctx/SKILL.md` file via a prose-only "Landing order"
registry (specs/ctx-skill-token-doctrine/SPEC.md's opening section),
which serializes SEVEN specs' SKILL.md-editing tasks into a fixed slot
order (1-7) so breakdown never emits two SKILL.md-editing tasks as
parallel work. This constraint lives only in SPEC.md prose — it is not,
and cannot currently be, expressed in any task file's `Depends on:`
header — so the scanner has no signal that would stop it from marking a
later-slot task dispatchable the moment its own (same-spec) numeric
dependency is satisfied.

Observed live 2026-07-21: `drain_frontier.py specs/ctx-absence-check
specs/ctx-cujs specs/drain-plugin-path-resolution` listed
`specs/ctx-cujs/tasks/02-skill-link-and-typo-fix.md` (= ctx-cujs SPEC.md's
R3, registry SLOT 7, "always last") as dispatchable, because its
`Depends on: 01` is satisfied (task 01 is done) — despite slots 1-6
(ctx-skill-token-doctrine R2/R7, ctx-static-analysis-augmentation R1,
ctx-query-ergonomics R4, ctx-minified-skip R5, ctx-dead-code-zones R4,
ctx-absence-check R5) being either not yet broken down into tasks/ at all
(five of six) or blocked (the sixth). The orchestrator caught this only
by reading ctx-skill-token-doctrine's SPEC.md prose directly and
cross-referencing the Landing order registry by hand; a scanner-only
read of the frontier would have dispatched it prematurely, corrupting
the shared SKILL.md's intended edit order. `ctx-absence-check`'s own
task 03 correctly reports `blocked`/`unblock: run: ...` for the SAME
Landing-order dependency, showing the registry's authors already know to
encode it as an explicit `Unblock:` runnable check on tasks that are
Status: blocked — but ctx-cujs/tasks/02 is `Status: pending` with only a
same-spec `Depends on:`, so it gets no equivalent protection.

## Acceptance

<!-- draft: needs runnable criteria before promotion. Likely shape: either
(a) a documented convention that any task participating in a cross-spec
landing-order registry must ship as `Status: blocked` with an `Unblock:
run:` check (matching ctx-absence-check/tasks/03's pattern) rather than
`Status: pending` + `Depends on:` alone, with breakdown's own procedure
updated to enforce it, or (b) a scanner-readable header (e.g. a
`Landing-order:` or generalized cross-spec `Depends on:` referencing
another spec's task-file path — reference.md already notes
`Depends on:` accepts repo-relative task-file paths across specs) that
lets drain_frontier.py itself detect the unmet cross-spec gate without a
human/orchestrator prose read. Either fix is verified by re-running
drain_frontier.py over ctx-absence-check + ctx-cujs +
drain-plugin-path-resolution + ctx-skill-token-doctrine and confirming
ctx-cujs/tasks/02 no longer appears in `dispatchable` while slots 1-6
remain unlanded. -->
