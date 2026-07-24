# bd-native session handoffs

## Problem

`/handoff` and `/resume-handoff` park and resume session state as a
free-standing `HANDOFF.md` prose file, with a `Tracked:` header line
pointing at whichever bd issues the open work already has. This grew from
two decisions made under different premises two days apart:
`docs/task-tracking-design-research-2026-07.md` (2026-07-21) adopted the
compact-header technique into markdown specifically *because* its stated
constraint at the time — "git stays the sole source of truth, no external
dependency introduced" — ruled out adopting bd itself. The
2026-07-22/23 agentic-core-redesign pivot reversed that constraint (bd is
now this repo's authoritative tracker, per CLAUDE.md's "Beads issue
tracker" section), but `/handoff` only got a `Tracked:` field bolted onto
the existing file-first design — nobody redesigned the mechanism bd-first.
The result is inconsistent with beads' own model (Steve Yegge's `bd
create/update --design`/`--notes`, `bd prime`'s AI-optimized context
recovery): a pure-beads shop keeps resumable narrative on the issue
itself, not in a side file. Beyond the two skills, `workboard.py`'s
`scan_handoffs()` and `agent-console.py`'s `dispatch-resume-handoff`
action both glob `HANDOFF*.md` too, so the inconsistency is visible in the
dashboard tooling as well.

## Solution

Retire the free-standing file. A parked session instead: (1) leaves a
timestamped `bd comment` on every bd issue it's still touching, and (2)
creates one lightweight bd issue per parking event, labeled `handoff`,
holding the cross-cutting narrative that doesn't belong to any single
issue (`--design` for decisions/rationale, `--notes` for a state summary),
linked to every touched issue via a `tracks` dependency edge. The
`handoff` label (bd's native `--labels`, not a custom `issue_type` — those
need `types.custom` config) is the signal a fresh session looks for. The
SessionStart hook and `/resume-handoff` query bd for an open
`handoff`-labeled issue instead of globbing a file; `workboard.py` and
`agent-console.py` do the same. `specs/structured-handoff-headers/`
(both tasks already `Status: done`) is marked superseded rather than
rewritten, per the precedent at `docs/external-playbooks.md:513-519` —
its compact-header technique has no file to attach to once this lands.

Verified bd CLI syntax (bd 1.1.0, checked 2026-07-24):

```bash
# Park (from /handoff):
bd comment <touched-id> "session state: <what's done, what's next for this piece>"
bd create "Session handoff: <topic>" --labels handoff --type=task \
  --design "<decisions + rationale>" --notes "<state summary>"
bd dep add <handoff-id> <touched-id> -t tracks

# Detect (SessionStart hook / workboard / agent-console):
bd list --label handoff --status=open --json

# Resume (/resume-handoff):
bd show <handoff-id> --json --include-comments
bd show <tracked-id> --json --include-comments   # per tracked issue, latest comment

# Consume:
bd close <handoff-id> --reason "resumed and consumed"
```

`bd prime` does not surface per-issue notes/design/comments automatically
(confirmed by inspecting its output this session) — the resume path must
call `bd show` explicitly rather than relying on `bd prime` alone.

## Requirements

R1. `.claude/skills/handoff/SKILL.md` no longer writes `HANDOFF.md`.
    Instead: for every bd issue this session leaves open/touched, it runs
    `bd comment <id> "..."` with that issue's session-state update; it
    creates exactly one new bd issue labeled `handoff`
    (`bd create "Session handoff: <topic>" --labels handoff --type=task
    --design "..." --notes "..."`), linked to every touched issue via
    `bd dep add <handoff-id> <touched-id> -t tracks`; it still runs the
    `verifier` agent on completed work before parking (unchanged from
    today) and records the verdict on the handoff issue's `--notes`; it
    closes by telling the user `/clear` then `/resume-handoff`. The
    `Tracked:`-header concept is retired — there is no file for a header
    to open.

R2. `.claude/skills/resume-handoff/SKILL.md` locates open handoff work via
    `bd list --label handoff --status=open --json` instead of finding
    `HANDOFF*.md` files. Zero found → tell the user there's nothing to
    resume, stop. Multiple found → `AskUserQuestion`, each option's text
    built from that issue's title plus a bounded `bd show <id>` read (not
    full comment history) so the question is answerable without reading
    every candidate in full — same non-guessing principle as today, new
    data source. Once resolved: read the chosen issue in full
    (`bd show <id> --json --include-comments`) plus each `tracks`-linked
    issue's latest comment. Resume the recorded next step, with the same
    `/build`/`/drain` gating as today (a handoff is not live user
    authorization for those). Once the work is captured and resumed:
    `bd close <handoff-id> --reason "resumed and consumed"` — the tracked
    work issues stay open/untouched, only the handoff-tracking issue
    closes.

