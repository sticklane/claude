# Task 07 (draft): antigravity build.md exceeds documented workflow char cap

Status: draft
Depends on: none
Spec: ../SPEC.md

## Original report

> `antigravity/.agents/workflows/build.md` is now 13,372 chars, over the
> 12,000-char antigravity workflow cap stated in `antigravity/README.md` —
> but it was already 12,019 (over) before this task, so the required
> fold-in (AC2/AC3) cannot coexist with the cap without deleting
> pre-existing procedure (forbidden by mirror-procedure-discipline). A
> follow-up may want to re-home build.md's "## Ultra path" reference note
> or revisit whether the 12,000 figure is current; matters because content
> past the cap is silently dropped by Antigravity's Agent Manager at load
> time.

## Acceptance

Baseline (verified 2026-07-19): `wc -c` of
`antigravity/.agents/workflows/build.md` is 15,437 — grown past the
13,372 in the report — and its `## Ultra path` tail section is 493
chars, so re-homing that note alone can no longer reach 12,000; the
resolution is one of the two paths below, each with its own checks.

Path A — fit the documented cap:

- [ ] `[ "$(wc -c < antigravity/.agents/workflows/build.md)" -le 12000 ]`
      exits 0 (fails today at 15,437, verified 2026-07-19).
- [ ] `bash tests/test_mirror_procedure_coverage.sh` exits 0 (green
      today, verified 2026-07-19) — trimmed/re-homed content must not
      drop a seeded procedure phrase (e.g. the manifest's "Two triggers
      escalate to a human" line for this file), and any procedure moved
      out lands in a real file build.md points at, never deleted
      (`.claude/rules/mirror-procedure-discipline.md`).

Path B — the 12,000 figure is stale:

- [ ] `antigravity/README.md`'s cap sentence is corrected to the
      re-verified current cap with its source named inline:
      `grep -c '12,000 characters' antigravity/README.md` → 0 (1 today,
      verified 2026-07-19), and
      `wc -c < antigravity/.agents/workflows/build.md` does not exceed
      the newly documented figure. Re-verifying the real cap requires
      exercising Antigravity's Agent Manager — a drained worker marks
      that half manual-pending with the reason stated
      (`.claude/rules/mirror-verification.md`'s escape;
      docs/memory/unattended-worker-tool-limits.md).

Depth ceiling: char-count and grep checks are artifact-structure (L1) —
the behavioral complement is a manual-pending human load of build.md in
Antigravity's Agent Manager confirming the workflow loads untruncated
(the silent-drop failure the cap exists to prevent).
