# Task 04: reclassify live-session / active-drain repos out of the attention inbox

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: pending
Depends on: 03
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R10; builds on R6; cross-cutting R8, R9)
Touch: .claude/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, .claude-plugin/plugin.json, ../SPEC.md

## Goal

The attention inbox flags a repo's uncommitted / unpushed git state as
`needs-review` even when a live session or an active drain owns that repo —
misleading, because that state is expected work-in-progress, not neglected
work. `attention_items()` lives at
`.claude/skills/workboard/workboard.py` L655–739 (`def attention_items(...)`
at L655; its closing `return items` is L739). Three concrete defects:

1. **Active drains are not recognized as coverage.** Suppression keys off
   `active_cwds` (L661:
   `{s["cwd"] for s in sessions if s["state"] == "active" and s["cwd"]}`);
   `covered_by_active` is then computed at L665–666 by raw path-prefix
   (`c == rp or c.startswith(rp + os.sep)`). A background drain's workers are
   Task-tool sub-agents that never emit their own top-level
   `~/.claude/projects/*.jsonl` session records, so their `cwd` never enters
   `sessions` / `active_cwds`. Coverage then hinges entirely on the `/drain`
   **orchestrator** session's `cwd`: if that does not resolve at/under the
   repo (e.g. the orchestrator was launched from `$HOME`), the repo is
   uncovered and its in-progress artifacts flag. The worker worktrees
   themselves live on a `task/NN-<slug>` branch under `.claude/worktrees/`
   (inside the repo root, background path) or at a sibling `../<repo>-task-NN`
   (headless-fallback path) — but **neither location is currently consulted
   for coverage**. `scan_batons()` (L414) parses `DRAIN-BATON.md` but returns
   only `{path, generation, command, needs_attention, mtime}` — **no PID and
   no session linkage** — and is not wired into suppression.
2. **Unpushed commits are never suppressed.** The `covered_by_active` guard
   is on the uncommitted-changes branch (L708:
   `if r["git"]["dirty"] and not covered_by_active:`) but absent from the
   unpushed-commits branch (L716–724: `if r["git"]["ahead"]:` … `items.append`,
   with no coverage guard), so even a normal live session's unpushed commits
   flag.
3. **Path-prefix over-match wrongly covers parents.** Because L665–666 uses
   raw `cwd` string-prefix, a live session whose `cwd` is inside a **nested**
   git repo (or a worktree) physically under `rp` marks the *parent* `rp` as
   covered. `assemble()` adds the nested repo as its own scan entry via
   `git rev-parse --show-toplevel` (L750), so the parent's genuinely-stranded
   dirty/unpushed state gets wrongly reclassified as owned by a session that
   actually owns the child.

Note on the existing worktree scan: there is **no** dedicated
`.claude/worktrees/*` filesystem scan, and `find_repos` prunes dot-dirs (L122)
so it never walks into `.claude/`. `git_info` (L144–164) *does* run
`git worktree list --porcelain` and populates `r["git"]["worktrees"]` with
path + branch (excluding the main checkout) — but it ignores the porcelain
`locked` line, does not filter to any branch pattern, and this data feeds only
HTML chip rendering (L946), never `attention_items()` suppression. So a
worktree-list parser exists to build on; lock/recency detection, the `task/*`
filter, and the wiring into suppression must all be **added**.

## Answers

**Decision (interview 2026-07-04) — the two locked decisions:**

- **Reclassify, do not hide.** A repo with a live session OR an active drain
  keeps its uncommitted/unpushed items *visible*, but moved out of the
  needs-attention inbox into a distinct **"Active / in-progress"** group,
  labeled as owned by a live session/drain. Rationale: suppressing entirely
  makes live WIP invisible if the owning session dies mid-flight; an Active
  group is honest without being alarming. (Builds on task 03's grouped-inbox
  infrastructure — Active is a new group alongside `blocked` / `needs-review`
  / `stale`, rendered *after* the attention groups.)
- **Unpushed follows the same rule as uncommitted.** Apply the live/drain
  coverage test to the unpushed-commits branch too (fixes the asymmetry at
  L716–724), so a live/draining repo's unpushed commits also land in the
  Active group.

**Resolved design decisions (fold into implementation):**

- **Human-session coverage matches on git toplevel equality, not path
  prefix.** `assemble()` already runs `git rev-parse --show-toplevel` per
  session (L750) but discards it — attach it to each session record and test
  `session_toplevel == rp`. This kills the nested-repo/worktree false cover
  (defect 3), keeps an "unrelated subdir in the same repo" session correctly
  covered (same toplevel), and cleanly separates human-session coverage
  (toplevel match) from drain coverage (worktree-activity signal), which is
  required because a worktree session's toplevel is the worktree, not `rp`.
- **Drain coverage is driven off `git_info`'s already-parsed worktree list,
  keyed on branch pattern, and gated on recency.** Detect a drain as any
  worktree whose branch `startswith("task/")` (catches BOTH the
  `.claude/worktrees/*` background path AND the sibling `../<repo>-task-NN`
  headless-fallback path — zero new globbing). Do **not** key on the lock or
  the branch's mere presence: a crashed drain leaves the worktree *still
  locked* and *still on* `task/*` (git never unlocks or renames on crash), so
  lock/branch presence is identical for the live and the stranded case.
