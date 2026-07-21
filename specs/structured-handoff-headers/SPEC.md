# Structured handoff headers: informative disambiguation without full-body reads

Status: open
Breakdown-ready: true

## Problem

`HANDOFF.md` files are prose-narrative with no structured header:
`.claude/HANDOFF-drain-hub.md` is 8,194 bytes. `resume-handoff` reads a
chosen handoff "in full" by design (correct — narrative context like
gotchas shouldn't be truncated), and when multiple candidate `HANDOFF.md`
files exist, `resume-handoff/SKILL.md` step 1 already does the right
thing procedurally — it does **not** read every candidate's full body;
it "list[s] the paths and ask[s] the user which one via `AskUserQuestion`
... never guess silently." (An earlier draft of this spec mischaracterized
this as "read each candidate's full prose body to pick one" — that isn't
what the skill does; corrected here after review.)

The real gap is narrower: the user is asked to disambiguate from **bare
file paths alone**, with no content signal to base the choice on. A path
like `.claude/HANDOFF-drain-hub.md` doesn't say what task it's about,
whether it's still relevant, or what the recorded next step is — so
answering the question well means either the user already remembers, or
the assisting session reads the candidates' full bodies anyway to
summarize them for the question text, paying the same full-read cost the
"never guess silently" design was trying to avoid on the other side.

Beads' `bd prime` solves the analogous problem — giving an agent a compact
resume artifact instead of forcing a full re-read
(`docs/task-tracking-design-research-2026-07.md`'s Design comparison
section has the citation and reasoning for adopting this technique
natively). This spec adopts that idea narrowly: a compact header ahead of
the existing prose, used to make the *existing* `AskUserQuestion` step
informative — not to replace it with silent auto-pick.

## Solution

`.claude/skills/handoff/SKILL.md` is updated so every `HANDOFF.md` it
writes opens with a fixed few-line block — `Task:` (a one-line name for
the work this handoff is about, e.g. the spec/task path or a short
description — the actual "which one is mine" signal, since `Status:` and
`Blocking on:` alone are often identical across candidates), `Status:`,
`Next step:`, `Resume with:` (the skill/command to run), `Blocking on:` —
before the existing free-form Task/Evidence/Gotchas prose, which is
unchanged in content and purpose.

`.claude/skills/resume-handoff/SKILL.md` step 1 is updated so that, when
multiple candidates exist, it reads each candidate's compact header only
(a bounded read, e.g. `head -n 10`) and presents each one's `Task:` and
`Status:` alongside its path as the `AskUserQuestion` option text — never
the full body. This makes the existing question answerable without
opening any file, while leaving the "ask the user, never guess silently"
contract fully intact: the skill never auto-selects. If the headers
genuinely don't distinguish two candidates (e.g. identical `Task:`
values — plausible for two parallel threads on the same spec), the
question is still asked with whatever the headers show; the user can
always fall back to inspecting the files themselves, exactly as today.
The single-candidate path is unchanged.

## Requirements

- **R1**: `.claude/skills/handoff/SKILL.md` documents the mandatory
  compact header block (`Task:`/`Status:`/`Next step:`/`Resume with:`/
  `Blocking on:`) as the first lines of every `HANDOFF.md` it produces,
  ahead of the unchanged free-form prose sections. `Task:` is a required
  field — the one a resumer actually compares between candidates.
- **R2**: `.claude/skills/resume-handoff/SKILL.md` step 1 is updated so
  that, when multiple candidate `HANDOFF.md` files exist, it reads each
  candidate's compact header only (bounded read) and includes each
  candidate's `Task:`/`Status:` values in the `AskUserQuestion` option
  text instead of a bare path. **The existing "ask the user, never guess
  silently" contract is unchanged** — this requirement makes the question
  informative, it does not replace the question with auto-selection. The
  single-candidate path is unchanged.
- **R3**: Per `.claude/rules/mirror-procedure-discipline.md`, R1/R2 are
  mirrored into `antigravity/.agents/skills/{handoff,resume-handoff}/`
  (real copies there — the full-mirrored-port leg) in the same commits.
  `codex/.agents/skills/{handoff,resume-handoff}` are confirmed symlinks
  into the antigravity copies — they reach codex automatically through the
  antigravity edit; no separate codex edit is needed or expected.
- **R4**: `.claude-plugin/plugin.json`'s `version` is bumped (skill
  behavior changed in handoff and resume-handoff).

## Out of scope

- Shortening or restructuring `HANDOFF.md`'s existing prose content — only
  a header is added ahead of it; the narrative sections are unchanged.
- Silent auto-selection among multiple candidates — explicitly rejected;
  see R2. The user is always asked.
- A tiebreak rule for headers that don't distinguish two candidates beyond
  "ask anyway, with whatever the headers show" — no smarter disambiguation
  (timestamps, content diffing) is added; the user resolves ambiguity the
  same way they do today.
- Any change to task-status representation (drain/build wiring,
  `drain_frontier.py`) — that is `specs/cheap-task-status-checks/SPEC.md`,
  a separate spec.
- A machine-readable (JSON/YAML) handoff format — the header stays plain
  `Key: value` markdown lines, consistent with every other machine-read
  header in this repo.
- Detecting handoff files that aren't literally named `HANDOFF.md` (e.g.
  `/handoff`'s own collision-avoiding `HANDOFF-<topic>.md` naming) as
  candidates — both the hook and `resume-handoff` already scope to the
  literal filename `HANDOFF.md` today; unchanged here.

## Acceptance criteria

The two grep checks below confirm the new text landed (doc-presence
anchors); they do not verify the disambiguation behavior itself — that is
the MANUAL-PENDING criterion, since `/handoff` and `/resume-handoff` are
interactive skills an unattended check cannot exercise.

- [ ] `grep -n "^Task:\|Resume with:\|Blocking on:" .claude/skills/handoff/SKILL.md`
      returns matches, including a required `Task:` field (R1).
- [ ] `grep -n "compact header\|head -n" .claude/skills/resume-handoff/SKILL.md`
      returns a match, in the step 1 multi-candidate branch specifically
      (R2).
- [ ] `grep -n "AskUserQuestion" .claude/skills/resume-handoff/SKILL.md`
      still returns a match after the edit — confirms R2 augments the
      existing question with header content rather than removing it (the
      never-guess-silently regression guard).
- [ ] MANUAL-PENDING: a human runs `/handoff` in a fixture repo with two
      candidate `HANDOFF.md` files present (distinct `Task:` values) and
      confirms `resume-handoff` presents an `AskUserQuestion` whose option
      text shows each candidate's `Task:`/`Status:` — not bare paths —
      without having read either candidate's full body first.
- [ ] `bash tests/test_mirror_procedure_coverage.sh` passes (add the new
      R1/R2 phrases to `tests/mirror-procedure-manifest.txt`).
- [ ] `test -L codex/.agents/skills/handoff && test -L
      codex/.agents/skills/resume-handoff` — both still symlinks, so no
      separate codex edit is needed (R3).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change (R4).

## Open questions

(none)

## Parallelization

Single cohesive change (R1/R2 touch two related SKILL.md files with no
independent sub-decisions) — one task, plus a closing task for the mirror
(R3) and version bump (R4) once it lands.
