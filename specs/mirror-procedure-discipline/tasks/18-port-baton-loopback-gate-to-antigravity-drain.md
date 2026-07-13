Status: draft
Discovered-from: specs/mirror-procedure-discipline/tasks/14-audit-codex-drain.md
Spec: ../SPEC.md
Blocking: no

# Port the d35fc9e baton loop-back gate to antigravity's drain mirror

Commit `d35fc9e` changed the Claude Code drain source's step 3 closing line
and step 3a's opening to force the baton-trigger check after every recorded
verdict, and task 13/14 this run already ported the equivalent fix into
`codex/.agents/skills/drain/SKILL.md`. `antigravity/.agents/workflows/drain.md`
still carries the pre-fix discretionary "At each safe boundary" / "Loop to
step 2 …" phrasing and has not received the same fix.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
