# Verification evidence — repo-orientation task 01 (R1, R2, R3)

Verdict: PASS
Verified: 2026-07-03, working tree at branch task/01-orientation-artifacts
(all changes uncommitted: `git status` shows `M CLAUDE.md`, untracked
`AGENTS.md`, `specs/status.sh`; branch has no commits vs main, so working
tree was verified per caller instruction).

## Acceptance commands (run from repo root)

1. R1 structure — exit 0
   `test -f AGENTS.md && grep -q "^## Repo map" AGENTS.md && grep -q "^## State" AGENTS.md && grep -q "^## Commands" AGENTS.md && [ "$(wc -l < AGENTS.md)" -le 60 ]`
   AGENTS.md = 35 lines (limit 60). Three sections present.

2. R1 State content — exit 0
   `grep -q "specs/QUEUE.md" AGENTS.md && grep -q "status.sh" AGENTS.md && grep -q "HANDOFF.md" AGENTS.md && grep -q "Status:" AGENTS.md`

3. R2 — exit 0
   `head -10 CLAUDE.md | grep -q "AGENTS.md" && [ "$(wc -l < CLAUDE.md)" -le 200 ]`
   CLAUDE.md = 89 lines. `git diff main -- CLAUDE.md` = exactly one added
   line at line 8: "Orientation — repo map, live work state, verified
   commands — is in @AGENTS.md." No orientation content duplicated.

4. R3 script hygiene — exit 0
   `test -x specs/status.sh && bash -n specs/status.sh && [ "$(wc -l < specs/status.sh)" -le 40 ]`
   status.sh = 33 lines, executable, syntax-clean.

5. R3 normal run — exit 0
   `out=$(mktemp) && ./specs/status.sh > "$out" && grep -q "TOTAL" "$out" && for f in specs/*/tasks/*.md; do grep -q "$f" "$out" || exit 1; done`
   All 30 task files appear. TOTAL tail:
   ```
   TOTAL
     done: 20
     in-progress: 2
     pending: 8
     all: 30
   ```

6. R3 empty queue — exit 0
   `d=$(mktemp -d) && mkdir -p "$d/specs" && (cd "$d" && bash "$OLDPWD/specs/status.sh")`
   Output: "Queue is empty: no task files under specs/*/tasks/."

## R3 detail checks

- No arguments taken; scans `specs/*/tasks/*.md`. Confirmed by read.
- FIRST `^Status:` anywhere in file: constructed throwaway test in a
  mktemp dir under the scratchpad (NOT under repo specs/) with a file
  whose `Status: buried` sits below a comment block and a second
  `Status: second` later — output row was `buried`, first line wins.
  (The spec's cited example file specs/skill-evals/tasks/01-evals-harness.md
  no longer exists in the tree; the constructed test covers the rule.)
- File with no Status line prints `none`: same temp test, row `none`.
- POSIX only: sh, sed, sort, uniq, grep, printf. No jq, no network calls.
- Writes nothing; exits 0 on both normal (exit=0) and empty-queue (exit=0).

## Commands section truthfulness (spec: every listed command re-run)

- `./specs/status.sh` — exit 0 (above).
- `claude plugin validate .` — exit 0, "Validation passed".
- `for t in tests/test_*.sh; do bash "$t"; done` — all pass, no failures.
- `./evals/runner-selftest.sh` — exit 0, "runner selftest: OK (PASS and
  FAIL plumbing verified ...)".

## Manual dry-read (spec end-to-end criterion)

Reading ONLY AGENTS.md plus the status.sh output answers all five:
(a) what the repo is — opening paragraph (toolkit for agent-driven spec
pipeline, distributed as plugin `agentic`); (b) where things live — Repo
map lists all 9 actual top-level dirs (verified against `ls`), calling out
`.claude/` skills/agents/rules, `specs/` with QUEUE.md, `docs/`, `evals/`;
(c) verified commands — Commands section, each with a half-line, all
re-verified above; (d) open work — dashboard: 30 tasks, 20 done /
2 in-progress / 8 pending; (e) handoff location — State section:
HANDOFF.md next to the active task/spec file (or .claude/HANDOFF.md).
Judgment: criterion met.

## Scope / gates

- Diff vs main (working tree): CLAUDE.md +1 line; new AGENTS.md; new
  specs/status.sh. Task file unchanged vs main. No other files touched.
- plugin.json NOT bumped: no diff vs main, version stays 0.6.2 —
  matches the task's "review-fixes 99 owns the bump" instruction.
- No scope creep; no overfitting (status.sh is generic, survives
  constructed variations).
- Note (non-blocking): work is uncommitted on the branch; caller
  directed working-tree verification.
