# Task 02: Give build a sibling-task /drain nudge at end-of-run

Status: in-progress
Depends on: none
Priority: P2
Budget: 40 turns
Spec: ../SPEC.md (requirements R2, R3; CLAUDE.md mirror + plugin-version
conventions)
Touch: .claude/skills/build/SKILL.md, antigravity/.agents/workflows/build.md, .claude-plugin/plugin.json

## Goal

`build/SKILL.md`'s end-of-run step (currently the "`/clear` before starting
the next task" line at line 186, blank line 187) checks whether the
just-completed task file resolves to a `specs/<slug>/tasks/*.md` path and,
if so, whether any sibling `tasks/*.md` file in that directory has
`Status: pending`. If both hold, the final output prints one additional
line pointing at `/drain specs/<slug>` for continuous multi-task work,
alongside (not replacing) the existing `/clear` instruction.
`Status: blocked`-only siblings do not trigger the nudge. Task files
outside a `specs/<slug>/tasks/` layout never trigger it. Build gains no
loop/continuation logic of its own — this is a printed line, not new
control flow (spec Solution #2, explicitly rejects an in-build loop mode).
The antigravity mirror (`antigravity/.agents/workflows/build.md`) carries
the same nudge concept in its own end-of-run wording, and
`.claude-plugin/plugin.json`'s version is bumped, per this repo's
mirror/version conventions in CLAUDE.md (skill behavior changed here, so
both are required, not optional polish).

## Touch

`.claude/skills/build/SKILL.md`, `antigravity/.agents/workflows/build.md`,
and `.claude-plugin/plugin.json` only. Do not touch drain's own files
(`.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`) —
this task adds a nudge *toward* drain, it does not change drain itself
(R3 stays untouched by this task too). Do not add an in-build
loop/continuation mode — out of scope per spec Solution #2.

## Steps

1. Read `.claude/skills/build/SKILL.md` lines ~175-195 (the end-of-run /
   final reporting section). Confirm the current line 186 instruction
   text ("Tell the user to `/clear` before starting the next task.") —
   note the file may have shifted a line or two since this task was
   authored; anchor on the instruction's wording, not a hard-coded line
   number.
2. Write the failing-check first where practical: before editing, run
   `grep -n "drain specs/<slug>" .claude/skills/build/SKILL.md` and confirm
   no match (this is the "red" baseline for the acceptance grep in step 6).
3. Add the conditional nudge logic to that end-of-run step: given the
   just-completed task file's path, derive `specs/<slug>/tasks/` if it
   matches that layout; if it does, scan sibling `tasks/*.md` files in the
   same directory for any with a `Status: pending` header line; if found,
   print one line naming `/drain specs/<slug>` as the tool for continuous
   work across the remaining tasks, in addition to (not replacing) the
   `/clear` line. No match on the path layout, or no `pending` siblings
   (blocked-only or none), means no nudge line — say so explicitly in the
   skill text so a worker following it doesn't over-fire.
4. Mirror the same nudge concept into
   `antigravity/.agents/workflows/build.md`'s end-of-run section (its
   current wording is "Tell the user to start the next task in a NEW
   conversation," not `/clear` — keep that phrasing, add the analogous
   drain-nudge sentence next to it). Per
   docs/memory/workboard-mirror-verbatim.md (cited in the breakdown
   skill's own guidance), this mirror is a paraphrased port, not a
   byte-identical copy — match the concept and the guard condition, not
   the original's exact sentence.
5. Bump `.claude-plugin/plugin.json`'s `"version"` field (currently
   `0.8.38` as of this task's authoring — verify the value at your own
   base commit with `git show HEAD:.claude-plugin/plugin.json | grep
   version` rather than assuming this literal, since a sibling task may
   have already bumped it) per CLAUDE.md: "Bump version in plugin.json
   whenever skill behavior changes."
6. Verify: `grep -n "drain specs/<slug>" .claude/skills/build/SKILL.md` (or
   your exact chosen wording) now matches, in the end-of-run section,
   visibly guarded by the sibling-`Status:` check rather than
   unconditional.
7. Run `bash evals/lint-ultra-gate.sh` — must still pass (build/SKILL.md
   is not one of the four ultra-path skills; confirms the gate is
   unaffected).
8. Exercise the four scenario checks from the spec's acceptance criteria
   using disposable fixtures — do NOT commit fixture files. Suggested
   approach: under a scratch location (e.g. this session's scratchpad, not
   `specs/`), construct minimal 2-3-file `tasks/` directories with
   `Status:` headers set to the four scenario shapes (pending sibling;
   no sibling; blocked-only sibling; not under a `specs/<slug>/tasks/`
   path at all), then trace your own edited SKILL.md logic by hand against
   each directory's file listing to confirm which produce the nudge line
   and which don't. This is a logic trace against your own diff, not a
   full nested `/build` pipeline invocation — a real end-to-end `/build`
   run against each scenario is a human verification step (below), not
   this task's automated acceptance gate, per
   docs/memory/unattended-worker-tool-limits.md's manual-pending pattern.
   Delete scratch fixtures when done.
9. Commit: `feat: nudge build toward /drain when pending sibling tasks
   remain`.

## Acceptance

- [ ] `grep -n "drain specs/<slug>" .claude/skills/build/SKILL.md` (or the
      exact wording chosen) is present in the end-of-run section, visibly
      guarded by a sibling-`Status:` check rather than unconditional.
- [ ] `grep -n "drain" antigravity/.agents/workflows/build.md` shows the
      mirrored nudge concept near its own end-of-run section (content
      coverage, not a byte-identical diff — this mirror is a paraphrased
      port per docs/memory/workboard-mirror-verbatim.md).
- [ ] `git show HEAD:.claude-plugin/plugin.json | grep version` differs
      from the same grep at this task's base commit (version bumped, not
      compared to a hard-coded literal).
- [ ] `bash evals/lint-ultra-gate.sh` exits 0.
- [ ] Your own hand-trace of the four scenario fixtures (step 8) shows the
      nudge firing only for the pending-sibling case and not the other
      three — record the trace result as evidence in this task's notes.

## Manual verification (human, after merge — not gating this task's Status)

These four require an actual `/build` invocation in a live session and are
explicitly deferred here rather than gated on this task, per CLAUDE.md's
"give the criterion an explicit manual-pending path" convention (an
unattended worker has no live-conversation authorization to self-invoke
`/build`'s launch-gated pipeline):

- [ ] `/build` on one task from a 2+ task spec with a `Status: pending`
      sibling → final output includes the `/drain` nudge line.
- [ ] `/build` on a single-task spec (no siblings) → no nudge line.
- [ ] `/build` on a task whose only sibling is `Status: blocked` → no
      nudge line.
- [ ] `/build` on a task file outside any `specs/<slug>/tasks/` layout →
      no nudge line.
