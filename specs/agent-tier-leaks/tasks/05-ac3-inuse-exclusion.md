Status: draft
Discovered-from: specs/agent-tier-leaks/tasks/01-verifier-leak-trace.md
Spec: ../SPEC.md
Blocking: no

# Task 05: Exclude .in_use PID markers from the plugin-cache-untouched check

AC3's command is a blunt mtime check that catches transient `~/.claude/plugins/cache/.../<ver>/.in_use/<pid>` runtime PID markers written by any live `claude` process, so it can read >0 with no content change — future readers of that criterion (in SPEC.md / this task) should exclude `-not -path '*/.in_use/*'`.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
