# Orchestrator Context: Drain & Co. Self-Manage Their Own Context

> **Provenance:** interview 2026-07-03. Steven: "drain and similar orchestration
> should self manage context, clearing and retriggering sometimes as needed —
> but compare this to best practices from all frontier model developers."
> Research: `docs/context-management-research-2026-07.md` (Anthropic sources
> 3-vote verified; other vendors unverified — see its caveats). Decisions:
> **self-relaunch headless** at safe boundaries; **task-count budget +
> degradation override** as the trigger; scope = **drain, autopilot, parallel,
> and the ultra-mode workflow templates**. Complements (does not modify)
> `specs/context-management/SPEC.md`, which covers compaction steering, memory
> indexing, and tool-call ceilings but explicitly not orchestrator relaunch.

## Problem

A drain run's queue state survives any session death (committed `Status:`
flips), but the orchestrator session itself only degrades: today drain's sole
guidance is "if this session grows heavy mid-queue, finish the in-flight task,
tell the user to `/clear` and re-run `/drain`" (drain/SKILL.md:85-87) — manual,
and dependent on a human noticing. The research confirms the failure mode is
real and gradual ("context rot": recall degrades before the hard limit) and
that compaction alone is insufficient for multi-context-window work — the
prescribed remedy is deliberate harness artifacts plus fresh-session relaunch,
with each fresh instance following a read-state-then-verify ritual. Autopilot
just stops at `--max-turns`; parallel's collection phase has no guidance at
all.

## Solution

Give each orchestrator a **baton-pass step**: at every safe boundary (a task
verdict recorded and committed), evaluate the trigger; when it fires, write a
mini-handoff, spawn a fresh detached instance of itself, report the pass, and
end. State never lives only in context (the research's "assume interruption"
rule) — the handoff artifact is small because task files already checkpoint
the queue.

- **Trigger** (research-calibrated): a deterministic **generation budget** —
  after N recorded verdicts in one session (default N=4, overridable per spec
  via a `Relaunch-every:` header next to the queue's other machine-state
  lines) — plus a **degradation override**: hand off early at the next
  boundary if the orchestrator notices itself re-reading files it already
  read, losing queue position, repeated failed corrections, or a compaction
  event. Proactive, never failure-triggered (degradation is a gradient; hand
  off before limits).
- **Handoff artifact**: `specs/<slug>/DRAIN-BATON.md` — done/next progress
  log (task ids + one-line outcomes this generation), generation number,
  in-flight anomalies (flagged tasks, deferred questions so far), and the
  exact relaunch command. NOT a transcript; ≤ half a page (the /handoff
  format, minus what task files already record).
- **Relaunch**: headless detached
  `claude -p "/drain <spec> (generation G+1, baton: <path>)"` in the repo,
  with the same headless flag set drain's reference already documents
  (permission mode, --max-turns). A **max-generations cap** (default 10)
  prevents runaway relaunch loops; hitting it stops with the baton written
  and a needs-attention note instead of respawning.
