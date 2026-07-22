Status: deferred
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

## Deferred questions

A dispatched worker confirmed the bug is real: `DetectPossibleMisses`
(`agentprof/cmd_skillcheck_trigger.go:161`) is called at
`cmd_skillcheck.go:220` with the full session user-turn list and never
cross-checks `invs` (the Skill invocations found in the same session), so
a turn matching skill X's trigger phrase is flagged even when X was
invoked in that session. Not promotable to a dispatchable task as-is:

1. No runnable acceptance criteria and no `Touch:` scope.
2. **Contradicts-premise-adjacent**: the fix conflicts with the SPEC's own
   "Out of scope" clause (`specs/agentprof-skill-audit/SPEC.md`, verbatim):
   "No fix to the possible-miss detector's precision beyond 'clearly
   labeled low-confidence' … this spec does not commit to a specific
   accuracy bar for it." A human must decide whether to reopen that scope.
3. Suppression semantics are ambiguous and unresolved by the SPEC (step 4
   "user turns that did NOT result in a Skill call" reads per-turn; R5 "no
   matching Skill call" reads session-wide) — pick one before writing
   tests: (a) suppress if skill X invoked anywhere in the session;
   (b) suppress if that specific turn triggered any skill; (c) suppress
   only if X invoked later in the session.

**Question:** does the spec author want to reopen possible-miss precision
(currently out-of-scope), and if so which suppression semantics? Once
decided, the task needs runnable acceptance criteria plus a `Touch:`
scope before it's dispatchable. No other pending task depends on this one
(`Blocking: no`).
