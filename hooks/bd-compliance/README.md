# bd-compliance hook

A `Stop` hook blocking "done" while bd issues this session claimed are
still open (specs/beads-daily-skill/SPEC.md, "The compliance Stop hook").

`/work` appends a claimed issue's id to `.beads/session-claims` (one id
per line) before working it, removing the line on close
(`.claude/skills/work/SKILL.md` steps 2, 5). This hook: file absent/empty,
or every id shows `status: "closed"` via `bd show <id> --json` -> exit 0;
any id not confirmed closed -> exit 2, naming it. bd missing from `PATH`
is tolerated (exit 0, note only) — never brick a repo without bd.

**Work in flight.** A `/drain` orchestrator ends a turn every time it
awaits a dispatched worker, so its claims are open on purpose; closing
them would record a completion that never happened. It writes `<id>
<dispatched-at-epoch-seconds>` to `.beads/session-inflight` at dispatch and
drops the line when it collects the verdict, and this hook treats such an
id as satisfied while bd *also* reports it `in_progress`. The exemption is
per-id, needs bd's own status to corroborate it, and expires after
`BD_COMPLIANCE_INFLIGHT_TTL` seconds (default 3600) so a session that
crashes mid-dispatch leaves no lasting immunity.

Install as a `Stop` hook entry per `.claude/skills/gate/reference.md`.
Tests: `bash hooks/bd-compliance/test.sh`.
