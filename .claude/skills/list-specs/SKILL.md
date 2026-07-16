---
name: list-specs
description: Prints a per-spec status table for the current repo - one row per specs/ directory with its task Status rollup and the next pipeline command to run (/critique, /breakdown, /build, /drain, or /distill) - by running the bundled list_specs.py scanner against the cwd. Use when the user asks "list the specs", "what's the state of the specs", "which specs are ready", "what's the next command per spec", or "where is each spec in the pipeline". For reordering work rather than reporting the next command - rebalancing Priority: headers across pending/blocked/deferred/draft tasks and not-yet-broken-down specs - use /prioritize instead. For cross-repo state, use /workboard.
---

Report, don't act: run the scanner, present its table, stop. This skill
is read-only, takes no arguments (it always scans `specs/` under the
current working directory), and must never auto-invoke the command named
in the table's Next command column — the human decides which to run.

## Procedure

1. Run `python3 .claude/skills/list-specs/list_specs.py` from the repo
   root (plugin installs: the same `list_specs.py` sits in this skill's
   own directory — invoke it by its path relative to this SKILL.md).
2. Present the script's stdout — a markdown table with one row per spec
   (`| Spec | Status | Next command |`, alphabetical by slug) — as the
   response, unaltered. A spec declaring `Rigor: prototype` carries a
   `[prototype]` annotation on its Spec cell; production (or absent, the
   default) specs show no marker. If it prints `no specs/ directory found`,
   relay that instead.
3. Do not run, queue, or offer to run any command from the Next command
   column unless the user asks in a follow-up.

Next stage: none — the table's Next command column names a per-spec next
step; the human decides which to run.
