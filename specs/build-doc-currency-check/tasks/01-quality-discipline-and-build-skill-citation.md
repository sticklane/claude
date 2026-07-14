# Task 01: Add Documentation-currency section and cite it from build/SKILL.md's close-out

Status: blocked
Unblock: run: for f in specs/narrow-autopilot/tasks/*.md; do grep -q '^Status: done' "$f" || echo "not done: $f"; done
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

**BLOCKING PRECONDITION — do not start until unblocked.** `specs/narrow-autopilot`
also edits `.claude/skills/build/SKILL.md` (inserting a classification gate
"near its start," shifting every line number after it) and must land
first — both specs' own text state this explicitly (this spec's Sequencing
note; narrow-autopilot's Problem section and critique-findings finding 6).
This task's `Unblock: run:` line checks that every narrow-autopilot task
file reads `Status: done`; if it doesn't, STOP — do not edit
`build/SKILL.md` regardless of what this task file's other content says.
Once narrow-autopilot has landed, find the pre-commit-review bullet in
`build/SKILL.md`'s "## 4. Close out" section by content (the bullet
adjacent to the `/code-review` invocation), not by a line number — the
spec's own line references are pre-narrow-autopilot snapshots.

## Steps

1. Confirm the blocking precondition above is satisfied (re-run the
   `Unblock: run:` check yourself before editing).
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

- [ ] `grep -c "Documentation currency" .claude/rules/quality-discipline.md`
      → 1 or more.
- [ ] `grep -c "Documentation currency" .claude/skills/build/SKILL.md`
      → 1 or more.
- [ ] `grep -c "not by /code-review itself" .claude/skills/build/SKILL.md`
      → 1 or more.
- [ ] `.claude-plugin/plugin.json`'s version is higher than its value at
      this task's own base commit (`git show <base-commit>:.claude-plugin/plugin.json | grep version`
      compared against the current value, not a hard-coded prior literal).
- [ ] `bash evals/lint-ultra-gate.sh` exits 0.
- [ ] **Manual-pending** (cannot be verified by an unattended
      worker/verifier — `/build` carries the launch-authorization
      contract, not something an unattended worker holds): a human runs
      `/build` on a fixture task that adds a new top-level directory with
      no `AGENTS.md` mention in the task's `Touch:` header, and confirms
      the completed task's commit includes an `AGENTS.md` Map update
      because the new quality-discipline.md check fired at completion
      time. Record the observation in the task's evidence, not as an
      automated check.
