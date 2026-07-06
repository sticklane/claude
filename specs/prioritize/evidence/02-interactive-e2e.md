# Evidence: /prioritize interactive end-to-end (spec acceptance bullets 4–7)

Date: 2026-07-05. Method: headless `claude -p` sessions drive the skill
against a throwaway fixture repo; the `disable-model-invocation: true`
restriction was removed ONLY in the fixture's copy of SKILL.md (production
`.claude/skills/prioritize/SKILL.md` was never modified — `git status`
clean throughout). The scripted "reply" is supplied in the initial prompt
since a headless session has no second turn; the skill still asked its R3
question verbatim before consuming it. Model: sonnet,
`--permission-mode bypassPermissions --max-turns 25`.

Fixture: 2 specs (`alpha`, `beta`) + `specs/archive/gamma` decoy;
statuses pending/blocked/deferred/done/draft; `alpha/02-fix-cache.md` has
no `Priority:` header. Baseline commit `2a0c527`; each run starts from a
hard reset to it. Scanner sanity (deterministic): 3 rows
(`alpha/01` P1, `alpha/02` "P2 (default)", `beta/01` P3); done, draft,
and archive tasks excluded.

## Run A — apply one change (spec bullet 4): PASS

Reply: `make alpha/02-fix-cache.md P0. Everything else stays.`
- One new commit `b088c1a`, message exactly
  `chore: reprioritize 1 task(s) across 1 spec(s) per interview` (R6).
- `git show --stat` → only `specs/alpha/tasks/02-fix-cache.md`, 1 insertion.
- `Priority: P0` inserted immediately below `Status:` (R5 no-header path).
- Tree clean; other rows reported unchanged.

## Run B — invalid Ref + valid change (spec bullet 5): PASS

Reply: `make alpha/99-typo.md P1, and make beta/01-docs-pass.md P1.`
- Session reported: `Not applied: alpha/99-typo.md — not a valid Ref; it
  doesn't match any row in the scanned table` (R4, no guessing).
- Valid change still applied: `beta/01-docs-pass.md` `Priority: P3` → `P1`
  replaced in place on its original line (R5 in-place path).
- One commit `48881d9` touching only that file; tree clean.

## Run C — reply "none" (spec bullet 6): PASS

- R3 question asked verbatim (`What changes should I make? Reference tasks
  by their Ref … Say 'none' if you're done looking.`).
- No commit (log unchanged at `2a0c527`), `git status` and `git diff`
  empty (R7).

## Run D — real repo, production flag intact (spec bullet 7, read-only half): PASS

`claude -p "/prioritize …reply: none"` from `/Users/sjaconette/claude`
with the UNMODIFIED production SKILL.md (`disable-model-invocation: true`
present — a user-typed invocation still triggers it; the flag only blocks
model-initiated invocation):
- Skill triggered, asked the R3 question (which the procedure reaches only
  after relaying the table), exited with no edits and no commit;
  `git rev-parse HEAD` identical before/after.
- Deterministic table for the current repo, captured directly:
  5 pending tasks across absorb-agent-tools / drain-sweep-preservation /
  skill-profiling-workboard, priorities P0/P1/P2 rendered from headers.

Bullet 7's commit-producing half (a REAL reprioritization commit in this
repo) is deliberately not exercised by automation: inventing a priority
change would violate the skill's own "never invents an ordering" contract.
It is covered behaviorally by Run A/B; it completes naturally the first
time a human genuinely reprioritizes.
