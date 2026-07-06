# Task 05: attended install + end-to-end verification

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- ATTENDED ONLY: this task mutates machine state (launchd services) — it fails drain's peripheral/core gate. Run via /build in an attended session; do NOT dispatch it from /drain. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02, 03, 04
Priority: P1
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

- [x] `launchctl print gui/$UID/com.sjaconette.agentprof-refresh | head -1` → exit 0 — actual: exit 0, `gui/501/com.sjaconette.agentprof-refresh = {`
- [x] `launchctl print gui/$UID/com.sjaconette.agentprof-pprof | head -1` → exit 0 — actual: exit 0, `gui/501/com.sjaconette.agentprof-pprof = {`
- [x] `curl -s http://127.0.0.1:8901/` → pprof UI HTML — actual: 307 to `/ui`, `curl -sL` confirms real UI HTML (matches task 02's documented redirect behavior)
- [x] `curl -s http://127.0.0.1:8899/workboard | grep -c '127.0.0.1:8901'` → ≥ 1 — actual: 2
- [x] CSRF refresh check — actual: `{"ok": true, "message": "profile refreshed; pprof kickstarted"}`, mtime advanced 1783308477 → 1783308527
- [x] `go tool pprof -top ~/.local/state/agentprof/claude-30d.pb.gz 2>/dev/null | grep -c 'skill:'` → ≥ 1, no bare `agentic:` frames — actual: 8 `skill:` frames, 0 bare `agentic:` frames
- [x] R8: `git diff --stat <spec-base>..HEAD -- CLAUDE.md .claude/rules/` → empty and no `.claude/skills/*/SKILL.md` changes across the spec's merged tasks — actual: this spec's own 10 commits (a050b54..46d9ae5) touch neither; the broader HEAD diff picks up unrelated concurrent specs' work, correctly excluded from scope
- [x] E2E screenshot exists in `specs/skill-profiling-workboard/evidence/` showing the session-filtered flamegraph with a `skill:` frame — actual: `specs/skill-profiling-workboard/evidence/e2e-flamegraph.png`, session cde638f5-a2fa-4da8-bf3a-62ff2f4eb42e, shows `skill:code-review` frame
