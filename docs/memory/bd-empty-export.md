# `bd export` writes an empty file while the database holds issues

Read this when `bd export` prints "Exported 0 issues" and exits 0 in a repo
whose `bd list` or `bd ready` still shows real work, or when deciding whether
a zero-issue export may be committed.

## What was observed

In `/Users/sjaconette/ynab-mcp-new` on 2026-07-25 (bd 1.1.0, Homebrew),
`bd export -o .beads/issues.jsonl` exits 0, prints `Exported 0 issues`, and
leaves a zero-line file, while `bd list` and `bd ready` return 13 real issues.
`bd export --all` and `bd export -C <repo>` behave the same. `bd doctor` and
`bd sql` both refuse with `not yet supported in embedded mode`, so the
database cannot be inspected directly from the CLI.

## It is not an export bug — the whole aggregate read path reports zero

Every command that reads the table as a whole reports nothing in that repo,
while every command that runs a filtered query returns the 13 issues:

| reports 0                                    | returns the 13 issues |
| -------------------------------------------- | --------------------- |
| `bd export`, `bd count`, `bd status`, `bd info` | `bd list`, `bd ready`, `bd show` |

An issue created *after* the fact is equally invisible to `bd count` and
`bd export`, so this is not an attribute of the existing rows. Framing it as
"export is broken" points at the wrong command.

## Ruled out, each by a controlled comparison

- **Embedded dolt mode.** `~/claude` is also `dolt_mode: embedded` on bd
  1.1.0 and exports 439 issues.
- **bd version.** Both repos are bd 1.1.0 with `.beads/.local_version` 1.1.0.
- **A hyphenated issue prefix.** Two scratch repos, prefixes `plainpfx` and
  `hy-phen-pfx`, both export correctly.
- **`beads.role`.** Exercised `maintainer`, `contributor`, and unset against
  one scratch repo; export count was unchanged.
- **Pending schema migration.** `bd migrate status` reports "Version matches"
  in both repos and `bd migrate schema` reports schema v53 already applied.
- **The repository path and its git config.** An `rsync -a` copy of
  `.beads/` into an unrelated scratch git repo reproduces the symptom exactly
  (`bd list` 13, `bd count` 0, `bd export` 0). The same copy of `~/claude`'s
  `.beads/` stays healthy (`bd count` 439), so the copy method is faithful
  and the defect travels with the database.

## What would settle it

Which query each command issues — available from bd's source, or by migrating
a **copy** of the affected database to dolt server mode, where `bd sql` works,
and running the export's own query by hand. Do not migrate the live
`ynab-mcp-new` database: whether to migrate it is an open human decision
(bd issue agentic-hty), and re-initializing it destroys the evidence.

Worth reporting upstream. A report needs: bd 1.1.0 embedded mode, the
`bd list` / `bd count` disagreement on one database, the fact that a newly
created issue is also uncounted, and that `bd doctor` and `bd sql` are both
unavailable in embedded mode so the reporter cannot inspect further.

## Consequence, and the guard

`bd export` exits 0 on the empty write, so any automation trusting the exit
code commits an empty queue file over a real one — and the export is the
committed, portable representation of the queue that non-bd consumers read.
`hooks/bd-export-guard/pre-commit` refuses a commit whose staged
`.beads/issues.jsonl` holds zero issues while the database holds more than
zero. The condition is the mismatch, never the bare zero: a genuinely empty
database exports zero issues and commits normally.