R3. `hooks/handoff-resume/resume-check.sh` detects an open
    `handoff`-labeled bd issue (`bd list --label handoff --status=open
    --json`) instead of globbing `HANDOFF*.md`, and injects a pointer to
    `/resume-handoff` when one exists. When `bd` is unavailable on `PATH`,
    it degrades silently (exit 0, no injected text) — matching
    `.claude/hooks/bd-compliance.sh`'s existing tolerance convention
    ("bd missing from PATH is tolerated... never brick a repo without
    bd").

R4. `specs/structured-handoff-headers/SPEC.md` gets a superseded-notice
    blockquote in the same style as `docs/external-playbooks.md:515-519`
    (`> **Superseded (<date>, bd-native-handoffs).** ...`), explaining
    that its compact-header technique has no file to attach to. The file
    is not rewritten or deleted — retained as history, per that precedent.

R5. `.claude/skills/workboard/workboard.py`'s `scan_handoffs()` (around
    line 598-625) queries bd (`bd list --label handoff --status=open
    --json`, run per scanned repo that has a `.beads/` directory) instead
    of globbing `HANDOFF*.md`. `.claude/skills/workboard/reference.md`'s
    documented `handoffs[]` schema (lines ~19, 38, 56) is updated to
    describe bd-issue-shaped fields (issue id, title, tracked issue ids,
    resume command) in place of a file path. Repos without `.beads/` (or
    without `bd` reachable) are skipped for handoff-scanning the same way
    they're presumably already skipped for other bd-dependent scans — do
    not error the whole workboard scan over one repo missing bd.

R6. `agent-console/agent-console.py`'s `dispatch-resume-handoff` action
    and related registry/navbar rendering (lines ~1101, 1115, 1237, 1242,
    2541-2599) are updated to consume workboard's new bd-issue-shaped
    handoff data instead of a file path — the dispatched action itself
    still ultimately invokes `/resume-handoff`, only the surfaced metadata
    changes.

R7. Tests updated to assert the new, bd-based behavior instead of the old
    file-based behavior, and continue to pass:
    `hooks/handoff-resume/test.sh` (currently 16/0 passing against file
    fixtures), `.claude/skills/workboard/test_workboard.py`'s
    `TestScanHandoffs` class and
    `test_parked_handoff_item_carries_resume_command` (currently 2 passing
    against file fixtures), `agent-console/tests/test_dispatch_kinds.py`'s
    `TestResumeHandoffGeneration`, `agent-console/tests/
    test_drilldown_registry.py`'s handoff-scan coverage, and
    `agent-console/tests/test_parsers.py`'s `handoffs[]`-field parsing.

