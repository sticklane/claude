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
> indexing, and tool-call ceilings but not orchestrator relaunch. Both specs
> edit the drain skill files — per QUEUE.md's serial-chain rule this spec is
> sequenced AFTER context-management's drain-touching tasks.

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
  after N recorded verdicts in one session (default N=4, overridable via a
  `Relaunch-every: N` header in the drained spec's SPEC.md header block — one
  per-spec location; task files keep only their existing per-task headers) —
  plus a **degradation override**: hand off early at the next
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
  with a **new orchestrator flag set** defined by this spec (NOT drain's
  existing headless-worker flags, which deliberately exclude the Task tool
  and would abort the orchestrator's first dispatch): agent/Task dispatch
  allowed, allowlist covering worktree merges and project gates, plus
  --max-turns. **Mandatory verification step:** whether a headless `-p`
  session supports background-agent dispatch with completion notifications
  must be verified live before this ships — every existing headless template
  in the toolkit is deliberately single-agent. If it does not, relaunched
  generations dispatch workers via drain's documented headless-worker
  fallback (sequential `claude -p` workers) instead — same queue semantics,
  slower. A **max-generations cap** (default 10) prevents runaway relaunch
  loops; hitting it stops with the baton written and a needs-attention note
  instead of respawning. A headless generation that reaches drain's
  batch-interview stage (queue drained to deferred-only) cannot interview:
  it writes the deferred-questions summary into the baton as a
  needs-attention section and stops — the workboard surfaces it (R6).
- **Fresh-instance ritual** (research finding: read state, then verify):
  generation G+1 reads the baton + task-file `Status:` lines + `git log
  --oneline -15` FIRST, then runs one cheap verification (the project's check
  command or the last flipped task's acceptance command) to catch undocumented
  drift, then resumes dispatching. On completion of the whole queue, the
  final generation deletes the baton file.

## Requirements

- R1: **drain** SKILL.md gains the baton-pass step (trigger, artifact,
  relaunch, cap, fresh-instance ritual) in ≤ 20 lines, with the exact
  relaunch command template and the NEW orchestrator flag set in reference.md
  (per the exact-config-goes-in-reference convention), including the recorded
  result of the background-dispatch verification above. Attended opt-out:
  generation 1 is always attended (drain is human-launched); passing the word
  `attended` in the /drain invocation makes every trigger offer the baton +
  relaunch command to the user instead of self-relaunching. Without it,
  gen-1 self-relaunches by default and MUST end its own turn immediately
  after spawning gen-2 with an explicit statement that this session is done
  and will not touch the queue again (preserving the one-writer invariant).
- R1a: **Fresh-instance ritual** (research: read state, then verify): a
  relaunched generation's first acts are (1) read the baton, (2) read the
  task files' `Status:` lines, (3) `git log --oneline -15`, (4) run one
  cheap verification command (the project check or the last-flipped task's
  acceptance command) — only then dispatch. In SKILL.md's ≤ 20 lines.
- R2: **autopilot**: pre-emptive, not post-cap (hitting `--max-turns`
  terminates the process — there is no after; and the /goal evaluator judges
  only condition-met, not progress): the launched run is instructed to write
  the baton and relaunch at its last safe boundary BEFORE the turn cap
  (e.g. at ~80% of --max-turns), judging its own advancement by new commits
  since launch; no new commits since the previous baton → stop for spec
  repair as today instead of respawning. Documented in autopilot SKILL.md +
  reference.md (same generations cap).
- R3: **parallel**: the collect/merge phase gains the same boundary rule —
  if collection will outlive the session budget (many workers), merge what's
  verified, commit, write the baton listing unmerged branches, relaunch.
- R4: **ultra-mode templates** (`runtimes/claude-code.md`, per
  specs/ultra-mode): the drain/parallel workflow templates note that the
  MAIN session should treat a long workflow as its own baton boundary — the
  workflow's resume (scriptPath + resumeFromRunId) plus committed task state
  make the main session disposable; the template comments include the
  baton/relaunch pointer rather than duplicating the mechanism. If ultra-mode
  is unimplemented when this lands, the pointer is recorded as an amendment
  note in ultra-mode's SPEC.md itself (it has no tasks/ dir).
- R5: The baton grammar and the `Relaunch-every:` header are documented in
  breakdown's task-file/queue conventions so specs can tune N; absence means
  the default (4).
- R6: The workboard scanner surfaces `DRAIN-BATON.md` files: generation
  number, relaunch command, and any needs-attention/deferred section, with
  baton-appropriate card text (NOT the handoff card's "resume in a fresh
  session then delete" prompt). This is a real, small scanner change
  (scan_handoffs globs the literal HANDOFF.md and extracts only a title) —
  it is the third sanctioned scanner change, after workboard-live R2a and
  unblock-next-steps R5.
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
      (every 4 verdicts), the override signs, the cap (10), and the
      read-state-then-verify ritual; reference.md has the relaunch command
      template with the orchestrator flag set AND the recorded verdict of the
      background-dispatch verification
      (`grep -n "baton\|Relaunch-every\|generation\|verif" <files>`)
      (covers R1, R1a)
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
      `Relaunch-every: 2` in its SPEC.md header. Stub mechanism (defined, not
      improvised): the relaunch step honors a `DRAIN_RELAUNCH_CMD` env
      override — the fixture sets it to a recorder script; fixture workers
      are also stubbed (task files carry trivial acceptance commands so
      verdicts flip without real worker sessions). Assert: 2 baton passes
      recorded; each baton contains the done/next log + generation number;
      the recorder's argv matches the documented relaunch command; the
      stubbed gen-2 log shows the ritual ran (baton read + verification
      command executed) before any dispatch; after the final generation the
      baton file is deleted and all 6 tasks are done (covers R1, R1a, R5,
      e2e).

## Open questions

(none — trigger, mechanism, scope, and cap decided in interview; vendor
comparison caveat is recorded, not blocking)

## Amendments

- **2026-07-03** — The OpenAI/Google context-management leg (see Out of
  scope: "Cross-vendor calibration — blocked on the unverified OpenAI/Google
  legs") has since verified (docs/context-management-research-2026-07.md,
  "Follow-up findings (2026-07-03)"). No mechanism changes: OpenAI's explicit
  criterion — trim/clear when turns are independent, summarize only when
  decisions/IDs/constraints must survive — corroborates relaunching at task
  boundaries, since drain's decisions live in committed task files, not in
  context. R7's decisions doc should record cross-vendor corroboration
  (Anthropic + OpenAI + Google) in place of the now-stale "Anthropic-only"
  vendor-coverage caveat; the remaining gap is the leg-B Anthropic
  re-verification items (still unverified after two attempts).
