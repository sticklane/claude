Depends on: agentic-zz3k (closed, merged)
Priority: P0
Budget: 40 turns
Touch: bin/drain-release-worktrees, tests/test_drain_release_worktrees.sh, .claude/skills/drain/SKILL.md, specs/toolkit-core-simplification/surface-inventory/drain-release-worktrees.json, tests/inventory/drain-release-worktrees.json
Rigor: production

# agentic-v50x — drain releases every worktree on a branch it lands

## Goal

A new `bin/drain-release-worktrees <branch>` removes every worktree carrying
that branch, salvaging any unique content first, then deletes the branch when
it is merged. `/drain`'s SKILL.md step 3 calls it as part of the same close-out
unit that already drops the inflight marker, removes the staging file, and runs
`bd close`.

## Evidence (measured 2026-07-30, one drain run)

The census went **17 → 21** worktrees while janitor's sweep removed 7 — waves
4–6 created eleven. Reclamation loses to accumulation because nothing removes a
worker's worktree when its issue closes.

**15 candidates** then skipped with `branch checked out by another worktree`.
Every findings-fix round left TWO worktrees on one branch: the harness gives
each `isolation: worktree` agent a fresh worktree, and a fix worker that cannot
operate in the original uses `git switch --ignore-other-worktrees` to bring the
branch into its own. Janitor correctly refuses a branch checked out twice, so
the accumulation bug now blocks its own cleanup.

Accumulation is structural: the harness auto-removes a worktree only if it is
UNCHANGED, so every worktree that did real work survives by construction.

## Scope

**Iterate every worktree on the branch, never resolve one.** That is the whole
point — duplicates are what janitor cannot handle, and releasing all of them
makes duplicates harmless without needing to prevent them.

**Reuse janitor's classification; do not reimplement it.** `agentic-zz3k`
landed the three-way rule (clean / reconstructible / unique → salvage first)
with test coverage in `bin/janitor`. Call it, or extract the shared decision
into one place that both use. A second copy of that logic is a defect, not an
implementation choice.

**Never destroy unique content.** A worktree whose content matches no commit
reachable from its branch is committed to a `salvage/` ref BEFORE its directory
is removed, exactly as janitor does.

**Refuse rather than guess.** If the branch is not merged into the default
branch, do not delete it — the branch is the archive until it lands. Removing
worktrees is still fine; deleting an unmerged branch is not.

Never touch the shared checkout (the worktree whose path is the repository
root), and never a worktree a live session is using — janitor's existing
live-session check applies here too.

The SKILL.md edit is small: name the release step inside step 3's close-out
unit so it is one transition with the other three side effects. Do not
restructure the step.

## Steps

1. Write `tests/test_drain_release_worktrees.sh` FIRST, with real throwaway git
   repositories as fixtures — never against this repo's own worktrees. Confirm
   it fails for the right reason.
2. Implement `bin/drain-release-worktrees`.
3. Add the call to `.claude/skills/drain/SKILL.md` step 3.
4. Register the new script and test in both inventories, writing each fragment
   correct in the SINGLE commit that introduces it (`agentic-1t9d`).

## Acceptance

- [ ] A1 (cheap): `bash tests/test_drain_release_worktrees.sh` exits 0 with 0
      failures.
- [ ] A2 (cheap): the test asserts a branch carrying TWO worktrees has BOTH
      removed by one invocation — the duplicate case that blocks janitor today.
- [ ] A3 (cheap): the test asserts a worktree holding unique content gets a
      `salvage/` ref whose contents are recoverable byte-for-byte, and that its
      directory is removed only after the ref exists.
- [ ] A4 (cheap): the test asserts a MERGED branch is deleted after its
      worktrees are released, and an UNMERGED branch is NOT deleted while its
      worktrees are still released.
- [ ] A5 (cheap): the test asserts the shared checkout is never removed, and a
      worktree belonging to a live session is never removed.
- [ ] A6 (cheap): the classification is not duplicated —
      `grep -c 'janitor' bin/drain-release-worktrees` returns at least 1,
      evidencing reuse. State in your return which mechanism you used and why
      it is genuinely shared rather than copied.
- [ ] A7 (cheap): `.claude/skills/drain/SKILL.md` names the release step inside
      step 3. Anchor structurally, not on a file-wide literal:
      `awk '/^3\. \*\*Verify each verdict/{f=1} f&&/^4\. \*\*Loop/{exit} f' .claude/skills/drain/SKILL.md | grep -c 'drain-release-worktrees'`
      returns at least 1. Confirmed absent today: that grep returns 0 on main.
- [ ] A8 (cheap): `wc -l < .claude/skills/drain/SKILL.md` stays under 500.
- [ ] A9 (cheap): `bash tests/test_drain_touch_claims.sh` exits 0 — the
      SKILL.md edit does not disturb the phrases that suite pins.
- [ ] A10 (cheap): `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json`
      exits 0, and `bash tests/test_check_inventory.sh` exits 0.
- [ ] A11 (cheap): `bash tests/test_janitor_worktree_sweep.sh` and
      `bash tests/test_janitor_candidate_report.sh` both still exit 0 — janitor
      does not regress.

## Notes

Do not run `scripts/check.sh`; drain runs the canonical gate once after an
independent review barrier.

`tests/test_janitor_worktree_sweep.sh` is classified `retain` in a fragment,
which freezes its bytes permanently (`agentic-jnxl`). Do not attempt to edit
it; add new assertions to your own new test file.

`grep` here wraps ugrep 7.5.0 and omits the leading `./` when recursing `.`, so
`grep -v '^\./…'` exclusions silently match nothing
(docs/memory/anchored-acceptance-criteria.md).
