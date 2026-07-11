# Task 01: Align codex-cli-port's gating rationale with the live-authorization-contract split

Status: in-progress
Depends on: none
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (Approach steps 1-4)
Touch: specs/codex-cli-port/SPEC.md

## Goal

`specs/codex-cli-port/SPEC.md`'s R3 names the live-authorization-contract
prose requirement for `drain`/`build`/`autopilot` specifically, its
Problem section documents the resolved research finding (that
`allow_implicit_invocation: false` already gives all four skills the
needed guarantee), and its `Breakdown-ready` header round-trips
false→true across two separate, ordered commits proving the race-closing
mechanism actually ran — not just a final state that happens to read
`true`.

## Touch

Only `specs/codex-cli-port/SPEC.md`. This is a single-file, single-task
spec fix — do not touch `specs/codex-cli-port/tasks/` (that spec has no
tasks/ yet and none should be created by this task), and do not touch
this task's own parent `../SPEC.md`.

## Steps

1. Edit `specs/codex-cli-port/SPEC.md`'s header: change
   `Breakdown-ready: true` to `Breakdown-ready: false`. **Commit this
   single-line change immediately, as its own standalone commit**, before
   doing anything else — this is what closes the race described in the
   parent spec's Problem section (a concurrent session reading committed
   HEAD must see `false` from this point on).
2. Edit `specs/codex-cli-port/SPEC.md`'s R3 (currently: "Each of the four
   SKILL.md bodies inline-covers the same execution steps as its
   `.claude/skills/<name>/SKILL.md` counterpart") to add: for
   `drain`/`build`/`autopilot` specifically, the inlined SKILL.md content
   must also include a live-authorization-contract paragraph — adapted to
   name Codex's actual mechanism (`allow_implicit_invocation: false`
   blocks automatic description-match selection; a human must type the
   invocation via `$skill-name` or `/skills`) rather than quoting
   `.claude/`'s own tool names verbatim. State explicitly that `evals`'s
   SKILL.md is unaffected (its "human-only, paid headless sessions"
   framing already covers an unconditional guarantee, nothing more to add).
3. Add one paragraph to `specs/codex-cli-port/SPEC.md`'s Problem section
   (append, don't rewrite existing prose) documenting the resolved
   research finding: Codex's docs (learn.chatgpt.com/docs/build-skills)
   describe exactly two invocation pathways — agent-autonomous
   description-match (blocked by `allow_implicit_invocation: false`) and
   human-typed explicit invocation (unaffected) — with no third
   "model self-invokes explicitly" pathway documented anywhere, so the
   flag already gives all four skills a sufficient, uniform guarantee.
   Cite `specs/codex-port-launch-authorization-parity/SPEC.md` as the
   source rather than duplicating the full quote chain.
4. Edit `specs/codex-cli-port/SPEC.md`'s header: change
   `Breakdown-ready: false` back to `Breakdown-ready: true`. Commit this
   as its own closing commit, separate from steps 2-3's edits.

## Acceptance

- [ ] `git log --all -p -- specs/codex-cli-port/SPEC.md` shows a commit
      from this task whose diff contains a removed `-Breakdown-ready: true`
      line and an added `+Breakdown-ready: false` line, as a standalone
      commit (not bundled with the R3 or Problem-section edits).
- [ ] `grep -n "live-authorization-contract" specs/codex-cli-port/SPEC.md`
      finds a match inside the `- R3:` bullet.
- [ ] `specs/codex-cli-port/SPEC.md`'s Problem section contains the
      resolved-research paragraph, citing
      `specs/codex-port-launch-authorization-parity/SPEC.md`.
- [ ] `grep -q "Breakdown-ready: true" specs/codex-cli-port/SPEC.md` passes
      (step 4's closing commit landed).

## Progress

- 2026-07-11: Worker returned DEFERRED — `specs/codex-cli-port/SPEC.md` was
  untracked in the parent checkout with no git history, so the
  false→true round-trip and its acceptance diff had no committed
  baseline to operate against. Resolved by the orchestrator: committed
  `specs/codex-cli-port/` (commit b75b5e6) to establish the baseline.
  No source changes were made by the deferred worker; re-dispatching
  against the now-committed baseline.
