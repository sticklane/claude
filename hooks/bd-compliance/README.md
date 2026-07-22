# bd-compliance hook

A `Stop` hook blocking "done" while bd issues this session claimed are
still open (specs/beads-daily-skill/SPEC.md, "The compliance Stop hook").

`/work` appends a claimed issue's id to `.beads/session-claims` (one id
per line) before working it, removing the line on close
(`.claude/skills/work/SKILL.md` steps 2, 4). This hook: file absent/empty,
or every id shows `status: "closed"` via `bd show <id> --json` -> exit 0;
any id not confirmed closed -> exit 2, naming it. bd missing from `PATH`
is tolerated (exit 0, note only) — never brick a repo without bd.

Install as a `Stop` hook entry per `.claude/skills/gate/reference.md`.
Tests: `bash hooks/bd-compliance/test.sh`.
