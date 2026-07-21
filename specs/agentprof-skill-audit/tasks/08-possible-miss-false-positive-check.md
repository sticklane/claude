Status: draft
Discovered-from: specs/agentprof-skill-audit/tasks/04-cli-wiring-and-report.md
Spec: ../SPEC.md
Blocking: no

# DetectPossibleMisses can over-report vs SPEC R5

`DetectPossibleMisses` (task 02, cmd_skillcheck_trigger.go) flags any user
turn matching an installed skill's trigger phrase without cross-checking
whether that skill was actually invoked somewhere in the session. SPEC R5
defines a possible-miss as "no matching Skill call" — the current
implementation can flag a turn as a possible miss even when the skill was
invoked later in the same session, producing false positives on real runs.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
