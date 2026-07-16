Status: draft
Discovered-from: specs/trajectory-evals/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# confirm the real stream-json field shape for the scout-delegation trajectory grep

`evals/breakdown/02-scout-delegation/assert.sh` and the matching
`.claude/skills/evals/reference.md` example grep for the bare `"scout"`
value in the stream-json Task-input field, assumed from Claude Code's
documented format rather than confirmed against a real transcript. If
plugin agents surface namespaced (e.g. `"agentic:scout"`), the substring
match still works, but a differently-nested field could false-fail. Needs
a real `claude -p --output-format stream-json` run to confirm and, if
necessary, adjust the grep.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
