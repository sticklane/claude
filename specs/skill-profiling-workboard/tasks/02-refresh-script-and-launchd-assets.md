# Task 02: refresh script, pprof wrapper, launchd templates

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: agentprof/scripts/, agentprof/launchd/

## Goal

The repo carries everything the attended install task needs, as files:
`agentprof/scripts/refresh-profile.sh` (builds/locates the agentprof
binary, runs `agentprof claude --days 30 -o ~/.local/state/agentprof/claude-30d.pb.gz`
atomically — write to a temp file, mv into place — creating the state dir
if absent), `agentprof/scripts/serve-pprof.sh` (execs
`go tool pprof -no_browser -http=127.0.0.1:8901 <profile>`; exits nonzero
with a clear message when the profile file is missing), and two launchd
plist templates under `agentprof/launchd/` —
`com.sjaconette.agentprof-refresh.plist.tmpl` (hourly StartInterval,
stdout/stderr under `~/Library/Logs/agentprof-refresh/`) and
`com.sjaconette.agentprof-pprof.plist.tmpl` (KeepAlive, logs under
`~/Library/Logs/agentprof-pprof/`). Templates only (`.tmpl`, matching the
agent-console convention) — NO launchctl calls, NO plist installed to
`~/Library/LaunchAgents`; the attended closeout task (05) does that.

## Touch

Only `agentprof/scripts/` and `agentprof/launchd/`. Do NOT touch
`agentprof/internal/` (task 01 owns it), `agent-console/` (task 03), or
any `.claude/` path. Scripts must not hardcode the username — derive HOME
at runtime; templates may carry a `__HOME__`-style placeholder the
installer substitutes (mirror agent-console's existing `.plist.tmpl`
pattern).

## Steps

1. Write `refresh-profile.sh` (set -euo pipefail; mkdir -p state dir;
   temp-file + mv for atomic replace; kickstart of the pprof service is
   the CALLER's job, not this script's — the workboard endpoint and
   launchd both invoke this script then handle their own restart).
2. Write `serve-pprof.sh`.
3. Write both plist templates.
4. Smoke-test both scripts locally without launchd: refresh produces a
   nonempty `.pb.gz`; serve-pprof against it responds on 8901 (curl, then
   kill it) — do NOT leave processes running.
5. `bash agentprof/scripts/check.sh` still green (shellcheck if the repo
   check includes it); run the personal-data sweep
   (`grep -rn "sjaconette\|Jaconette" agentprof/scripts/ agentprof/launchd/`
   must only hit the launchd label strings `com.sjaconette.*`, which are
   the documented standard — record the hits in evidence); commit.

## Acceptance

- [ ] `bash agentprof/scripts/refresh-profile.sh && test -s ~/.local/state/agentprof/claude-30d.pb.gz` → exit 0
- [ ] `bash agentprof/scripts/serve-pprof.sh & sleep 2; curl -s http://127.0.0.1:8901/ | head -c 200; kill %1` → pprof UI HTML fragment
- [ ] `ls agentprof/launchd/com.sjaconette.agentprof-refresh.plist.tmpl agentprof/launchd/com.sjaconette.agentprof-pprof.plist.tmpl` → both exist; `plutil -lint` passes on each after placeholder substitution (evidence shows the substitution used)
- [ ] `find agentprof -name "*.plist" ! -name "*.tmpl" | wc -l` → 0
- [ ] `cd agentprof && bash scripts/check.sh` → exit 0
