# Task 01: idea self-chains into /design for open technology/architecture choices

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R1b, R2, R3, R4, R5, R6)
Touch: .claude/skills/idea/SKILL.md, .claude-plugin/plugin.json

## Goal

`.claude/skills/idea/SKILL.md` gains a new step, inserted between the
existing "write the spec" step and the `/critique`-invocation step, that
self-chains into `/design specs/<slug>/SPEC.md` (via the Skill tool,
synchronous, same mechanism already used for `/breakdown`) whenever
`## Open questions` names a technology/architecture choice — both
immediately after the spec is first written and after every subsequent
`/critique` fix wave (the same file check, re-run, not two mechanisms).
The old technology-choice fallback text is removed from the hand-off step,
which keeps only its non-technology fallback and its existing
`/breakdown` self-chain. `.claude-plugin/plugin.json`'s version is bumped.

## Touch

Do not touch `.claude/skills/design/SKILL.md`, `.claude/skills/critique/SKILL.md`,
or `.claude/skills/breakdown/SKILL.md` — this task only changes how `/idea`
invokes `/design`, never their own internals. Do not touch anything under
`antigravity/` — per the spec's Out of scope, this change is a skill
self-chain and self-chaining is documented as deliberately not ported
(`antigravity/README.md`'s translation table); `antigravity/.agents/skills/idea/SKILL.md`'s
step 5 printed-pointer text for the technology-choice case must stay
byte-for-byte unchanged.

## Steps

1. Read `.claude/skills/idea/SKILL.md` in full to find the current step
   numbering (spec's Problem section cites step 5 at lines ~89-95; verify
   against current content, don't trust stale line numbers).
2. Insert a new step between "write the spec" and the `/critique`
   invocation step implementing R1 (the initial check) and R1b (the
   re-check after every `/critique` fix wave, reusing R1's identical
   `## Open questions` file check — not a separate semantic judgment over
   critic findings).
3. In that new step, implement R2 (ignore `/design`'s own "Next stage"
   line; resume step 4 — proceed to `/critique` for the R1 entry point, or
   continue the fix loop without restarting from the spec-writing step for
   the R1b entry point), R4 (if `/design` leaves `## Open questions`
   non-empty, take the printed-pointer fallback — for R1: don't proceed to
   the first `/critique` invocation; for R1b: abort the fix loop), and R5
   (at most one `/design` self-chain per `/idea` session; a second
   occurrence after the cap is spent also takes the printed-pointer
   fallback, never a second `/design` call).
4. In the hand-off step, remove the technology-choice `/design` fallback
   text (the old lines ~99-100 per the spec's Problem section — verify
   against current content). Keep the non-technology fallback (user asked
   for spec only; non-interactive doubt) and the existing `/breakdown`
   self-chain untouched (R3).
5. Bump `.claude-plugin/plugin.json`'s `version` (R6).
6. Verify: read back the edited `idea/SKILL.md` and confirm the new step's
   prose states (a) the same `## Open questions` check fires at both entry
   points, (b) the once-per-session cap and its fallback, (c) R4's
   fallback phrasing for both entry points — these are prose-consistency
   checks, not runtime behavior, so verify by reading the text you wrote.
7. If practical within budget, exercise the new step live: run `/idea` in
   a throwaway scratch directory (or a disposable test spec slug clearly
   marked for deletion, e.g. `specs/zz-test-design-autochain-<random>/`)
   with a test idea whose interview surfaces a genuine open library/
   framework choice; confirm in the transcript that `design` is invoked
   via the Skill tool with the test spec's `SPEC.md` as argument, before
   any `/critique` invocation, and that `/design`'s "Next stage:
   /breakdown..." line is not surfaced to you as an instruction. Delete
   the throwaway spec directory afterward (never leave test artifacts in
   `specs/`). If this live check is impractical within budget, say so in
   your final report's Done vs remaining and rely on the static
   prose-inspection checks in step 6 instead — do not skip verification
   entirely.

## Acceptance

- [ ] `grep -c '## Open questions' .claude/skills/idea/SKILL.md` → the new
      step's text references `## Open questions` at least once as its
      trigger condition (R1).
- [ ] The new step's text states the check re-runs after every `/critique`
      fix wave, not only once after the spec is first written (R1b) —
      confirm by reading the step's prose; it must not describe a second,
      different detection mechanism for critic-revealed choices.
- [ ] The new step's text states the once-per-session cap and its
      fallback (a second occurrence after the cap is spent takes the
      printed-pointer fallback, never a second `/design` call) (R5).
- [ ] The new step's text states R4's fallback for both entry points (R1:
      does not proceed to the first `/critique` invocation; R1b: aborts
      the fix loop) when `/design` leaves `## Open questions` non-empty.
- [ ] `grep -c 'design' .claude/skills/idea/SKILL.md` in the hand-off step
      specifically (the step containing "Hand off" / the `/breakdown`
      self-chain) → the technology-choice `/design` fallback branch is
      gone from that step; the non-technology fallback text is still
      present, unchanged.
- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json | grep '"version"'`
      shows the version increased (R6).
- [ ] `git diff HEAD~1 -- antigravity/` → empty (no antigravity changes;
      per Out of scope).
- [ ] `git diff HEAD~1 -- .claude/skills/design/SKILL.md .claude/skills/critique/SKILL.md .claude/skills/breakdown/SKILL.md` →
      empty (none of the downstream skills' own internals touched).
