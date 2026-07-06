Status: draft
Priority: P3
Discovered-from: specs/drain-rolling-window/tasks/05-ship-gates-and-mirrors.md
Spec: ../SPEC.md
Blocking: no

# Version-bump acceptance criteria that pin an exact pre-task value can go stale

Task 05's own acceptance criterion hard-coded the pre-task `plugin.json` version as `0.8.14`, but by the time the task actually ran, a sibling task (03's own bump, or an earlier merge) had already advanced it to `0.8.15` — the criterion's own fallback wording ("or simply confirm the checked-in version string is not 0.8.14") absorbed the drift this time, but a future task authored the same way, without that fallback, would false-fail once a sibling task bumps the same file first. Worth a note in `/breakdown`'s authoring guidance: version-bump acceptance criteria should check "changed from the value at the task's own base commit" (or equivalent relative check) rather than hard-coding an exact pre-task literal.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
