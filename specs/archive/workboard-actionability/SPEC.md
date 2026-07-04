# Workboard actionability: surface ready work + batch the fixes

## Problem

The workboard dashboard (`.claude/skills/workboard/workboard.py`) is a
point-in-time snapshot that tells you what is *broken* — its attention
inbox (`attention_items()`, workboard.py:494–578) lists `blocked`,
`needs-review`, and `stale` items, each with a copy-paste `cmd` string.
Two things make acting on it slower than it should be:

1. **It never shows what's ready to START.** The board surfaces stuck
   work but has no view of *dispatchable* tasks — `Status: pending` tasks
   whose dependencies are all `done` — even though `/drain` already
   computes exactly that readiness deterministically
   (`.claude/skills/drain/SKILL.md:24–45`). To find the next thing to
   pick up you have to leave the board and run `/drain` or read
   `status.sh`.
2. **Every fix is a one-at-a-time copy-paste.** A routine sweep (e.g. 4
   repos to push, 4 done specs to verify) is 8 separate copy → terminal →
   paste → run cycles. The board emits the commands but never groups them
   into something runnable in one go.

The inbox is also a flat newest-first-within-severity list with no
category grouping, and the summary counts at the top are not clickable —
you can text-filter but you can't click "needs-review" to isolate it.

The clipboard *mechanics* (visible copy buttons, resilient fallback,
cwd-independent command normalization) are already owned by the open
`specs/workboard-copy-commands/` spec and are **out of scope here**; this
spec is independent of it and touches different code paths.

## Solution

Extend `workboard.py` along the actionability axis, all rendered into the
same self-contained static HTML (no server, no external requests):

- Compute a **Ready to start** list by parsing `Status:` (already read at
  workboard.py:173–218) plus a **newly added** `Depends on:` parse, and
  applying drain's dispatchability rule (resolving deps the way drain
  does), then render it as a distinct top section with a launch command
  per item.
- Write a **companion actions script** next to the HTML containing only
  the *safe, mechanical* batch fixes (repo pushes; verifier invocations),
  grouped into labeled, independently-runnable sections — never
  auto-archiving and never auto-launching workers.
- **Group and rank** the attention inbox by category, and make the
  top summary boxes **clickable filters** (embedded JS, toggle).

Real anchors: readiness data is already parsed at workboard.py:173–218;
attention items at :494–578; cmd generation at :513/:536; HTML template
at :823–929; existing text-filter JS at :912–913; output write at
:967–972. Dispatchability rule mirrored from drain (SKILL.md:24–45, with
the dep-resolution forms at SKILL.md:57–58): a task is dispatchable when
`Status: pending` AND every `Depends on:` id is `done`.

## Requirements

- **R1 — Readiness computation.** `workboard.py` gains a new
  `Depends on:` header parse (the scanner today reads only `Status:` at
  :173–218 — deps are NOT currently parsed) and computes, per toolkit
  spec (the `specs/<slug>/tasks/NN-*.md` files it scans), the set of
  *ready* tasks: a task is ready iff `Status: pending` AND every entry in
  its `Depends on:` header is *satisfied*. Parse and resolve deps exactly
  as `/drain` does (drain/SKILL.md:57–58 — "numbers within a spec,
  task-file-relative paths across specs"):
  - Split the header value on commas; trim each entry; `none`/empty ⇒ zero
    deps ⇒ ready.
  - A **bare numeric id** (`01`, `03`, `05`) refers to the sibling task
    file in the **same spec** whose filename begins with that
    zero-padded prefix (`01-*.md`).
  - A **task-file-relative path** entry
    (`../../orchestrator-context/tasks/02-*.md` or a `specs/...`-rooted
    path) refers to a task file in **another spec**, resolved relative to
    the current task file's directory (mirroring drain's cross-spec
    resolution). A `<slug>/NN` shorthand (e.g. `orchestrator-context/03`)
    resolves to `../<slug>/tasks/NN-*.md` relative to the current task
    dir — expand it to that form before resolving; it is NOT a literal
    child path of the current `tasks/` dir.
  - An entry is *satisfied* when its resolved task file has
    `Status: done`. If an entry cannot be resolved to an existing task
    file, the task is NOT ready and the item is recorded as
    blocked-by-unresolved with the offending id surfaced (so the gap is
    visible, not silently swallowed).
  Kiro/Antigravity specs are excluded from readiness (toolkit specs only).
- **R2 — Ready launch command.** Each ready item carries a `cmd`: if the
  task is the *only* ready task in its spec, `cd <quoted-repo> && claude
  "/build specs/<slug>/tasks/<resolved-filename>.md"` — a **repo-relative,
  fully-resolved** path (the actual filename, not a `NN-*.md` glob, since
  the glob sits inside the quoted `claude` arg and would not be
  shell-expanded); if a spec has *two or more* ready tasks, emit one
  spec-level item instead with `cd <quoted-repo> && claude "/drain
  specs/<slug>"`. `<quoted-repo>` is the absolute repo path, quoted, so
  the command is cwd-independent.
