# Verification: 03-doctrine-and-playbook-citations

Verdict: PASS

## Acceptance commands (run from worktree root)

1. `grep -ci '3.5\|3–5\|3-5' .claude/rules/token-discipline.md` → **1** (≥1) — PASS
2. `grep -ci 'rolling top.up\|rolling top-up' .claude/rules/token-discipline.md` → **1** (≥1) — PASS
3. `grep -ci 'agent teams\|agent-teams' docs/external-playbooks.md` → **4** (≥1) — PASS
4. `grep -ci 'shared.contract\|shared contract' docs/external-playbooks.md` → **1** (≥1) — PASS

## Qualitative constraints

- **Additive, non-contradictory edit**: token-discipline.md's fleet-sizing
  bullet retains "One worker is the default; scale the fleet only for
  genuinely divisible groups..." unchanged, then appends the 3–5
  concurrent-writer window and rolling top-up guidance, closing with an
  explicit disclaimer: "This tightens the sizing guidance; it does not
  change the opt-in default above." — PASS, matches Step 4's cross-check.

- **Citation not restatement**: token-discipline.md ends the extended
  bullet with "The cross-vendor evidence for both the window and the
  rolling claim-next design is in docs/external-playbooks.md (cited, not
  restated)." No verbatim research quotes appear in token-discipline.md
  itself — PASS.

- **Five verbatim quotes in docs/external-playbooks.md**, new "##
  Concurrent writer fleets" section (lines 88–121), each with a source
  citation, matching the file's existing bold-label-then-quote-then-link
  per-entry format:
  - (a) agent-teams shared-task-list: "after finishing a task, a teammate
    picks up the next unassigned, unblocked task on its own" —
    [Agent teams] link present. PASS
  - (b) 3–5-teammate sweet spot: "Start with 3-5 teammates for most
    workflows… Three focused teammates often outperform five scattered
    ones"; "If you have 15 independent tasks, 3 teammates is a good
    starting point." — two source links present. PASS
  - (c) file-ownership: "Two teammates editing the same file leads to
    overwrites. Break the work so each teammate owns a different set of
    files" — [Agent teams] link. PASS
  - (d) serial-integration-everywhere: Devin's manager "monitors progress,
    resolves any conflicts, and compiles the results" plus the
    one-branch-per-task observation across Codex/Jules/Cursor. PASS
  - (e) Cognition's shared-contract: "Actions carry implicit decisions,
    and conflicting decisions carry bad results" — [Don't Build
    Multi-Agents] link. PASS
  All five verified verbatim against
  `specs/drain-rolling-window/SPEC.md`'s "## Research grounding" section.

- **Scope check**: `git diff --name-only main` from worktree root returns
  exactly:
  ```
  .claude/rules/token-discipline.md
  docs/external-playbooks.md
  ```
  No edits to docs/anthropic-playbook.md or any other `.claude/rules/`
  file — PASS, matches Touch list.

- **Append-only task-file check**: `git diff main -- specs/drain-rolling-window/tasks/03-doctrine-and-playbook-citations.md`
  produced **empty output** — the task file is byte-identical to main
  (Status still reads "in-progress", no checkboxes ticked, no evidence
  line added yet). This is within bounds per the verification brief
  (worker may not have flipped Status/boxes at verify time) — not a
  finding, just noted: the worker has not yet recorded its own
  Status/checkbox/evidence-citation update for this task.

## Gates

No repo-standard build/lint/test gate applies to this doc-only task (no
`scripts/check.sh` invoked by these two prose files; task Touch list is
limited to the two doctrine files, no code).

## Overall verdict: PASS

All four acceptance commands return ≥1 as required. Both qualitative
doctrine constraints (additive/non-contradictory framing, citation-not-
restatement) hold. All five verbatim quotes from SPEC.md's Research
grounding section are present in docs/external-playbooks.md with source
citations, in the file's existing format. No scope creep — only the two
Touch-listed files changed. No unauthorized edits to the task file itself.