- **Liveness is recency, not PID.** Add a per-worktree newest-activity
  timestamp to `git_info` (max file mtime under the worktree, excluding
  `.git/` and `node_modules/`, OR the branch tip-commit time). A `task/*`
  worktree counts as a **live drain** only if its newest activity is younger
  than a dedicated **drain window** (default 15m, configurable) — matching the
  grace window in `drain/reference.md:69`. Older ⇒ stranded ⇒ still flags. Do
  NOT use the worktree lock's PID (`drain/reference.md:86`: "The worktree
  lock's recorded pid is not a liveness signal") and do NOT reuse
  `--stale-days` (7d is far too coarse — a 6-day-idle abandoned drain would
  wrongly read Active).
- **Drop the baton as a coverage signal.** `scan_batons()` exposes no PID and
  no session linkage, and its `mtime` is written once at pass time and never
  refreshed — a parked baton is a *paused* generation whose relaunch chain may
  have died, exactly the stranded case. The `task/*` worktree activity window
  is the **sole** drain-coverage signal. A parked baton is already surfaced
  separately (relaunch item / ready) and must not suppress git-state flags.
- **Count contract.** Reclassified items get a distinct state
  (`in-progress`) and category (`active`), and are **excluded** from
  `totals["attention"]` (L801) — compute the attention total as the count of
  inbox items whose state is not `in-progress` (or move them to a separate
  `data["active"]` list). Categorization is asserted at the
  `attention_items()` return-value level so no HTML-grouping assertion is
  needed.
- **SPEC amendment (part of this task).** Add requirement **R10**
  (active-coverage reclassification: the drain live-vs-stale signal, the
  toplevel human-session signal, and the Active group) to `../SPEC.md`, and
  update its Parallelization line from `01 -> 02 -> 03` to
  `01 -> 02 -> 03 -> 04` (strict serial: 04 depends on 03 and edits the same
  file).

## Active-coverage signal (implementer guidance)

A repo counts as **actively covered** if EITHER:

- **Live human session:** some session's `git rev-parse --show-toplevel`
  equals `rp` (toplevel equality; replaces the L665–666 prefix match), OR
- **Live drain:** the repo has at least one worktree (from
  `r["git"]["worktrees"]`) whose branch `startswith("task/")` **and** whose
  newest-activity timestamp is within the drain window (default 15m).

A `task/*` worktree whose newest activity is *older* than the drain window is
**stale** — the genuine "drain died, work stranded" case that SHOULD flag.
Live vs. stale differ ONLY by recency, never by lock or branch state.

## Render / grouping

- Name the new state `in-progress` and category `active`. Add a
  `STATE_BADGE` row for it (L811–820; the existing `active` → ●/good badge is
  for sessions, not this) and a legend sentence in the inbox legend
  (TEMPLATE L1152–1155) describing the Active group and its
  render-after-attention position.
- Render the Active section **only when it has items** (conditional-section
  pattern), rendered after `blocked` / `needs-review` / `stale`. Ensure the
  needs-attention "Inbox zero 🎉" message does not fire while Active is
  non-empty.
- Reword the reclassified items' `what` / `why` from neglect-framed copy
  ("no live session" L712; "push or open a PR — local-only work is invisible
  work" L721) to owned-WIP framing (e.g. "uncommitted changes — a live
  session/drain is working here").
- Add an **Active filter tile** with its own count to task 03's tile row
  (tile-building loop L905–915), so the group is filterable like the others.

## Acceptance

- `attention_items()` moves uncommitted AND unpushed items for an
  actively-covered repo into the `active` category / `in-progress` state
  instead of emitting them at `needs-review`; non-covered repos are unchanged.
- Reclassified items are excluded from `totals["attention"]`: an
  actively-covered dirty/unpushed repo does not increment the needs-attention
  headline count.
- A repo under a **live drain** (a `task/*` worktree whose newest activity is
  within the drain window) is actively covered even though no session toplevel
  equals it — regression test encodes the case that misfired this session
  (drain live, orchestrator session cwd not under the repo).
- A repo with a **stale** `task/*` worktree (newest activity older than the
  drain window) still flags — the "stranded work" case is preserved. The live
  and stale fixtures differ ONLY by worktree activity mtime, not by lock or
  PID state.
- New `test_workboard.py` cases cover: (a) live-session repo (session toplevel
  == repo) → `active`, not needs-review, for both dirty and unpushed;
  (b) live-drain repo → `active`; (c) stale `task/*` worktree → still
  needs-review; (d) **decay** — a repo that is `active` while covered returns
  to needs-review once the covering session's toplevel is gone / the
  worktree's activity ages past the drain window. Fixtures use synthetic git
  repos, never real `~/.claude` paths, so they pass under both the `.claude`
  and Antigravity mirrors. Existing tests unchanged/green.
- SPEC amended: `../SPEC.md` contains requirement R10 and its Parallelization
  line reads `01 -> 02 -> 03 -> 04`.
- Antigravity mirror carries the same change in the same commit (both
  `workboard.py` paths, and both `test_workboard.py` mirrors if the mirror
  test is kept in sync); `.claude-plugin/plugin.json` version bumped
  (0.7.2 → 0.7.3, behavior change).

Acceptance commands:

- `python3 -m unittest discover -s .claude/skills/workboard`
- `git diff HEAD~1 -- .claude-plugin/plugin.json` (shows the version bump; R9)
- `git show --stat HEAD` (shows the commit touches BOTH `workboard.py` paths; R9)

## Open questions

- Is the Antigravity mirror test at
  `antigravity/.agents/skills/workboard/test_workboard.py` maintained in sync
  with the `.claude` copy? It is on the Touch list on the assumption that it
  is; drop it from Touch if the mirror test is not kept in lockstep.
- Exact name/default of the configurable drain-window knob (proposed default
  15m per `drain/reference.md:69`) — confirm against any existing workboard
  CLI flag naming convention before adding a new one.
