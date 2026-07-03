# Persisted verification evidence

## Problem

The verifier's evidence — the commands it ran and what they printed —
lives only in its final message and dies with the session. Pull requests
then carry claims ("verified ✓") instead of proof. Both the Anthropic
playbook ("pull requests… verified end to end, it has screenshots for
me") and Antigravity's artifact model (docs/external-playbooks.md,
"Evidence artifacts") treat persisted evidence as what makes walk-away
trust possible.

## Solution

The verifier agent writes its full report to a committed evidence file
next to the spec, and /build's close-out commits it with the code. Files
touched: `.claude/agents/verifier.md`, `.claude/skills/build/SKILL.md`,
plus the antigravity verifier skill and build workflow mirrors.

## Requirements

- R1: `.claude/agents/verifier.md` instructs the agent to write its full
  report to `specs/<slug>/evidence/<task-file-basename>.md` (e.g. task
  `specs/x/tasks/03-auth.md` → `specs/x/evidence/03-auth.md`), creating
  the directory if needed. When verifying a bare SPEC.md (no task file),
  the path is `specs/<slug>/evidence/spec.md`. When no spec directory is
  derivable (ad-hoc invocation), skip the file and say so in the report.
- R2: the evidence file contains: verdict line, per-criterion entry with
  the exact command and an output tail (last ~10 lines, enough to show
  the result), gate results, and scope-creep findings — the same content
  as the message, not a second format. The chat message remains the
  summary; the file is the durable record.
- R3: `.claude/skills/build/SKILL.md` close-out commits the evidence file
  together with the code and task file, and the task file's per-criterion
  evidence lines cite the evidence file rather than duplicating output.
- R4: a re-verify overwrites the evidence file (latest verdict wins);
  stale PASS evidence from a failed earlier attempt must not survive a
  FAIL.
- R5: antigravity mirrors: the antigravity verifier skill writes the same
  file, and the build workflow commits it; the workflow notes that
  Antigravity's native walkthrough artifacts complement but don't replace
  the committed file (walkthroughs live in the Antigravity UI, not the
  repo).
- R6: under /drain, no drain-side change is required — the evidence file
  is committed on the worker's branch by /build's close-out and arrives
  via the merge; drain's SKILL.md gains one clause noting DONE merges
  carry the evidence file.

## Out of scope

- Screenshots or browser recordings (the verifier is CLI-only in v1;
  command output only).
- Evidence retention/pruning policy — files accumulate with the spec and
  are cleaned up when the spec directory is.
- plugin.json version (owned by the hardening-quick-wins spec).

## Acceptance criteria

- [ ] `grep -q "evidence/" .claude/agents/verifier.md` with the path rule and the ad-hoc skip rule present (R1)
- [ ] verifier.md names the required file contents: verdict, per-criterion command + output tail, gates, scope creep (R2)
- [ ] `grep -qi "evidence" .claude/skills/build/SKILL.md` in the close-out step, including the commit instruction (R3)
- [ ] verifier.md states re-verification overwrites the file (R4)
- [ ] `grep -qi "evidence" antigravity/.agents/skills/verifier/SKILL.md && grep -qi "evidence" antigravity/.agents/workflows/build.md` (R5)
- [ ] `grep -qi "evidence" .claude/skills/drain/SKILL.md` — one clause on merges carrying evidence (R6)
- [ ] End to end: run /build on a toy task in a scratch repo; after close-out, `ls specs/*/evidence/` shows the report and `git log --stat -1` shows it committed (manual until the eval harness covers /build).

## Open questions

(none)
