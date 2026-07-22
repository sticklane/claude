# Fixture: only valid `ctx` invocations

Used by the doc-conformance stale-waiver and reverse-coverage tests. Every
invocation below is a real subcommand+flag combination, so analyzing this
fixture yields zero drift.

- `ctx tree <path>`
- `ctx map --tokens 5`
- `ctx refs <name>`
- `ctx notes add <symbol> --kind gotcha`
- `ctx notes list [--file <path>]`
