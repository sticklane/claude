# Task 04: attended close-out — reinstall service, archive old repos

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- ATTENDED ONLY: this task mutates machine state (launchd) and external services (GitHub archive) and deletes working copies — it fails drain's peripheral/core gate. Run via /build in an attended session; do NOT dispatch it from /drain. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 03
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R5, R8)
Touch: none

## Goal

The machine and GitHub reflect the migration: `com.agent-console` runs
from the toolkit checkout (`~/claude/agent-console/agent-console.py`),
`sticklane/agentprof` and `sticklane/agent-console` are archived on
GitHub, and the old `~/agentprof` / `~/agent-console` working copies are
deleted. Nothing here changes repo files (Touch: none) — it is external
and machine state only, performed only after tasks 01–03 are green on
pushed `main`.

## Touch

No repo files. Everything below is launchd/GitHub/filesystem state
outside the repo. Get explicit human confirmation in-session before the
archive and delete steps — they are outward-facing / destructive.

## Steps

1. Verify precondition: tasks 01–03 merged and pushed
   (`git log origin/main --oneline -5` shows them; repo gates green).
2. Uninstall the old service (`bash ~/agent-console/uninstall.sh`), then
   `bash ~/claude/agent-console/install.sh` and confirm healthz.
3. Archive both GitHub repos: `gh repo archive sticklane/agentprof -y`
   and `gh repo archive sticklane/agent-console -y` (confirm with the
   human first).
4. Delete `~/agentprof` and `~/agent-console` (confirm with the human
   first; both must have no uncommitted/unpushed work — check before
   deleting).
5. Run the end-to-end check below.

## Acceptance

- [x] `launchctl print gui/$(id -u)/com.agent-console | grep -c "claude/agent-console"` → ≥1 — actual: 1
- [x] `curl -fsS http://127.0.0.1:8899/healthz` → ok — actual: ok
- [x] `gh repo view sticklane/agentprof --json isArchived -q .isArchived` → true — actual: true
- [x] `gh repo view sticklane/agent-console --json isArchived -q .isArchived` → true — actual: true
- [x] `test ! -d ~/agentprof && test ! -d ~/agent-console` → exit 0 — actual: exit 0, both absent
- [x] End-to-end: `curl -fsS http://127.0.0.1:8899/workboard` returns a page whose inbox rows name the same repos as `python3 ~/claude/.claude/skills/workboard/workboard.py --json` inbox items — actual: both list {claude, fooszone, hub, prioritize-fixture}
