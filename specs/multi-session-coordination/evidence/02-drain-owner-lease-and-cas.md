# Verification: 02-drain-owner-lease-and-cas

Verdict: PASS (with one process finding: work is uncommitted)

Base commit: 006ed266161b7b9ad6c2aaee5b450150b631bf3e
Worktree HEAD at verification time: still 006ed266... (no new commit) —
changes are staged/unstaged in the working tree only.

## Acceptance checkboxes — commands actually run

1. `grep -c "DRAIN-OWNER" .claude/skills/drain/SKILL.md` → 5 (≥2 ✓)
   `grep -c "DRAIN-OWNER" .claude/skills/drain/reference.md` → 5 (≥1 ✓)
   PASS — matches claimed evidence (SKILL.md 5, reference.md 5).

2. `grep -c "Run-token" .claude/skills/drain/reference.md` → 5 (≥2 ✓)
   PASS — matches claimed evidence (5).

3. `grep -ciE "compare-and-swap|exact-match" .claude/skills/drain/SKILL.md` → 3 (≥1 ✓)
   PASS — matches claimed evidence (3).

4. `grep -c "path-scoped" .claude/skills/drain/SKILL.md` → 8 (≥1 ✓)
   `grep -c "pull --rebase" .claude/skills/drain/SKILL.md` → 1 (≥1 ✓)
   PASS — matches claimed evidence (8 and 1).

5. `grep -c "claude agents --json" .claude/skills/drain/SKILL.md` → 1 (≥1 ✓)
   PASS — matches claimed evidence (1).

6. `bash evals/lint-ultra-gate.sh` → exit 0
   Output: "lint-ultra-gate: OK — all ultra mentions gated in 4 files"
   PASS — matches claimed evidence.

7. `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./specs/status.sh && claude plugin validate .`
   All 9 test_*.sh files ran with 0 failures each:
     test_check_token_discipline.sh: pass 55 fail 0
     test_doc_links.sh: pass 14 fail 0
     test_drain_owner_protocol.sh: PASS (d) losing claim, PASS (e) baton
       adoption predicate, pass 13 fail 0 (all 5 lettered cases a-e passed)
     test_hook_templates.sh: pass 77 fail 0
     test_install_gates.sh: pass 159 fail 0
     test_review_skip.sh: pass 9 fail 0
     test_sync_workflows.sh: passed 28 failed 0
     test_workboard_actionability.sh: PASS
     test_workboard_render.sh: PASS
   `./specs/status.sh` ran, listed the queue (TOTAL done:20 draft:6
   pending:8 all:34), exit 0.
   `claude plugin validate .` → "✔ Validation passed", exit 0.
   PASS — matches claimed evidence, full chain exits 0.

## Semantic check of R1-R7 against the diff (git diff 006ed26 -- SKILL.md reference.md)

(a) Owner claim before step 1's dispatch-plan report; release at step 4:
    CONFIRMED. SKILL.md inserts "**Claim the owner lease, before reporting
    the plan below.**" immediately under "## 1. Inventory", before the
    "Report the plan in one block" line. Release text: "Release: the
    terminal report (queue empty / only blocked / interview handoff to
    human, step 4) deletes the owner file..." — correctly tied to step 4.

(b) Refuse-on-live-owner path reports owner evidence + freshest-signal
    age + other dispatchable specs:
    CONFIRMED. "FRESH ... → REFUSE — report the owner file's headers, the
    freshest signal and its age, and any other specs with dispatchable
    tasks, then stop".

(c) Baton-lineage exception's adoption predicate matches Run-token
    exactly, matching test_drain_owner_protocol.sh case (e):
    CONFIRMED. SKILL.md: "UNLESS this generation was launched via the
    baton relaunch command and its baton's `Run-token:` matches
    DRAIN-OWNER.md's". reference.md "Baton-lineage exception": "adopts a
    FRESH existing owner ... iff the baton's `Run-token:` line ... matches
    DRAIN-OWNER.md's." Test case (e)'s `adopt()` helper does exactly this
    string-equality comparison of the `Run-token:` grep line; ran the test
    directly, both sub-assertions passed ("PASS: (e) baton adoption
    predicate").

(d) Foreign-reclaim tightening requires BOTH stale signals AND no
    `git worktree list` checkout:
    CONFIRMED, and consistent between the two files. reference.md: "a
    task is swept ... only when BOTH hold: its activity signals are
    stale, AND `git worktree list` shows no worktree checked out on its
    `task/NN-<slug>` branch". SKILL.md restates the same conjunction.

(e) CAS flip requires fresh-read + exact-match + path-scoped-commit +
    post-commit HEAD verify:
    CONFIRMED. SKILL.md step 2: "Re-read the task file immediately before
    flipping — the flip is an exact-match edit of the literal `Status:
    pending` line ... Set `Status: in-progress` and commit that edit,
    path-scoped to the task file ... then push ... After committing,
    re-read the file at HEAD and confirm your own flip is present before
    dispatching." All four elements present. test_drain_owner_protocol.sh
    case (a) exercises the exact-match precondition mechanically and
    passed.

(f) Push guard extension covers every bookkeeping commit, not just DONE
    merges, and cites the `pull --rebase` dropped-commit rationale:
    CONFIRMED. "extended here to every drain bookkeeping commit — not
    only DONE merges — since a concurrent session's `pull --rebase` has
    been observed to drop unpushed drain commits:
    docs/memory/concurrent-session-collision.md" — file exists (verified
    with `ls`), and the extension is explicitly applied to "the owner
    claim/release commits (step 1), every flip (step 2), and the
    Deferred/Blocked/discovery commits below".

