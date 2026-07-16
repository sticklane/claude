---
name: list-specs
description: Renders a one-row-per-spec status table for the current repo by running the bundled list_specs.py scanner against the cwd - each row shows the spec's task Status rollup and the next pipeline command (/critique, /breakdown, /build, /drain, or /distill). Use when asked "list the specs", "which specs are ready", "what's the next command per spec", or "where is each spec in the pipeline". To reorder work (rebalance Priority: headers) rather than report the next command, use /prioritize; for cross-repo state, use /workboard.
---

Read-only reporter: run the scanner, relay its table, take no further
action. No arguments — it always scans `specs/` under the current
working directory. Never auto-run the command a row suggests; picking
the next step is the human's call.

## Procedure

1. Execute `python3 <this skill dir>/list_specs.py` from the repo root
   (the scanner ships in this skill's directory).
2. Relay its stdout verbatim — a markdown table
   (`| Spec | Status | Next command |`, rows alphabetical by spec slug). A
   spec declaring `Rigor: prototype` carries a `[prototype]` annotation on
   its Spec cell; production (or absent, the default) specs show no marker.
   If it prints `no specs/ directory found`, relay that message instead.
3. Stop there: do not invoke, queue, or offer the Next command entries
   unless the user asks in a follow-up turn.

Next stage: none — each row's Next command column already names that
spec's next step; the human chooses which to run.
