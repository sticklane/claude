# Task 01: Reconcile token-discipline.md's awaited-children rule with drain's shipped self-relaunch

Status: pending
Depends on: none
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirements R1, R3)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md`'s "Awaited children, never detached
(maintainer policy, 2026-07-09)" bullet (currently lines 93-101) carries a
dated exception sentence so a reader of the rule alone — no git-log
archaeology — can correctly state whether drain's headless generation
self-relaunch is policy-compliant or a violation. No behavior changes
anywhere else; this is a documentation-only reconciliation. a524797's
decision (default self-relaunch, `attended` flag as sole opt-in checkpoint)
is not re-litigated or re-tightened (R3) — this task touches only
token-discipline.md.

## Touch

Only `.claude/rules/token-discipline.md`. Do not touch
`.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`,
`.claude-plugin/plugin.json`, or the antigravity mirror — none of those
change under this task; editing any of them would re-open R3's
already-closed question of whether a524797's decision stands.

## Steps

1. Read the current bullet verbatim (lines 93-101):

   > - **Awaited children, never detached (maintainer policy, 2026-07-09).**
   >   Fresh context comes from the subagent boundary — a worktree-isolated
   >   worker with a blank context — never from detachment. Every spawned
   >   agent has a parent that waits for it and collects its result before
   >   moving on (synchronous dispatch); no fire-and-forget sub-verifiers, no
   >   orphaned children outliving the step that spawned them, no detached
   >   orchestrator generations where an attended parent can supervise
   >   instead. A worker that spawns its own verifier awaits it inline the
   >   same way.

   Confirm "2026-07-11" does not currently appear in the file (it doesn't,
   as of this task's authoring) and that the bullet still reads as an
   unconditional ban.
2. Read docs/human-gates.md lines ~115-136 for the launch-vs-continuation
   framing already used for the 2026-07-11 boundary move elsewhere in this
   repo, specifically: "the human gates govern the _launch_ of an
   autonomous run, not its _continuation_: once a human launches, the
   session consumes its scope and self-chains on already-granted READY
   verdicts, re-gating no individual step." (lines 128-131).
3. Draft one dated exception sentence (or short clause) appended to the
   bullet, anchored specifically to the "no orphaned children outliving
   the step that spawned them" clause — not to the "where an attended
   parent can supervise instead" qualifier, which already reads as
   conditioned on supervision being available and is therefore the wrong
   clause to anchor an exception to (per spec R1). The sentence must:
   - Name drain's generation-boundary self-relaunch specifically (not a
     generic carve-out for "background work" or similar).
   - Cite a524797 by short hash and its "Maintainer decision 2026-07-11
     (explicit, supersedes this morning's attended-only tightening): no
     pipeline step forces a human" rationale.
   - Use the human-gates.md launch-vs-continuation framing to explain why
     this is a scoped exception rather than a rule violation (the
     generation relaunch is a continuation of an already-launched drain
     run, not a new unauthorized launch).
   - Read as clearly dated/scoped — a future maintainer changing this
     policy again should be able to tell this sentence is a point-in-time
     carve-out, not the rule's permanent shape.
4. Edit the bullet in place. Keep the rest of the bullet's wording and the
   surrounding "## Dispatch authoring" section untouched.
5. Verify: `grep -n "2026-07-11" .claude/rules/token-discipline.md` shows
   the new sentence adjacent to the bullet.
6. Run `bash evals/lint-ultra-gate.sh` — must still pass (this file isn't
   one of the four ultra-path skills, but confirm unaffected).
7. Fresh-eyes check for the end-to-end acceptance criterion: dispatch one
   `scout` agent, prompted with ONLY the edited bullet's text (not this
   task file, not git log, not a524797's diff) and the question "Per this
   bullet alone, is drain's headless generation-boundary self-relaunch
   policy-compliant or a rule violation?" A correct edit produces an
   answer citing the exception sentence and concluding compliant, without
   the scout needing to ask for more context. If the scout can't tell,
   the sentence isn't clear enough — revise and re-check.
8. Commit: `docs: reconcile awaited-children rule with drain's dated
   self-relaunch exception`.

## Acceptance

- [ ] `grep -n "2026-07-11" .claude/rules/token-discipline.md` shows the
      new exception sentence adjacent to the "Awaited children, never
      detached" bullet, naming drain's generation relaunch specifically.
- [ ] `bash evals/lint-ultra-gate.sh` exits 0.
- [ ] `git diff --stat` shows only `.claude/rules/token-discipline.md`
      changed (confirms R3: no drain skill files touched).
- [ ] A fresh `scout` agent given only the edited bullet's text answers
      the compliance question correctly (per step 7) without additional
      context — record its answer in this task's plan/notes as evidence.
