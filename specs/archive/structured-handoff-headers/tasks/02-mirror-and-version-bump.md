# Task 02: Mirror into antigravity, confirm codex symlinks, version bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirements R3, R4)
Touch: antigravity/.agents/skills/handoff/SKILL.md, antigravity/.agents/skills/resume-handoff/SKILL.md, tests/mirror-procedure-manifest.txt, .claude-plugin/plugin.json

## Goal

Task 01's header-format and disambiguation changes are ported (paraphrased,
not byte-copied — these are prose SKILL.md files) into
`antigravity/.agents/skills/{handoff,resume-handoff}/SKILL.md` (the real
content — `antigravity/.agents/workflows/handoff.md` is a thin launcher
stub pointing at the skill, not the mirror target; confirm this before
editing), coverage-checked via the mirror manifest, and
`.claude-plugin/plugin.json`'s version is bumped. `codex/.agents/skills/
{handoff,resume-handoff}` are confirmed symlinks into the antigravity
copies — reach codex automatically, no separate codex edit.

## Touch

Exactly the files listed above. Do not touch
`.claude/skills/handoff/SKILL.md` or `.claude/skills/resume-handoff/SKILL.md`
(task 01's scope, already landed) or `antigravity/.agents/workflows/handoff.md`
(the launcher stub — unaffected).

## Steps

1. Confirm task 01 is `Status: done` before starting.
2. Confirm `antigravity/.agents/workflows/handoff.md` is still a thin
   stub with no step text of its own (per Goal) — if it has grown real
   content since this spec was written, port there instead and note it in
   `## Progress`.
3. Port task 01's header-block change into
   `antigravity/.agents/skills/handoff/SKILL.md` in antigravity's own
   voice — same fields (`Task:`/`Status:`/`Next step:`/`Resume with:`/
   `Blocking on:`), same "precedes the unchanged free-form prose"
   framing.
4. Port task 01's disambiguation change into
   `antigravity/.agents/skills/resume-handoff/SKILL.md`'s own
   multiple-candidates branch — same behavior (read headers only, show
   `Task:`/`Status:` in the question, never auto-select).
5. Add two new lines to `tests/mirror-procedure-manifest.txt` in its
   existing `<source>|<mirror>|<phrase>` format: one for the handoff
   header-field phrase, one for the resume-handoff disambiguation phrase.
6. Confirm `codex/.agents/skills/handoff` and
   `codex/.agents/skills/resume-handoff` are still symlinks (not real
   files) — if either has been converted to real content since this spec
   was written, that's a scope change; flag it in `## Progress` rather
   than silently editing it.
7. Bump `.claude-plugin/plugin.json`'s `version`.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` passes.
- [x] `grep -n "Resume with:\|Blocking on:" antigravity/.agents/skills/handoff/SKILL.md`
      returns matches (content-coverage check for the paraphrased port,
      per `docs/memory/workboard-mirror-verbatim.md`'s distinction between
      byte-identical `.py` mirrors and paraphrased prose mirrors — this is
      the latter).
- [x] `grep -n "compact header\|head -n" antigravity/.agents/skills/resume-handoff/SKILL.md`
      returns a match.
- [x] `test -L codex/.agents/skills/handoff && test -L
      codex/.agents/skills/resume-handoff` — both still symlinks.
- [x] The commit modifying `.claude-plugin/plugin.json` shows the version
      line changed in its own diff (`git show <this-commit> --
      .claude-plugin/plugin.json | grep -q '^+.*"version"'`) — not a
      pinned before/after literal.
- [ ] MANUAL-PENDING (attended-only: `/handoff` and `/resume-handoff` are
      interactive skills, not runnable by an unattended worker per
      `docs/memory/unattended-worker-tool-limits.md`): a human runs
      `/handoff` in a fixture repo with two candidate `HANDOFF.md` files
      present (distinct `Task:` values) and confirms `resume-handoff`
      presents an `AskUserQuestion` whose option text shows each
      candidate's `Task:`/`Status:` — not bare paths — without having
      read either candidate's full body first.

## Progress

- 2026-07-21: DONE. 4 of 5 acceptance criteria verified against merged main (merge commit 8c38f757, worker commits 03007fbb/f86b1367). The 5th is the task's own MANUAL-PENDING criterion (attended-only `/handoff`+`/resume-handoff` fixture check) — filed to repo-root HUMAN.md per `.claude/rules/human-blockers.md`. Worker deliberately did not port the Claude-Code-specific `AskUserQuestion` tool name into antigravity (0 existing references there); expressed as plain "ask the user" instead, matching antigravity's existing idiom — a load-bearing runtime divergence, not a gap.
