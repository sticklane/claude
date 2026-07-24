# Task 02: Rewrite the handoff-resume SessionStart hook to detect a bd-native handoff

Status: pending
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R3, R7)
Touch: hooks/handoff-resume/resume-check.sh, hooks/handoff-resume/test.sh, hooks/handoff-resume/README.md

## Goal

`hooks/handoff-resume/resume-check.sh` detects an open `handoff`-labeled
bd issue instead of globbing `HANDOFF*.md`, and tolerates both `bd`
unavailable on `PATH` and `bd` present but the repo has no `.beads/` —
both degrade silently (exit 0, no injected text).

## Touch

Do not touch `.claude/skills/handoff/` or `.claude/skills/resume-handoff/`
— task 01 owns those; this task only changes the detection hook and its
tests.

## Steps

1. Read `hooks/handoff-resume/resume-check.sh` in full (49 lines) and
   `hooks/handoff-resume/test.sh` (99 lines) to see the current fixture
   structure (it currently creates `HANDOFF*.md` files in a temp dir and
   asserts on the script's stdout).
2. Rewrite `resume-check.sh`: replace the `find ... -name 'HANDOFF*.md'`
   logic with `bd list --label handoff --status=open --json` (scoped to
   `$root`, e.g. `bd -C "$root" list --label handoff --status=open
   --json`). Verified 2026-07-24: running this outside any
   `.beads/`-containing directory already exits 0 with the error on
   stderr and empty stdout — treat empty/failed JSON parsing as "nothing
   found," not an error, so both the no-`.beads/` and `bd`-missing cases
   degrade free without a special-case branch (don't add `set -e`, and
   don't treat non-empty stderr as a signal). When one or more open
   `handoff`-labled issues are found, emit the same style of pointer
   text as today (single vs. multiple candidates), naming the issue
   id(s) instead of a file path.
3. Rewrite `hooks/handoff-resume/test.sh`'s fixtures to set up real bd
   state instead of writing `HANDOFF*.md` files: `hooks/bd-compliance/
   test.sh` is the precedent to follow (verified 2026-07-24) — it builds
   a scratch git repo + real bd store under `mktemp -d`, files a real
   issue via `bd`, and drives the hook against that scratch repo, never
   touching this toolkit's own `.beads` store. Do the same here: a
   scratch repo with a real `bd create ... --labels handoff` issue for
   the "found" cases, and `env PATH=...` restriction (same technique
   `hooks/bd-compliance/test.sh:91` uses) for the "bd unavailable" case.
   Keep the same test count/shape (single found, multiple found, none
   found, bd unavailable) plus one new case: `bd` present, no `.beads/`.
4. Update `hooks/handoff-resume/README.md` to describe the new detection
   mechanism.

## Acceptance

- [ ] `grep -c "HANDOFF" hooks/handoff-resume/resume-check.sh` → 0
- [ ] `grep -c "bd list --label handoff" hooks/handoff-resume/resume-check.sh` → ≥ 1
- [ ] `bash hooks/handoff-resume/test.sh` → all pass, exit 0
