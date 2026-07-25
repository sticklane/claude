# bd-export-guard hook

A `pre-commit` hook refusing a commit whose staged `.beads/issues.jsonl`
holds zero issues while the bd database holds more than zero (bd issue
agentic-kts).

`bd export` can write an empty file, print "Exported 0 issues", and exit 0
against a database `bd list` reports as populated — observed in
`/Users/sjaconette/ynab-mcp-new` on bd 1.1.0, with the investigation in
[docs/memory/bd-empty-export.md](../../docs/memory/bd-empty-export.md). The
exported JSONL is the committed, portable copy of the queue every non-bd
consumer reads, and this repo's `.beads/config.yaml` sets `export.auto: true`
so the bd pre-commit hook regenerates and stages it on every commit. Nothing
between that export and the remote reads the file's contents, so a silent
empty write lands as a committed empty queue.

**The condition is the mismatch, not the bare zero.** A repository whose bd
database is genuinely empty exports zero issues correctly and commits
normally; only "export says zero, database says more than zero" refuses.
The database count comes from `bd list --all --limit 0 --json`, which counts
every status — the filtered-query path that still returns rows in the
affected repo, deliberately not `bd count`, which reports zero there.

A staged *deletion* of the export counts as an export of nothing and refuses
the same way.

Anything the guard cannot establish — no `bd` on `PATH`, no repository, a
count it cannot parse — allows the commit. A hook that refuses on its own
uncertainty only teaches the operator to bypass it.

Escape hatches, both printed in the refusal:

    BD_EXPORT_GUARD=0 git commit ...   # this commit only
    git commit --no-verify ...         # skips every pre-commit hook

`BD_EXPORT_GUARD_PATH` overrides the guarded path for a repo that exports
somewhere other than `.beads/issues.jsonl`.

Wiring: `.beads/hooks/pre-commit` (this repo's `core.hooksPath`) chains it
inside an `AGENTIC BD-EXPORT-GUARD` marker block placed after the beads
block, which is what stages the export being checked.

Tests: `bash tests/test_bd_export_guard_hook.sh`.
