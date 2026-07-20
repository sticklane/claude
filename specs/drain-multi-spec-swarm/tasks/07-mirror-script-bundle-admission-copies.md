Status: draft
Discovered-from: specs/drain-multi-spec-swarm/tasks/03-mirror-and-version-bump.md
Spec: ../SPEC.md
Blocking: no

# Ship admission.py/drain_frontier.py copies in the antigravity script bundle

`antigravity/.agents/skills/drain/` (the script-bundle convention its
README documents, used by `screen-stub.sh`) carries no `admission.py` or
`drain_frontier.py` copy, so the drain workflow's mirrored shell-out
takes the documented by-hand fallback until copies ship; the codex
overlay inherits the same gap. (Worker-reported discovery from the task
03 mirror port; vet/rewrite before promoting.)

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
