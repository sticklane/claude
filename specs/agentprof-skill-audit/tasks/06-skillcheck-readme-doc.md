Status: done
Discovered-from: specs/agentprof-skill-audit/tasks/04-cli-wiring-and-report.md
Spec: ../SPEC.md
Blocking: no

# agentprof/README.md doesn't mention the skillcheck subcommand

`agentprof/README.md`'s subcommand list predates this spec and doesn't
list `skillcheck` alongside `claude`/`gcp`/`vertex`/`otel`/`antigravity`/
`build`. User-facing docs drift from the actual CLI surface.

## Acceptance

- [x] `grep -c 'agentprof skillcheck' agentprof/README.md` returns ≥ 2 — a
  dedicated section and a Commands-table row (was 0 before this task).
- [x] The Commands table carries a `skillcheck` row naming its report output:
  `grep -q '`agentprof skillcheck.*trigger' agentprof/README.md`.
- [x] The section documents the exclusion of explicit/self-chained
  invocations and the `--judge-tier` model choice:
  `grep -q 'self-chains' agentprof/README.md && grep -q 'judge-tier' agentprof/README.md`.
- [x] `bash scripts/check.sh` (from `agentprof/`) passes.