- **R3 — Ready section render.** The HTML renders a "Ready to start"
  section, visually distinct from the attention inbox (it is opportunity,
  not a problem), showing a count and one row per ready item
  (repo · spec · task · `cmd`). It appears even when the attention inbox
  is empty. When there are zero ready items the section header still
  renders with a "nothing ready" empty state (so the absence is legible,
  not a missing section).
- **R4 — Companion actions script.** `workboard.py` writes an executable
  shell script to a sibling path of `--out` (default: `--out` stem +
  `.actions.sh`; overridable via `--actions-out <path>` for hermetic
  tests), `chmod +x`. It begins with `#!/usr/bin/env bash` and `set -u`,
  and an echoed one-line banner telling the user to review before running.
  It contains up to two labeled sections, each a `# === <label> ===`
  comment block whose lines are independently runnable:
  - **Pushes** — one `git -C <abs-repo> push` line per repo the board
    found with unpushed-ahead commits (mirrors the needs-review push cmd).
  - **Verify done specs** — one `claude "Use the verifier agent to verify
    specs/<slug> against its acceptance criteria"` line (with a preceding
    `cd <abs-repo>`) per all-tasks-done unarchived **toolkit** spec with
    `tasks_total > 0`. Kiro specs (`.kiro/specs/<slug>`) are excluded —
    they have no verifier-agent flow — even though the inbox's
    done-spec detection (:527) fires for them too.
  The script MUST NOT contain any `git mv`/archive move, any `git push
  --force`/`-f`, any `rm`, or any `/build`//`/drain` worker launch. If
  both sections are empty the script is still written but contains only
  the header plus a `# no batch actions available` comment.
- **R5 — HTML links the script.** The HTML shows, near the top, the path
  to the actions script and the exact `bash <path>` invocation to run it.
  Render the invocation as a `<code>` inside a table cell (`<td><code>`)
  so the existing click-to-copy handler (which fires only on
  `closest('td code')`, workboard.py:902) applies to it. It states in one
  line that pushes run immediately and verify lines launch review
  sessions.
- **R6 — Grouped, ranked inbox.** The attention inbox is grouped under
  per-category headers in fixed severity order (`blocked` → `needs-review`
  → `stale`); within a group, items are ordered by existing `age_ts`
  newest-first. Item content/`cmd` is unchanged from today.
- **R7 — Clickable filter tiles.** The top-of-board summary renders one
  box per category present (`ready`, `blocked`, `needs-review`, `stale`)
  showing its count. Each box carries a `data-filter="<category>"`
  attribute and, via embedded JS (no external request), clicking it hides
  all items/sections not of that category; clicking the active box again
  (or an "all" affordance) restores the full view. This complements — does
  not replace — the existing text-filter input (:912–913), and both must
  still work.
- **R8 — No regression.** Existing behavior is preserved: attention-item
  detection and `cmd` strings, click-to-copy JS (:902–906), the
  `--abandon`/`--abandon-stale` mutation path (:440–458), and the default
  `--out` write (:967–972). Running with no ready items and no pushable
  repos produces a valid board and a header-only actions script.
- **R9 — Mirror + version bump.** The workboard skill is mirrored at
  `antigravity/.agents/skills/workboard/workboard.py`; per CLAUDE.md's
  authoring conventions the same behavior changes land there in the **same
  commit**, and `.claude-plugin/plugin.json` `version` is bumped once
  (skill behavior changed). If the antigravity mirror has diverged such
  that a change does not apply cleanly, port the equivalent change rather
  than copying verbatim, and note the divergence in the commit message.

- **R10 — Active-coverage reclassification.** The attention inbox no longer
  flags a repo's uncommitted **or** unpushed git state as `needs-review` when
  a live session or an active drain owns that repo. Instead those items are
  *reclassified* (not hidden) into a distinct **Active** group — state
  `in-progress`, category `active` — rendered after the attention groups and
  excluded from the needs-attention headline count. Two coverage signals: a
  **live human session** whose `git rev-parse --show-toplevel` equals the repo
  root (toplevel *equality*, replacing the old path-prefix match that
  over-covered parents of nested repos/worktrees), OR a **live drain** — any
  worktree on a `task/*` branch whose newest activity is within a configurable
  **drain window** (default 15m, `--drain-window-min`). A `task/*` worktree
  whose activity is older than the window is **stale** and still flags (the
  "drain died, work stranded" case); live vs. stale differ ONLY by recency,
  never by the worktree lock or branch state. A parked baton is not a coverage
  signal. Builds on R6's grouped inbox; cross-cuts R8 (no regression) and R9
  (mirror + bump).

## Out of scope

