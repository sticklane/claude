# Skill-level profiling, linked from the workboard — plus skill-doctrine guide docs

## Problem

Steven wants to see what his agentic skills actually cost — "what does
/drain cost me" — without spending a single conversation token to produce
or view that data. agentprof already turns Claude Code transcripts into
pprof flame graphs, already emits a per-line skill frame (from the
harness's `attributionSkill` field), and already links workflow subagents
via `wf_` run ids. What's missing: (a) nothing regenerates profiles
automatically; (b) skill frames are inconsistent — the same skill appears
both namespaced and bare (`agentic:build`: 852 samples vs `build`: 1260
on the live corpus), splitting its spend across two frames; (c) the
workboard UI (agent-console, port 8899) has no path from a session row to
its profile. Separately, the toolkit's research on context management,
correctness, and model routing lives in dense research dumps
(`docs/anthropic-playbook.md`, `docs/orchestration-research-2026-07.md`,
`docs/context-management-research-2026-07.md`) with no visual, linkable
guide layer.

## Solution

All zero-LLM: binaries, launchd, and stdlib server code — no model
inference anywhere in the pipeline, and no new always-loaded prompt text.

- **agentprof** (Go, `agentprof/` in this repo post-absorb) normalizes
  its existing skill frame: strip a leading `<plugin>:` namespace, render
  as `skill:<name>` so namespaced and bare invocations of the same skill
  collapse into one frame; the `(no skill)` default stays as-is. The
  frame is emitted where the current code places `r.skill` / `ctx.skill`
  (today `internal/claude/claude.go` ≈271–313; `attributionSkill` parsed
  ≈407, default ≈459). Skill-invocation parsing, last-skill-wins spans,
  and wf_ linkage are NOT built — they exist or are superseded by the
  harness's per-line attribution.
- **Generation** is hybrid: launchd agent `com.sjaconette.agentprof-refresh`
  runs `agentprof claude --days 30 -o ~/.local/state/agentprof/claude-30d.pb.gz`
  hourly; launchd agent `com.sjaconette.agentprof-pprof` serves
  `go tool pprof -no_browser -http=127.0.0.1:8901` over that file with
  KeepAlive. Both follow the local launchd standard (com.sjaconette.*
  labels, logs under `~/Library/Logs/<job>/`).
- **Workboard** (agent-console.py; routes in `do_GET`, POST handlers
  dict — re-derive exact lines after absorb task 02 merges, it rewrites
  this file) gets: a header "Profile" link to `http://127.0.0.1:8901/`;
  a per-session profile link on each session row using the pprof web
  UI's tagfocus URL param on the profile's existing `session` label —
  `http://127.0.0.1:8901/ui/flamegraph?tf=session=<sid>` (param verified:
  `tf` → tagfocus in pprof's `internal/driver/config.go:152`); and
  `POST /api/profile/refresh`, which regenerates the profile file and
  `launchctl kickstart -k`s the pprof service.
- **Docs**: three guide pages under `docs/guides/` — context-management,
  correctness, model-routing — each with at least one mermaid diagram,
  links into the in-repo research docs, and at least two primary-source
  links; a repo-local link checker keeps them honest.

All file:line anchors above are indicative (pre-absorb positions); the
implementing agent re-derives them in the post-absorb tree.

**Dependency:** the absorb-agent-tools queue (tasks 01–03) must be merged
first — this spec edits `agentprof/` and `agent-console/` at their
post-absorb in-repo locations. launchd install/reinstall steps are
machine-state mutations: attended-only (drain's peripheral/core gate),
like absorb task 04.

## Requirements

- R1: agentprof's skill frame is normalized: a leading `<plugin>:`
  namespace is stripped and the frame renders as `skill:<name>`;
  `agentic:build` and `build` samples land in ONE `skill:build` frame.
  Lines with no `attributionSkill` keep the existing `(no skill)` frame.
  Unit-tested against a fixture transcript containing the namespaced and
  bare forms of one skill plus unattributed lines.
- R2: launchd agent `com.sjaconette.agentprof-refresh` regenerates
  `~/.local/state/agentprof/claude-30d.pb.gz` hourly via a repo-checked
  script at `agentprof/scripts/refresh-profile.sh` (the path R5's
  handler also invokes); logs land under `~/Library/Logs/agentprof-refresh/`.
- R3: launchd agent `com.sjaconette.agentprof-pprof` serves the pprof web
  UI for that file on `127.0.0.1:8901` (`go tool pprof -no_browser
  -http=...`), KeepAlive, logs under `~/Library/Logs/agentprof-pprof/`;
  a repo-checked wrapper script restarts cleanly when the profile file
  is replaced.
- R4: the workboard page renders a header "Profile" link to
  `http://127.0.0.1:8901/` and one profile link per session row with
  href `http://127.0.0.1:8901/ui/flamegraph?tf=session=<sid>` (sid
  escaped via `esc()`, URL-encoded); links render even when the pprof
  server is down (plain anchors, no health gating).
- R5: `POST /api/profile/refresh` on agent-console, registered in the
  existing POST handlers dict (so it inherits the CSRF check and the
  shared response wrapper), invokes R2's repo-checked regeneration
  script (not an inline agentprof command) and kickstarts the pprof
  service, returning the wrapper's standard `{"ok": true, "message":
  ...}` on success and `{"ok": false, ...}` with non-200 on failure; the
  workboard page exposes it as a refresh control (client JS `acPost`,
  which already sends the `X-CSRF` header).
- R6: `docs/guides/context-management.md`, `docs/guides/correctness.md`,
  and `docs/guides/model-routing.md` exist; each contains ≥1 mermaid
  diagram, ≥1 link to an in-repo research doc, and ≥2 links to primary
  sources; each names the toolkit skills/rules it explains (e.g.
  token-discipline for model-routing).
- R7: a link checker (`scripts/check-doc-links.sh`) verifies every
  relative link in `docs/guides/` resolves to an existing file and every
  mermaid block is a fenced block with a non-empty body; wired into the
  repo's `scripts/check.sh`.
- R8: zero token overhead: the diff makes no additions to `CLAUDE.md`,
  `.claude/rules/`, or any `.claude/skills/*/SKILL.md` body. (Docs are
  informational; nothing new loads into session context.)

## Out of scope

- Skill-invocation parsing in agentprof (harness `attributionSkill`
  already attributes per line — better than any span heuristic).
- wf_ workflow linkage and `(unlinked)` reduction — already landed
  (`b411bfd feat: link workflow subagents via path runId and
  toolUseResult`); any residual `(unlinked)` gap is a separate spec.
- Inline spend columns/figures in workboard rows (link-out chosen instead).
- Serving the guide docs inside the console UI.
- Attribution changes for non-Claude sources (gcp, vertex, otel).
- Any hosting beyond 127.0.0.1; any auth; any remote publishing.
- SessionEnd hooks (rejected: fires too often, rescans the corpus).

## Acceptance criteria

- [ ] `cd agentprof && bash scripts/check.sh` passes, including the R1
      unit test (`go test ./internal/claude/ -run SkillFrame` or the
      implementer's chosen name, cited in evidence)
- [ ] R1 corpus spot-check: `go tool pprof -top` over a freshly built
      profile shows `skill:build` and NO bare `build` / `agentic:build`
      frames (record the -top excerpt in evidence)
- [ ] `launchctl print gui/$UID/com.sjaconette.agentprof-refresh` and
      `...agentprof-pprof` both succeed (attended task)
- [ ] `curl -s http://127.0.0.1:8901/` returns pprof UI HTML (attended task)
- [ ] agent-console's `scripts/check.sh` smoke test asserts ≥1
      `127.0.0.1:8901` anchor in the live-rendered workboard (header
      link), and a unit test in `tests/` renders `render_workboard`
      against a SYNTHETIC board fixture containing one session with a
      known sid and asserts its row anchor contains `?tf=session=<sid>`
      (the live smoke render may have zero active sessions — never
      assert per-row anchors against live data)
- [ ] Attended refresh check: fetch the workboard page, extract the
      per-process CSRF token (`window.CSRF`), then
      `curl -s -X POST -H "X-CSRF: $TOKEN" http://127.0.0.1:8899/api/profile/refresh`
      → `{"ok": true, ...}` and the profile file's mtime advances
- [ ] `bash scripts/check-doc-links.sh` passes; `ls docs/guides/` shows
      the three files; `grep -c '```mermaid' docs/guides/*.md` ≥ 1 each
- [ ] R8: `git diff <base>..HEAD -- CLAUDE.md .claude/rules/ '.claude/skills/*/SKILL.md'`
      is empty
- [ ] End-to-end (attended): open `http://127.0.0.1:8899/workboard`,
      click a session's profile link, land on the pprof flamegraph
      filtered to that session (tf param), and locate a `skill:` frame
      for a session known to have run a skill (e.g. this drain session);
      screenshot into `specs/skill-profiling-workboard/evidence/`.
      Seam to eyeball here: agentprof's `session` label is the MAIN
      transcript's basename — a workboard row for a sub-agent session
      may filter to an empty flamegraph (its samples fold under the
      parent session). Verify a main-session row, and note the sub-agent
      behavior observed in evidence.

## Open questions

(none)
