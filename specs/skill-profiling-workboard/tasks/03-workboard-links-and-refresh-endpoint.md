# Task 03: workboard profile links + refresh endpoint

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirements R4, R5)
Touch: agent-console/

## Goal

The workboard page carries a header "Profile" link to
`http://127.0.0.1:8901/` and a per-session-row profile link with href
`http://127.0.0.1:8901/ui/flamegraph?tf=session=<sid>` (sid `esc()`-escaped
and URL-encoded; plain anchors, rendered even when the pprof server is
down). `POST /api/profile/refresh` is registered in the existing POST
handlers dict (inheriting the CSRF check and the shared
`{"ok": ..., "message": ...}` response wrapper); it invokes
`agentprof/scripts/refresh-profile.sh` (path pinned by the spec — resolve
repo root relative to the server file, same pattern as the skill-tree
resolution) and then `launchctl kickstart -k gui/$UID/com.sjaconette.agentprof-pprof`,
tolerating kickstart failure when the service isn't installed (still
`ok: true` if regeneration succeeded, with the kickstart result in
`message`). The workboard page exposes a refresh control wired through the
existing `acPost` JS helper.

## Touch

Only `agent-console/`. The per-row href goes in via `viz.timeline`'s
existing optional per-row `href` key — thread `sid` into the row dicts in
agent-console.py; do NOT modify `.claude/skills/_shared/viz.py` or
`.claude/skills/workboard/workboard.py` (out of bounds; if the seam truly
can't be crossed without editing them, stop with verdict DEFERRED and say
exactly why). Note the refresh script (task 02) may not exist on this
branch — the endpoint resolves its path at request time; unit tests stub
the subprocess call, they do NOT execute the real script.

## Steps

1. Failing tests first, in `agent-console/tests/`: (a) a SYNTHETIC board
   fixture containing one session with a known sid rendered through
   `render_workboard` asserts the row anchor contains `?tf=session=<sid>`
   and the page contains the `127.0.0.1:8901` header link — never assert
   per-row anchors against live data; (b) the refresh handler returns the
   wrapper shape on success/failure with subprocess stubbed.
2. Thread `sid` + `href` into the session timeline rows; add the header
   link.
3. Register `/api/profile/refresh` in the handlers dict; wire the UI
   button via `acPost`.
4. `bash agent-console/scripts/check.sh` green; commit.

## Acceptance

- [ ] `python3 -m unittest discover -s agent-console/tests -v` → new tests pass (fixture-board anchor test + refresh-handler test named in evidence)
- [ ] `bash agent-console/scripts/check.sh` → exit 0
- [ ] `grep -c '127.0.0.1:8901' agent-console/agent-console.py` → ≥ 1; `grep -c 'tf=session=' agent-console/agent-console.py` → ≥ 1; `grep -c 'profile/refresh' agent-console/agent-console.py` → ≥ 1
- [ ] `git diff --stat main -- .claude/skills/` → empty