- Clipboard mechanics — visible copy buttons, resilient clipboard
  fallback, cwd-independent normalization of the *existing* inbox
  commands. Owned by `specs/workboard-copy-commands/`; this spec neither
  depends on nor modifies that work.
- Executing any mutation from the browser, or any server/daemon/watch
  mode. The board stays a static point-in-time snapshot; the only run-time
  action is the human running the companion script.
- Auto-archiving done specs (archival stays a human-reviewed step gated on
  a PASS verdict) and auto-launching `/build`//`/drain` workers from the
  batch script.
- Readiness detection for Kiro (`.kiro/specs`) and Antigravity work — R1
  covers toolkit specs only.
- AI/model-driven ranking or prioritization of the inbox; grouping and
  ordering are deterministic (R6).

## Acceptance criteria

- [ ] `bash tests/test_workboard_actionability.sh` passes (covers
      R1–R7). The test is hermetic: it exports `HOME` and
      `CLAUDE_CONFIG_DIR` to a fixture tree under
      `tests/fixtures/workboard-actionability/` AND passes the fixture
      repo path(s) as **explicit positional roots** to `workboard.py`
      (because `default_roots()` always appends `Path.cwd()`,
      workboard.py:127 — omitting roots would let the real repo leak into
      the scan). It runs `workboard.py <fixture-repos...> --out <tmp>/wb.html
      --actions-out <tmp>/a.sh` and asserts:
  - a fixture spec with a pending task whose only (same-spec, bare-numeric)
    dep is `done` appears in "Ready to start" with a `claude "/build `
    command (R1–R3);
  - a fixture spec with a pending task whose **cross-spec** `../`-relative
    dep is `done` DOES appear as ready — the cross-spec case that a
    same-spec-only rule would wrongly hide (R1);
  - a fixture spec with a pending task whose dep is still `pending` does
    NOT appear as ready, and a task with an unresolvable dep id is
    recorded blocked-by-unresolved, not ready (R1);
  - a fixture spec with ≥2 ready tasks yields one `claude "/drain
    specs/<slug>"` item, not per-task build items (R2);
  - the actions script contains a `git -C <repo> push` line for a fixture
    repo with unpushed commits, and a Kiro fixture done-spec produces NO
    verify line (R4/S5); the script contains NO `git mv`, NO `push
    --force`/`-f`, NO `rm`, NO `/build`//`/drain` (R4);
  - the HTML contains a `data-filter="needs-review"` tile and the filter
    handler JS, and still contains the existing text-filter input (R7);
  - the inbox renders category group headers in `blocked`,
    `needs-review`, `stale` order (R6).
- [ ] `bash -n <actions-script>` exits 0 — the emitted script is
      syntactically valid shell (R4).
- [ ] `python3 -c "import ast; ast.parse(open('.claude/skills/workboard/workboard.py').read())"`
      exits 0 (module still parses after edits) and a smoke run
      `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html
      --actions-out /tmp/wb.actions.sh` exits 0 on the real machine (R8).
- [ ] `git show --stat HEAD` (the implementing commit) touches BOTH
      `.claude/skills/workboard/workboard.py` and
      `antigravity/.agents/skills/workboard/workboard.py`, and
      `git diff HEAD~1 -- .claude-plugin/plugin.json` shows a `version`
      bump (R9).
- [ ] End-to-end: after the smoke run, `/tmp/wb.html` contains both a
      "Ready to start" section header and the actions-script path/`bash`
      invocation, and `test -x /tmp/wb.actions.sh` succeeds — proving the
      two new surfaces render together and the script is executable
      (R3, R4, R5).

## Parallelization

None — the four tasks are a strict serial chain (01 → 02 → 03 → 04). All
edit the same core file (`.claude/skills/workboard/workboard.py` + its
antigravity mirror) and grow the same single test file
(`tests/test_workboard_actionability.sh`), so their `Touch` lists fully
overlap and no group is disjoint. They also share undecided design surface
(the readiness data structures from R1 feed the tiles/counts in R7; the
HTML template layout is edited by all; task 04's Active group extends R6's
grouped inbox), which fails the decision-coupling test. Run them one at a
time, each as its own mirror-and-version-bump commit.

## Open questions

(none)

## Notes

- The workboard test-harness pattern (hermetic `HOME`/`CLAUDE_CONFIG_DIR`
  export + fixture tree) is the same one proposed by
  `specs/workboard-copy-commands/tasks/01` (which scopes to
  `tests/fixtures/workboard/`); to avoid a collision, this spec uses a
  **distinct** `tests/fixtures/workboard-actionability/` subdir and ships
  its own `tests/test_workboard_actionability.sh`, importing nothing from
  the copy-commands work. If both land, a later cleanup can merge the
  fixtures — not required here.
- `workboard` is not one of the five ultra-path gate skills
  (critique/drain/parallel/build/idea), so `evals/lint-ultra-gate.sh`
  does not apply to these edits.
