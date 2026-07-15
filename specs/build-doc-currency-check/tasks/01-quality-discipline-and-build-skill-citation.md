# Task 01: Add Documentation-currency section and cite it from build/SKILL.md's close-out

Status: done
Depends on: none
Priority: P1
Budget: 5 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R7)
Touch: .claude/rules/quality-discipline.md, .claude/skills/build/SKILL.md, .claude-plugin/plugin.json

## Goal

`.claude/rules/quality-discipline.md` gains a "## Documentation currency"
section scoped to `/build`'s attended completion step: before finishing a
task, check whether the diff invalidates `AGENTS.md`'s Map/Commands/State
sections or anything README.md tells an end user, and update it in the
same commit if so. This is a discipline reminder, not a new mechanical
gate. `.claude/skills/build/SKILL.md`'s close-out section (section 4, the
pre-commit-review bullet) cites this new section by name, and separately
notes that doc-currency checking lives there, "not by /code-review
itself" (verbatim, no backticks around `/code-review`) — distinct from the
citation so both edits verify independently. `.claude-plugin/plugin.json`'s
version is bumped.

## Touch

Exactly the three files listed above. Do not touch antigravity or codex
mirrors (Task 02 owns those) — this deliberately splits from CLAUDE.md's
codex-leg convention that a task touching `.claude/skills/build/SKILL.md`
also carries the matching `codex/.agents/skills/build/SKILL.md` update in
its own `Touch:`. Here it's deferred one task later instead: confirmed
safe because the codex parity gate (`tests/test_codex_parity.sh`) is
existence-only and the content-parity gate covers only enumerated `.py`
files, not SKILL.md prose — so this task's intermediate commit (`.claude`
edited, mirrors not yet) trips no gate.

**BLOCKING PRECONDITION — cleared by human judgment call, 2026-07-15.**
`specs/narrow-autopilot` also edited `.claude/skills/build/SKILL.md`
(inserting a classification gate "near its start," shifting every line
number after it) and had to land first — both specs' own text stated
this explicitly (this spec's Sequencing note; narrow-autopilot's Problem
section and critique-findings finding 6). All 6 of narrow-autopilot's
real tasks (01-06) are `Status: done` and merged. One additional stub,
`specs/narrow-autopilot/tasks/07-antigravity-build-md-char-cap.md`, was
discovered mid-drain and remains `Status: draft` — but it is an
unrelated documentation item (antigravity's `build.md` character count)
touching only `antigravity/.agents/workflows/build.md`, never
`.claude/skills/build/SKILL.md`. The line-shift race this precondition
guards against is fully resolved; the orchestrating session made this
call explicitly rather than waiting on task 07 (which was never part of
narrow-autopilot's original scope). Find the pre-commit-review bullet in
`build/SKILL.md`'s "## 4. Close out" section by content (the bullet
adjacent to the `/code-review` invocation), not by a line number — the
spec's own line references are pre-narrow-autopilot snapshots.

## Steps

1. The blocking precondition above is already confirmed cleared (human
   judgment call, 2026-07-15) — no re-check needed; proceed directly.
2. Add a "## Documentation currency" section to
   `.claude/rules/quality-discipline.md`, alongside its existing TDD/
   Commits/Checks sections, scoped explicitly to `/build`'s attended
   completion step (not "any code change" — match the Out-of-scope
   exclusion in ../SPEC.md).
3. In `.claude/skills/build/SKILL.md`'s "## 4. Close out" section, at the
   pre-commit-review bullet: add a one-line citation to the new
   quality-discipline.md section (don't restate its content), and a
   separate one-line note using the exact phrase "not by /code-review
   itself" (no backticks around `/code-review`) distinguishing this
   spec's doc-currency check from the `/code-review` invocation nearby.
4. Bump `.claude-plugin/plugin.json`'s `version`.
5. Run `bash evals/lint-ultra-gate.sh` — `build/SKILL.md` is one of the
   four ultra-path skills it checks; this task edits it directly.

## Acceptance

- [x] `grep -c "Documentation currency" .claude/rules/quality-discipline.md`
      → 1 or more. Evidence: returns 1 (base commit afcd8a8).
- [x] `grep -c "Documentation currency" .claude/skills/build/SKILL.md`
      → 1 or more. Evidence: returns 1.
- [x] `grep -c "not by /code-review itself" .claude/skills/build/SKILL.md`
      → 1 or more. Evidence: returns 1 (phrase present, no backticks around /code-review).
- [x] `.claude-plugin/plugin.json`'s version is higher than its value at
      this task's own base commit (`git show <base-commit>:.claude-plugin/plugin.json | grep version`
      compared against the current value, not a hard-coded prior literal).
      Evidence: base b5acb52 = 0.9.10, current = 0.9.11 (strictly higher).
- [x] `bash evals/lint-ultra-gate.sh` exits 0. Evidence: "OK — all ultra
      mentions gated in 4 files", exit 0.
- [ ] **Manual-pending** (cannot be verified by an unattended
      worker/verifier — `/build` carries the launch-authorization
      contract, not something an unattended worker holds): a human runs
      `/build` on a fixture task that adds a new top-level directory with
      no `AGENTS.md` mention in the task's `Touch:` header, and confirms
      the completed task's commit includes an `AGENTS.md` Map update
      because the new quality-discipline.md check fired at completion
      time. Record the observation in the task's evidence, not as an
      automated check.
