Status: pending
Discovered-from: specs/ctx-doc-drift-gate/tasks/01-conformance-test.md
Spec: ../SPEC.md
Blocking: no

# docs/guides/ctx-cujs.md documents an unshipped `ctx show` command as a live step

`docs/guides/ctx-cujs.md:70` documents `ctx show <symbol>` as a live
"Sequence" step, while the same guide says at line 75 that `show` is not
yet shipped — a latent adoption trap. Task 01's conformance gate waives
this drift (via a `Waiver { subcommand: "show", flag: None }` entry)
rather than fixing it, since fixing the guide is outside task 01's Touch.
The waiver becomes stale (auto-warns) once the guide drops the invocation
or `show` ships.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
