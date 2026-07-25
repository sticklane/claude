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

The split runs along whole-table reads versus filtered queries, so framing it
as "export is broken" points at the wrong command.

An issue created *after* the fact was equally invisible to `bd count` and
`bd export`. That observation came from running `bd create` against the live
`ynab-mcp-new` database, which the investigating task had explicitly
forbidden — the same database this file tells you not to re-initialize. It
must not be repeated, and it probably does not mean what it looks like: see
the read-only hypothesis below, which reads it as a symptom of that condition
rather than as independent evidence about the existing rows.

## Leading hypothesis: the store reports itself read-only

`bd delete ynab-mcp-new-cbd --force` in that repo fails with:

    Error: deleting issue: embeddeddolt: store is read-only

That is bd's own internal state, not a filesystem permission:
`.beads/embeddeddolt` is `drwx------` owned by the invoking user, and a shell
write into the directory succeeds. A read-only store is a single candidate
explanation for the entire pattern above — every whole-table read returning
zero while filtered queries return the rows — and it has never been tested.

It also subsumes the after-the-fact-creation observation instead of standing
beside it. If that `bd create` write never landed in committed dolt state,
then "the new issue is uncounted" measures the read-only condition, not a
separate export defect. Treat it as evidence *for* this hypothesis, not as a
second data point.

Embedded mode alone does not cause it. In a fresh embedded-dolt scratch repo
on the same bd 1.1.0, `bd create` followed by `bd delete <id> --force`
succeeds, `bd count` agrees with `bd list`, and `bd export` writes the issue.

Open: what puts a store into that state, and whether clearing it restores the
aggregate reads. Settling that needs the `rsync -a` scratch copy described
below — checking whether the copy also reports read-only, and what bd's
source keys the flag off. The session that found the error was barred from
touching the affected repo again, so it made no such copy and the hypothesis
stands untested.

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

Whether the read-only flag above is the cause — testable on an `rsync -a`
scratch copy, by finding what bd's source keys `store is read-only` off and
whether a copy with that condition cleared reads its own table again. Failing
that, which query each command issues, available from bd's source or by
migrating a **copy** to dolt server mode, where `bd sql` works, and running
the export's own query by hand. Do not migrate the live `ynab-mcp-new`
database, and do not write to it: whether to migrate it is an open human
decision (bd issue agentic-hty), and re-initializing it destroys the
evidence.

Worth reporting upstream. A report needs: bd 1.1.0 embedded mode, the
`bd list` / `bd count` disagreement on one database, the
`embeddeddolt: store is read-only` failure on any write to it, and that
`bd doctor` and `bd sql` are both unavailable in embedded mode so the
reporter cannot inspect further.

## Consequence, and the guard

`bd export` exits 0 on the empty write, so any automation trusting the exit
code commits an empty queue file over a real one — and the export is the
committed, portable representation of the queue that non-bd consumers read.
`hooks/bd-export-guard/pre-commit` refuses a commit whose staged
`.beads/issues.jsonl` holds zero issues while the database holds more than
zero. The condition is the mismatch, never the bare zero: a genuinely empty
database exports zero issues and commits normally.