(g) Sweep is advisory/non-blocking, `claude agents --json` primary path,
    pid-record fallback:
    CONFIRMED. "Startup session sweep (advisory) ... `claude agents
    --json`, filtered by cwd the way `agent-console/agent-console.py`'s
    `live_sessions_from_cli` (≈429–490) does; if the CLI is unavailable,
    fall back to `~/.claude/sessions/*.json` pid records probed with
    `kill -0` ... this check is advisory only and never blocks dispatch".
    Verified `live_sessions_from_cli` is defined at line 430 of
    agent-console/agent-console.py, matching the cited ≈429-490 range.

R3 (owner-liveness definition, TaskList session-local) also confirmed
present in reference.md's new "Owner lease" section: liveness = newest of
spec-dir commit recency and per-task stale-lock signals vs the grace
window; "`TaskList` is explicitly session-local ... MUST NOT be treated
as evidence about another session's activity."

No keyword-stuffing observed — the grepped terms appear inside complete,
mechanically-coherent procedural prose that matches the model-free test
suite's actual exercised behavior (test_drain_owner_protocol.sh cases
a-e), not just incidental mentions.

## Append-only task-file check

Command: `git diff 006ed266161b7b9ad6c2aaee5b450150b631bf3e..HEAD -- '*/tasks/*.md'`
Output: empty — because HEAD has not advanced past the base commit (no
commit was made; see Process finding below).

Fallback check against the actual uncommitted working-tree diff
(`git diff HEAD -- specs/multi-session-coordination/tasks/02-drain-owner-lease-and-cas.md`,
and `git status --porcelain=v1`):
- Only ONE task file is modified anywhere in the working tree:
  specs/multi-session-coordination/tasks/02-drain-owner-lease-and-cas.md.
  No other spec's tasks/*.md file is touched.
- The only changes to that file are: the `Status:` header
  (`in-progress` → `done`), and the 7 acceptance checkboxes
  (`[ ]` → `[x]` plus an appended `— evidence: ...` line each). Goal,
  Steps, Touch, Budget, Acceptance criterion text are byte-for-byte
  unchanged. This satisfies the append-only worker contract.

## Scope check (Touch: list)

Task's Touch: `.claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md`.
`git status --porcelain=v1` shows exactly:
```
 M .claude/skills/drain/SKILL.md
 M .claude/skills/drain/reference.md
MM specs/multi-session-coordination/tasks/02-drain-owner-lease-and-cas.md
```
No untracked files, no other files touched. Scope is clean — matches
Touch list plus the task file itself (task-file self-update is implicitly
allowed/expected).

## Gates

- `bash evals/lint-ultra-gate.sh` → exit 0 (see above).
- Full test sweep (`tests/test_*.sh`) → all pass, 0 failures.
- `./specs/status.sh` → ran cleanly, exit 0.
- `claude plugin validate .` → "✔ Validation passed", exit 0.

## Findings

1. PROCESS FINDING (not a criterion failure, but a real gap): none of the
   edits have been committed. `git log --oneline 006ed26..HEAD` is empty;
   `git status` shows all three files as staged/partially-staged
   modifications against base HEAD 006ed26, not committed. The task's own
   Step 3 says "Run the acceptance greps and the full test sweep; commit"
   and CLAUDE.md / the toolkit's own quality-discipline rule both require
   never leaving finished work uncommitted. Since drain/verification
   workflows key off committed state (e.g. the append-only task-diff
   check above returned empty specifically because there is no commit
   yet), this should be committed before the task can be considered truly
   "done" in the queue sense, even though the file content and all
   acceptance commands already pass against the working tree.
2. No scope creep: diff limited to the two Touch-listed files plus the
   task file's own Status/checkbox/evidence lines.
3. No evidence of keyword-stuffing / overfitting to the test file — the
   test file (tests/test_drain_owner_protocol.sh) was not modified in
   this diff (it's outside Touch and outside the base->working-tree diff
   for SKILL.md/reference.md); it appears to have been added by an
   earlier/different task and this task's prose was written to genuinely
   satisfy its mechanics, which the test run confirms.

## Overall verdict

PASS on all 7 acceptance checkboxes and the R1-R7 semantic checks.
FINDING (not a checkbox failure): the work is uncommitted in this
worktree — flagged for the caller to decide whether that blocks
queue-completion sign-off.
