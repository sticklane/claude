Status: draft
Discovered-from: specs/fleet-viz-css-resync/tasks/01-resync-and-drift-guard.md
Spec: ../SPEC.md
Blocking: no

# Make the three container-hostile tests portable (GNU sed/stat, root)

tests/test_drain_owner_protocol.sh, test_hook_templates.sh, and test_install_gates.sh fail in root containers on GNU-vs-BSD sed/stat invocation and chmod-000 fixtures readable as root — pre-existing on base 6196cc8, so the full check sweep can never go green in that environment regardless of the change under test.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
