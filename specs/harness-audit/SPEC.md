# Harness audit: health check for an onboarded repo

Status: open
Priority: P3

## Problem

/onboard handles first contact (repo map, CLAUDE.md, allowlist, gates
offer) and /gate installs the check hooks — but nothing audits an
already-onboarded repo whose harness has drifted. Documented commands go
stale, Stop hooks point at checks that no longer exist, skills change
without evalsets, `docs/memory.md` diverges from `docs/memory/`, and
permission allowlists accrete entries nobody remembers granting. "The New
SDLC With Vibe Coding" (adopted-practice record in
docs/external-playbooks.md) closes its deployment checklist with exactly
this class of check — memory configured, permissions scoped, eval
coverage measured, regression suite wired — and the toolkit has no
equivalent for the harness it installs.

## Solution

A read-only audit that checks an onboarded repo against a fixed checklist
and emits a ranked findings report — never auto-fixes:

1. **Command currency** — every command CLAUDE.md/AGENTS.md documents as
   verified still runs (exit 0 or a documented expected failure).
2. **Gate coverage** — if gates are installed, the Stop hook and
   pre-commit layer reference checks that exist and pass on a clean tree;
   if not installed, say so once, not as a finding per file.
3. **Evalset presence** — toolkit-style repos: skills changed since the
   last eval run (or with no evalset at all) are listed.
4. **Memory hygiene** — `docs/memory.md` index entries all resolve to
   files and vice versa; stale-dated entries flagged.
5. **Allowlist drift** — permission entries granted but unused in recent
   transcripts, and prompts that recur without an entry.

Output: a ranked findings list (blocking → advisory) written to the
session, with each finding naming the file and the one-line fix. The
next pipeline step for a finding is a normal task/spec, not an in-audit
edit.

Delivery shape — /onboard re-run mode vs. a new skill — is an open
question for /critique; the checklist above is the contract either way.

## Requirements

- R1: Read-only: the audit makes no edits, installs nothing, and states
  that contract in its skill text.
- R2: The five checklist areas above are each checked and each produce
  either findings or an explicit "clean" line — silent skips are the
  failure mode this exists to catch.
- R3: Findings are ranked (blocking → advisory) and name file + fix.
- R4: Mechanical checks (command runs, file-existence greps) dispatch
  scout-tier per token-discipline's dispatch-authoring rules; only the
  ranking/synthesis step uses the session model.
- R5: Antigravity mirror + plugin.json bump ride some task's `Touch:`
  (CLAUDE.md's mirroring convention).

## Out of scope

- Auto-fixing anything it finds — findings feed the normal pipeline.
- Production-runtime monitoring or drift detection of deployed agents —
  outside a dev toolkit (the standing scope line in
  docs/external-playbooks.md's "Considered and rejected").
- Scoring/grading the repo — a ranked findings list, not a health score.

## Acceptance criteria

- [ ] Skill text states the read-only contract (R1):
      `grep -qi "read-only" <the shipped skill/mode file>`.
- [ ] All five checklist areas named in the skill text (R2):
      `grep -qi "allowlist" ... && grep -qi "memory" ...` etc.
- [ ] Fresh-session test on this repo with one seeded defect (a fake
      stale command in a scratch CLAUDE.md copy): the audit reports it
      as a finding with file + fix, and edits nothing (`git status`
      clean afterward) (R1–R3, manual per CLAUDE.md's testing
      convention).
- [ ] plugin.json version higher than before; antigravity mirror present
      (R5).

## Open questions

- /onboard re-run mode or standalone skill — decide at /critique (a new
  skill needs no plugin.json skills-manifest edit; a new _agent_ would).
