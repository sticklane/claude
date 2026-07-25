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
`BD_COMPLIANCE_INFLIGHT_TTL` seconds so a session that crashes mid-dispatch
leaves no lasting immunity.

**The block message never names the marker, deliberately.** A session that
claimed work and then abandoned it is already `in_progress` — claiming is
what set that — so the only thing between it and a pass is one append to
`.beads/session-inflight`. Printing that file name to the very session being
blocked would hand it a copy-pasteable self-exemption and turn the escape
hatch into a general bypass. The message advertises close, defer, and unclaim
only; a real `/drain` orchestrator writes the marker from its own dispatch
procedure and never needs to learn it here. `tests/test_bd_compliance_hook.sh`
asserts the absence. Do not add it back.

**The 3600s default TTL is a ceiling, not a timer to refresh.** The marker is
rewritten per dispatch, and an orchestrator blocked awaiting a worker cannot
refresh it mid-flight, so a single worker-plus-verifier round longer than the
TTL ages out its own marker and eats one false block before `stop_hook_active`
clears the loop. That is the accepted cost of bounding a crashed session's
immunity. Observed rounds run 370–960 seconds, so 3600 is roughly 4× the worst
case measured; a workload with longer rounds raises
`BD_COMPLIANCE_INFLIGHT_TTL` rather than removing the expiry.

Install as a `Stop` hook entry per `.claude/skills/gate/reference.md`.
Tests: `bash hooks/bd-compliance/test.sh`.
