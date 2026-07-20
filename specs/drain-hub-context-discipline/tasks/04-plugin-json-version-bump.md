Status: draft
Discovered-from: 01-enforce-section-read-and-worker-prompt-delivery.md
Spec: ../SPEC.md
Blocking: no

# Bump plugin.json version for the drain skill behavior change

Task 01 changed `/drain`'s documented procedure (Grep-then-offset reads,
path-pointer Worker prompt delivery) but did not touch
`.claude-plugin/plugin.json`, which CLAUDE.md says to bump whenever skill
behavior changes. Confirm whether task 02 or 03 already covers this bump;
if not, bump the version.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
