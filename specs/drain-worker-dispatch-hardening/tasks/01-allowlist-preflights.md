# Task 01: Allowlist pre-flights for headless dispatch and baton self-relaunch

Status: in-progress
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

Drain's headless-dispatch step and its baton self-relaunch step each gain
an explicit pre-flight check that runs _before_ dispatching, so a missing
tool or a stale orchestrator allowlist surfaces as a caught gap instead of
a live BLOCKED verdict burning a whole worker run.

## Touch

Both edits land in `.claude/skills/drain/reference.md`: the worker-allowlist
pre-flight in the "Headless fallback" section (near the `--allowedTools`
placeholder at reference.md:924), and the orchestrator-allowlist pre-flight
in the "## Baton pass (self-relaunch)" section itself (reference.md:949-1126),
next to the ORCHESTRATOR allowlist literal in its "Relaunch command
template" subsection (~reference.md:1059-1085, literal at ~1079). Note:
a `## Anomalies` heading appears nearby at ~1017, but it sits inside a
fenced ` ```markdown ` illustration of a DRAIN-BATON.md file's contents
(the fence spans ~997-1021) — it is example template content, not a real
reference.md section heading; the actual next section after Baton pass is
"## Critique intake" at ~1127. Don't be misled by that fenced heading
into placing the pre-flight outside the Baton-pass section. These are two
distinct checks over two distinct allowlists — don't merge them into one
paragraph or one check.

`antigravity/.agents/workflows/drain.md` mirrors both of these
reference.md sections (confirmed at SPEC.md's Mirror obligations — it
carries the same worker-prompt/Baton-pass content). Port both pre-flight
additions into their corresponding sections there in the same commit.

Do not touch `.claude/skills/drain/SKILL.md`, `runtimes/claude-code.md`,
or `.claude/skills/breakdown/SKILL.md` — those are sibling tasks' scope.

## Steps

1. Read `.claude/skills/drain/reference.md`'s "Headless fallback" section
   in full, and the "## Baton pass (self-relaunch)" section's "Relaunch
   command template" subsection in full — note the exact allowlist
   strings at each (the per-task WORKER allowlist near line 924, the
   ORCHESTRATOR allowlist literal near line 1079). Confirm for yourself
   that the literal sits inside "## Baton pass (self-relaunch)" (the
   section runs 949-1126) — a `## Anomalies` heading near line 1017 is
   fenced illustration content inside a code block, not a real section
   boundary; don't let it mislead you into thinking the section ends
   before the literal.
2. In "Headless fallback", add a pre-flight step stated as running before
   the generation's first `claude -p` invocation: scan the pending tasks'
   acceptance-criteria commands for the tool/command names they invoke,
   confirm each is covered by the `--allowedTools` string about to be
   used, and widen the list before dispatching if not. Use the literal
   phrase "validate its allowlist against" somewhere in this addition (the
   spec's acceptance criterion greps for it).
3. Next to the ORCHESTRATOR allowlist literal in the "Relaunch command
   template" subsection (inside "## Baton pass (self-relaunch)"), add a
   pre-flight step stated as running before self-relaunching: confirm
   that allowlist still carries `Task`, `Bash(git *)`, and the repo's
   actual project gate/lint/test command(s) — a fixed, repo-level check,
   not a per-task tool scan (the orchestrator dispatches workers rather
   than running their acceptance commands itself).
4. Port both additions into `antigravity/.agents/workflows/drain.md`'s
   corresponding sections, adapted to that runtime's own dispatch
   mechanism per `.claude/rules/mirror-procedure-discipline.md` (same
   steps, same order, same stated conditions — a runtime-forced wording
   difference is fine, a dropped step is not).
5. Commit.

## Acceptance

- [ ] `grep -c "validate its allowlist against" .claude/skills/drain/reference.md` → at least 1
- [ ] `grep -n "Headless fallback" .claude/skills/drain/reference.md` shows the new pre-flight text appears before the existing `--allowedTools` invocation line, not after
- [ ] inspect by hand: the orchestrator-allowlist pre-flight sits next to the ORCHESTRATOR allowlist literal in the "Relaunch command template" subsection inside "## Baton pass (self-relaunch)", and names `Task`, `Bash(git *)`, and a project check command — not a single grep-able literal, since the surrounding text already contains all three tokens today
- [ ] `grep -n "validate its allowlist\|self-relaunching" antigravity/.agents/workflows/drain.md` shows both pre-flights ported
