# Task 05: attended install + end-to-end verification

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- ATTENDED ONLY: this task mutates machine state (launchd services) — it fails drain's peripheral/core gate. Run via /build in an attended session; do NOT dispatch it from /drain. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01, 02, 03, 04
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R2, R3, R8 + all attended acceptance)
Touch: none

## Goal

Both launchd agents are installed and healthy (plist templates from task
02, placeholders substituted, loaded via `launchctl bootstrap gui/$UID`),
the profile file regenerates on schedule and via the workboard refresh
button, and the full user path works: workboard → session row link →
pprof flamegraph filtered to that session → `skill:` frames visible.
Evidence (including a screenshot) lands in
`specs/skill-profiling-workboard/evidence/`.

## Steps

1. Substitute placeholders, install both plists to `~/Library/LaunchAgents/`,
   `launchctl bootstrap` each, verify with `launchctl print`.
2. Restart the agent-console service so the new server code is live.
3. Run the attended acceptance checks below.
4. E2E: click through from the workboard. Seam to eyeball: agentprof's
   `session` label is the MAIN transcript's basename — a sub-agent
   session's row may filter to an empty flamegraph (samples fold under
   the parent). Verify a main-session row; note observed sub-agent
   behavior in evidence.
5. Screenshot → `specs/skill-profiling-workboard/evidence/`; commit
   evidence + this task's flip.

## Acceptance

- [ ] `launchctl print gui/$UID/com.sjaconette.agentprof-refresh | head -1` → exit 0
- [ ] `launchctl print gui/$UID/com.sjaconette.agentprof-pprof | head -1` → exit 0
- [ ] `curl -s http://127.0.0.1:8901/` → pprof UI HTML
- [ ] `curl -s http://127.0.0.1:8899/workboard | grep -c '127.0.0.1:8901'` → ≥ 1
- [ ] CSRF refresh check: extract `window.CSRF` from the workboard page, `curl -s -X POST -H "X-CSRF: $TOKEN" http://127.0.0.1:8899/api/profile/refresh` → `{"ok": true, ...}` and `~/.local/state/agentprof/claude-30d.pb.gz` mtime advances
- [ ] `go tool pprof -top ~/.local/state/agentprof/claude-30d.pb.gz 2>/dev/null | grep -c 'skill:'` → ≥ 1, with no bare `agentic:` skill frames (R1 live confirmation)
- [ ] R8: `git diff --stat <spec-base>..HEAD -- CLAUDE.md .claude/rules/` → empty and no `.claude/skills/*/SKILL.md` changes across the spec's merged tasks
- [ ] E2E screenshot exists in `specs/skill-profiling-workboard/evidence/` showing the session-filtered flamegraph with a `skill:` frame