R8. Doctrine and doc references updated to describe the bd-based
    mechanism instead of a markdown file: `.claude/rules/
    token-discipline.md` (Session hygiene / Session refresh sections,
    currently 3 case-insensitive "handoff" mentions — reword "write a
    handoff file" to "park state via `/handoff`" without naming a file
    format), `docs/guides/context-management.md` (3 mentions), `AGENTS.md`
    (3 mentions — hooks section, in-flight-handoff placement, any
    `Tracked:`-header reference), `docs/external-playbooks.md`'s handoff
    section (~line 548-596, already frames the file as "not authoritative
    state" — light edit, not a rewrite, since there's no file at all now).

R9. No backward-compatibility fallback for legacy `HANDOFF.md` files is
    added anywhere in this change. Confirmed at spec-authoring time: zero
    `HANDOFF.md`/`HANDOFF*.md` files exist anywhere in `~/claude`, and
    `handoff`/`resume-handoff` are plugin-distributed skills (not copied
    per-repo, per CLAUDE.md's "Portability is data-level" convention), so
    no other repo needs a migration path either.

## Out of scope

- Any repo other than `~/claude`. The two skills are plugin-distributed;
  a repo with the `agentic` plugin enabled picks up the new behavior
  automatically, with nothing to port per-repo.
- Changes to bd's own CLI, schema, or label semantics — this spec only
  uses commands that already exist and were verified this session.
- `CLAUDE.md`'s "Compact instructions" section — confirmed generic
  (task-file paths, wave state, branch names, evidence pointers, review
  findings), with no direct `HANDOFF.md` reference to update.
- `hooks/session-refresh/refresh-check.sh` — confirmed format-agnostic; it
  only names `/handoff` as the directive to run, never assumes a file
  format, so it needs no code change (its README/docs may get an
  incidental word-choice edit under R8 if they describe the artifact as a
  "file").
- Retagging historical, already-closed bd issues with a `handoff` label —
  the label only matters for open, in-flight parking going forward.
- Building a new eval scenario exercising a full park-then-resume cycle
  end to end — out of scope for this pass; R7's updated unit/integration
  tests are the verification depth for this change (see the Depth ceiling
  note on AC7 below).

## Acceptance criteria

- [ ] AC1 (R1): `grep -ci "HANDOFF.md" .claude/skills/handoff/SKILL.md` →
      0 (today: 5 — verified 2026-07-24). `grep -c "bd comment\|bd create.*--labels handoff\|bd dep add.*-t tracks" .claude/skills/handoff/SKILL.md`
      → ≥ 3 (today: 0 — the three commands don't appear yet).
- [ ] AC2 (R2): `grep -ci "HANDOFF.md" .claude/skills/resume-handoff/SKILL.md`
      → 0 (today: 4). `grep -c "bd list --label handoff\|bd show.*--include-comments\|bd close.*resumed and consumed" .claude/skills/resume-handoff/SKILL.md`
      → ≥ 3 (today: 0).
- [ ] AC3 (R3): `grep -c "HANDOFF" hooks/handoff-resume/resume-check.sh` →
      0 (today: 9). `grep -c "bd list --label handoff" hooks/handoff-resume/resume-check.sh`
      → ≥ 1 (today: 0). `bash hooks/handoff-resume/test.sh` → all pass
      (rewritten to fixture bd state instead of fixture files; baseline
      today is 16/0 against the old file-based fixtures).
- [ ] AC4 (R4): `grep -c "^Superseded\|Superseded (" specs/structured-handoff-headers/SPEC.md`
      → ≥ 1 (today: 0).
- [ ] AC5 (R5): `grep -c "HANDOFF" .claude/skills/workboard/workboard.py`
      → 0 (today: 9). `grep -c "bd list --label handoff\|--label.*handoff" .claude/skills/workboard/workboard.py`
      → ≥ 1 (today: 0). `cd .claude/skills/workboard && python3 -m pytest test_workboard.py -k handoff -q`
      → all pass (today: 2 passed against file fixtures; must still pass
      2+ after rewriting to bd-mocked fixtures).
- [ ] AC6 (R6): `cd agent-console && python3 -m pytest tests/test_dispatch_kinds.py -k ResumeHandoff tests/test_drilldown_registry.py tests/test_parsers.py -q`
      → all pass (baseline: currently passing against file-based mocks;
      must still pass after rewriting to bd-based mocks).
- [ ] AC7 (R7): the four test files listed in R7 all pass as a group:
      `bash hooks/handoff-resume/test.sh && (cd .claude/skills/workboard && python3 -m pytest test_workboard.py -q) && (cd agent-console && python3 -m pytest tests/ -q)`
      → exit 0. Depth ceiling: this verifies the mechanism's unit-level
      pieces (detection, scanning, dispatch-action shape) independently;
      it does not exercise one continuous session parking and a second
      session resuming end to end. That gap is a named manual-pending
      check: after implementation, run `/handoff` for real in a scratch
      task, confirm the resulting bd issue and comments look right via
      `bd show`, then start a fresh session and confirm `/resume-handoff`
      picks it up and closes it correctly.
- [ ] AC8 (R8): `grep -ci "HANDOFF\.md\|handoff file" .claude/rules/token-discipline.md docs/guides/context-management.md AGENTS.md docs/external-playbooks.md`
      → 0 in each (today: mentions exist per R8's counts; the literal
      phrases "HANDOFF.md" and "handoff file" are the ones to retire —
      references to the `/handoff` skill by name are fine to keep).
- [ ] AC9 (R9): `find /Users/sjaconette/claude -iname "HANDOFF*.md" -not -path "*/.git/*"`
      → empty (today: empty — confirms no regression introduces a new
      file-based fallback path).
- [ ] End-to-end: `bash scripts/check.sh` passes with all of the above
      landed.

## Open questions

(none)
