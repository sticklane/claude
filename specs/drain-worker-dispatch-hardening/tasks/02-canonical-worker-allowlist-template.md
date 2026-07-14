# Task 02: Canonical worker allowlist template

Status: in-progress
Depends on: 01
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirement R2)
Touch: runtimes/claude-code.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

One canonical, tool-complete WORKER allowlist template for compute-heavy
specs (`go`, `bash`, `npm`, `python3`, `git` at minimum) exists in
`runtimes/claude-code.md`'s `## Headless` section, and drain's Headless
fallback section references it by name instead of restating an allowlist
ad hoc.

## Touch

Depends on task 01 landing first: both tasks edit the same "Headless
fallback" section of `reference.md` (01 adds a pre-flight paragraph, this
task replaces the bare allowlist placeholder with a named reference) —
serialize to avoid stacking conflicting edits on the same lines. This
task's scope is the per-task WORKER allowlist only; the ORCHESTRATOR
allowlist (task 01's pre-flight next to the Relaunch command template,
reference.md:~1059-1085) is out of scope here.

Closure-time check (not this task's job, but flag it): the "canonical
worker allowlist" phrase this task ports into
`antigravity/.agents/workflows/drain.md` will reference a template that
lives only in `runtimes/claude-code.md` — a Claude-runtime-specific file
with no antigravity equivalent. Confirm at task 05's closing sweep (or
sooner, if you notice it here) that this reference resolves sensibly for
an antigravity reader rather than pointing at a file antigravity has no
reason to open; per `.claude/rules/mirror-verification.md` a phrase-grep
passing is not the same as the cross-reference actually resolving.

## Steps

1. Read `runtimes/claude-code.md`'s `## Headless` section (the file that
   already defines the `<allowlist>` placeholder shape used elsewhere).
2. Add a canonical, tool-complete WORKER allowlist template there for
   compute-heavy specs, covering at minimum `go`, `bash`, `npm`,
   `python3`, `git`, following the existing
   `Bash(<verified test/lint/build cmds>)` placeholder convention. Use the
   literal phrase "canonical worker allowlist" in this addition (the
   spec's acceptance criterion greps for it in both this file and
   reference.md).
3. In `.claude/skills/drain/reference.md`'s "Headless fallback" section
   (reference.md:~924's ad hoc `--allowedTools` placeholder), replace the
   restated allowlist with a reference to the new canonical template by
   name — also using the literal phrase "canonical worker allowlist".
4. Port the reference.md change into `antigravity/.agents/workflows/drain.md`'s
   corresponding Headless-fallback-equivalent section.
5. Commit.

## Progress

- [2026-07-14 /drain gen 3] Suspected zombie (bounded escalation). Re-ran
  the Stale-lock liveness check: `TaskList` shows no harness-tracked worker
  for this task in this session (session-local signal only, not evidence of
  another session's activity). Worktree `.claude/worktrees/agent-aada71f1f77b3d13c`
  is still checked out on `task/02-canonical-worker-allowlist-template`
  (tip `804d8ef`, committer time 2026-07-13T21:55:35-05:00 ≈ 8h before this
  check) with uncommitted dirty changes to `runtimes/claude-code.md`,
  `.claude/skills/drain/reference.md`, and this task file — real partial
  progress, never committed. No file mtime in the worktree is newer than 30
  min ago. Per the foreign-reclaim tightening, a live worktree blocks sweep
  regardless of staleness, so this is NOT swept.
  This is the THIRD independent generation to observe this exact same stale
  state with zero new activity (gen 1 first parked it; gen 2 re-confirmed at
  ~2h stale; this generation re-confirms at ~8h stale) — aggregate elapsed
  real time since last activity vastly exceeds the 4×15-min bounded-escalation
  threshold, even though no single session executed four literal
  sleep-and-recheck cycles in place (idle-sleeping ~1h to mechanically satisfy
  the counter would contradict this toolkit's own sleep/wake-economics
  discipline when the answer — no new activity across 8h and 3 independent
  checks — is already unambiguous). Escalating now: this task is a suspected
  zombie, leaves the parked set, and is treated like `blocked` for this
  generation's exhaustion trigger and final report. `Status:` stays
  `in-progress` per the zombie-escalation contract; the worktree and branch
  are left untouched (no sweep, no deletion) — a human should inspect
  `.claude/worktrees/agent-aada71f1f77b3d13c` and either resume/commit that
  work or clear it so a future drain generation can reclaim the task.

- [2026-07-14 /drain gen 5] Re-confirmed: worktree still checked out on
  `task/02-canonical-worker-allowlist-template` at the SAME tip `804d8ef`,
  same 3 dirty files, zero new activity across two more full generations
  (gen 4 re-confirmed byte-identical state per its own baton entry; this
  generation's own check again finds no drift and no live agent process
  attached via `claude agents --json`). Fourth independent generation to
  observe this exact stale state. Not re-swept (worktree still present with
  real uncommitted work — the mechanical sweep precondition of no checked-out
  worktree is not met). Not re-litigated further per gen 3/4's established
  reasoning; recommendation unchanged: a human should inspect
  `.claude/worktrees/agent-aada71f1f77b3d13c` directly.

## Acceptance

- [ ] `grep -c "canonical worker allowlist" runtimes/claude-code.md` → at least 1
- [ ] `grep -c "canonical worker allowlist" .claude/skills/drain/reference.md` → at least 1
- [ ] `grep -n "allowedTools" .claude/skills/drain/reference.md` (Headless fallback section) shows a reference to the named template, not a re-listed ad hoc tool string
- [ ] `grep -c "canonical worker allowlist" antigravity/.agents/workflows/drain.md` → at least 1