- **Fresh-instance ritual** (research finding: read state, then verify):
  generation G+1 reads the baton + task-file `Status:` lines + `git log
  --oneline -15` FIRST, then runs one cheap verification (the project's check
  command or the last flipped task's acceptance command) to catch undocumented
  drift, then resumes dispatching. On completion of the whole queue, the
  final generation deletes the baton file.

## Requirements

- R1: **drain** SKILL.md gains the baton-pass step (trigger, artifact,
  relaunch, cap) in ≤ 20 lines, with the exact relaunch command template and
  headless flags in reference.md (per the exact-config-goes-in-reference
  convention). The attended path stays available: when drain is running
  attended and the trigger fires, it offers the baton + command to the user
  instead of self-relaunching only if the user asked to stay attended;
  default is self-relaunch.
- R2: **autopilot**: on hitting `--max-turns` with the bounded goal unmet but
  progressing (goal evaluator says advancing, not stuck), the run writes the
  baton and relaunches (same cap); a stuck verdict still stops for spec
  repair as today. Documented in autopilot SKILL.md + reference.md.
- R3: **parallel**: the collect/merge phase gains the same boundary rule —
  if collection will outlive the session budget (many workers), merge what's
  verified, commit, write the baton listing unmerged branches, relaunch.
- R4: **ultra-mode templates** (`runtimes/claude-code.md`, per
  specs/ultra-mode): the drain/parallel workflow templates note that the
  MAIN session should treat a long workflow as its own baton boundary — the
  workflow's resume (scriptPath + resumeFromRunId) plus committed task state
  make the main session disposable; the template comments include the
  baton/relaunch pointer rather than duplicating the mechanism.
- R5: The baton grammar and the `Relaunch-every:` header are documented in
  breakdown's task-file/queue conventions so specs can tune N; absence means
  the default (4).
- R6: The workboard scanner treats a `DRAIN-BATON.md` like a handoff:
  surfaced on the board with its generation number and relaunch command
  (parses the file's header line; this rides on the scanner's existing
  handoff detection — no new sanctioned scanner change beyond a filename
  pattern).
- R7: Research + decisions recorded: `docs/decisions/orchestrator-context.md`
  captures the trigger design (N=4 + override), the cap, the
  Anthropic-verified basis (context rot, insufficient-compaction,
  read-state-then-verify), the vendor-coverage caveat (Anthropic-only), and
  links the research doc + this spec.
- R8: Repo conventions: antigravity mirror updated in the same commit (the
  baton step mirrors as a workflow note; Antigravity runs can't self-relaunch
  claude — the mirrored text says "write the baton and stop"), and
  `.claude-plugin/plugin.json` version bumped.

## Out of scope

- **Compaction steering, memory index, tool-call ceilings** — already owned by
  `specs/context-management/SPEC.md`.
- **Token-count introspection** — the trigger is verdict-count + self-observed
  signs; no attempt to read exact context size (not exposed to the session).
- **Worker-session context management** — workers are per-task fresh sessions
  by construction; nothing to do.
- **Auto-relaunch outside orchestrators** — /build and /idea keep the manual
  /handoff flow.
- **Cross-vendor calibration** — blocked on the unverified OpenAI/Google legs
  (research doc open question); revisit if that verifies later.

## Acceptance criteria

- [ ] drain SKILL.md: baton step present, ≤ 20 lines, names the default
      (every 4 verdicts), the override signs, and the cap (10); reference.md
      has the relaunch command template with headless flags
      (`grep -n "baton\|Relaunch-every\|generation" <files>`) (covers R1)
- [ ] autopilot + parallel SKILL.md each grep for "baton" with their
      respective boundary rules (covers R2, R3)
- [ ] `runtimes/claude-code.md` orchestration templates reference the baton
      boundary (grep "baton") — or, if ultra-mode hasn't landed, this item is
      recorded as a follow-on edit in ultra-mode's task list (covers R4)
- [ ] breakdown's conventions document `Relaunch-every:` (covers R5)
- [ ] A fixture `DRAIN-BATON.md` in a scanned repo appears on the workboard
      with generation + command (scanner unit test or rendered-HTML grep)
      (covers R6)
- [ ] `docs/decisions/orchestrator-context.md` exists, names N=4/cap 10 and
      the Anthropic-only caveat, links both docs (covers R7)
- [ ] Mirror + version bump present in the implementing commit(s) (covers R8)
- [ ] **End-to-end (fixture):** a drain run over a 6-task fixture spec with
      `Relaunch-every: 2` — using a stub relaunch command recorder in place of
      real claude — records 2 baton passes: each baton contains the done/next
      log and generation number; the stub's recorded argv is the documented
      relaunch command; after a simulated final generation, the baton file is
      deleted and all 6 tasks are done.

## Open questions

(none — trigger, mechanism, scope, and cap decided in interview; vendor
comparison caveat is recorded, not blocking)
