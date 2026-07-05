# Workboard: CLI-sourced session liveness, dependency graphs, source-health

Assumes: shared-viz-renderer tasks 01+02 are merged to main (satisfied —
`.claude/skills/_shared/viz.py` exists and `workboard.py` already imports it
and renders via `viz.timeline()`/`viz.dag()`/`viz.VIZ_CSS`). This spec is
written against that merged code.

## Problem

The `/workboard` scanner (`.claude/skills/workboard/workboard.py`) has three
gaps a sibling tool ("Agent Console") already solved and proved on this machine:

1. It determines which sessions are live by scraping `~/.claude/sessions/*.json`
   PID records and calling `os.kill` (`live_session_ids()`, `pid_alive()`).
   That's an undocumented Claude internal; Anthropic's docs say those formats
   change between versions. A supported CLI now exists: `claude agents --json`.
2. It parses each task's `Depends on:` line (`parse_deps()`, `DEPENDS_RE`) and
   even resolves refs (`resolve_dep`/`_glob_task`), and — since shared-viz
   merged — renders a per-spec DAG via `viz.dag()` (`_spec_dag_tasks` /
   `_spec_dag_html`). But `_spec_dag_tasks` keeps only deps passing a bare
   `isdigit()` check, so path-form, glob-form, and `specs/...`-rooted same-spec
   refs draw **zero edges** — `resolve_dep`'s output never reaches the graph.
3. When a source exists but parses to nothing (schema drift), the affected
   section renders empty and indistinguishable from "no work" — a silent lie
   after a Claude Code update.

This backports the three read-only improvements into `workboard.py`, keeping its
form factor: one-shot, stdlib-only, self-contained HTML snapshot.

## Solution

For A and C, adapt (do NOT copy verbatim) the algorithm from the reference
implementation `~/agent-console/agent-console.py` — it's a separate repo, so
the implementer ports the *algorithm*, matching workboard's own data shapes.
B needs no port: the renderer is the already-imported shared `viz.dag()`
(agent-console's old `_dep_graph_svg` was deleted upstream when shared-viz
centralized it). Preserve the read-only-toward-reported-state + stdlib-only
contract (`reference.md` "Data sources (all read-only)"; SKILL.md's
stdlib-only fallback note).

**A. CLI-sourced session liveness (R1, R2).** Rewrite `live_session_ids()`
(today the `~/.claude/sessions/*.json` PID-record scan) to build its
`{sid: {...}}` liveness map from `claude agents --json` (active records
`[{pid, sessionId, status, ...}]`), falling back to the existing PID-record +
`pid_alive()` scan when `claude` is absent from PATH or returns a non-list.
**The liveness map stays a sid-keyed dict**, but the function now returns a
2-tuple `(live, liveness_unknown)` — `live` is the unchanged `{sid: {...}}`
map; `liveness_unknown` is the R4 bool (source present and non-empty but
yielded zero live ids). Its only consumer, `scan_sessions`, unpacks the
tuple and uses `live` purely as a membership test (`if sid in live` →
state "active"), plumbing `liveness_unknown` through for R4. Session *rows* keep rendering from the `.jsonl` transcript
via `_first_prompt_and_meta`; CLI `cwd/name` are NOT used for row content.
Reference: agent-console `live_sessions_from_cli` / `_live_sessions_from_pids`
(port the parse + fallback logic; then reduce to the sid-keyed map). R2:
canonicalize both sides of the session→repo attribution — the "attach
sessions to repos" list-comprehension in `assemble()` (`s["cwd"] ==
r["path"] or s["cwd"].startswith(r["path"] + os.sep)`) — with
`os.path.realpath` before the comparison (agent-console lesson: symlinked
cwds otherwise mis-attribute).

**B. Dependency-graph edges via resolve_dep (R3).** The render pipeline
already exists and stays: `_spec_dag_tasks(spec)` maps `spec["tasks"]` to
`viz.dag()`'s `{num, deps, status, title}` schema (num from the task file's
leading `NN-` prefix) and `_spec_dag_html` wraps each non-empty `viz.dag()`
SVG in a collapsible `<details class="spec-dag">` inside the per-spec card —
do NOT write a new SVG layout function. The remaining work is data plumbing:
replace `_spec_dag_tasks`'s `isdigit()` dep filter with resolution through
the existing `resolve_dep`/`_glob_task` (task dicts carry `abs`; derive
`task_dir = Path(abs).parent` and `repo_root = Path(abs).parents[3]` — abs is
`<repo>/specs/<slug>/tasks/NN-*.md`, so parents[3] is the repo root needed
for `specs/…`-rooted refs), map each resolved in-spec file to its task
`num`, and exclude cross-spec resolutions from the drawn graph. `viz.dag()`
is itself cycle-guarded and returns "" when there are no in-list edges —
don't re-implement either guard, but keep a workboard-level test that a
cyclic `Depends on:` set still returns.

**C. Source-health (R4).** Give the spec-task parser and the liveness source an
`unparseable` count. Pinned definition for the spec-task side: a task file is
**unparseable iff its filename lacks the leading `NN-` numeric prefix that
`_TASK_NUM_RE` needs** (today `scan_toolkit_specs` appends a row for every
`tasks/*.md` unconditionally — missing Status defaults to `pending`, missing
title to the stem — so the parser must be tightened to count, not silently
default, exactly this case; no other rejection criterion is in scope). For
the liveness side: the source is unparseable when it is present and
non-empty but yields no live ids — the `liveness_unknown` bool R1's 2-tuple
carries. When a *work* source's count > 0, emit a
small "source check" marker on that section; for the liveness source, mark
"liveness unknown" (not "no sessions", since session rows come from
transcripts, not liveness). Sessions now render as a `viz.timeline()` Gantt
(`_session_timeline_html`: one `.viz-lane`/`.viz-bar` per session) in each
repo card's Sessions column and in the "Sessions outside scanned repos"
section — place the marker adjacent to that timeline (e.g. beside the
section heading), never inside the `.viz-bar` rows, which are
transcript-sourced and unaffected. `scan_sessions` already computes
`start_ts`/`end_ts` (merged shared-viz work), so R4's liveness edits land in
`live_session_ids()`'s post-R1 form and plumb the flag out through
`scan_sessions`/`assemble` to the renderer. Reference: agent-console
`parse_session_entries` returns `(by_repo, unparseable)`.

**R-note (TEMPLATE):** `render_html` returns `TEMPLATE.format(...)`. The
TEMPLATE literal's own `<style>` rules double every brace (`:root {{ }}`);
`viz.VIZ_CSS` is NOT part of the literal — it is injected through the
`{viz_css}` placeholder inside `<style>` as a `.format` argument, so it stays
un-doubled. Anything passed as a `.format` *argument* (SVG, marker HTML) is
brace-safe; only CSS written literally into TEMPLATE needs doubled braces.
For R4's marker, prefer existing classes (e.g. `chip warning`, `muted-text`)
or inline `style=` over adding TEMPLATE CSS.

## Requirements

1. **R1** — `live_session_ids()` returns a 2-tuple `(live, liveness_unknown)`:
   `live` is the same `{sid: {...}}` liveness map as today, built from
   `claude agents --json` (parsing `pid`, `sessionId`, `status`);
   `liveness_unknown` is the R4 bool. With `claude` absent from PATH or
   returning a non-list, `live` falls back to the current PID-record +
   `pid_alive()` scan — the map's shape is unchanged in both paths.
2. **R2** — the session→repo attribution (the "attach sessions to repos"
   list-comprehension in `assemble()`) applies `os.path.realpath` to both the
   session cwd and the repo root before matching. A **new** test must exercise
   this loop directly: a session whose `cwd` is a symlink into a repo
   attributes to that repo (the `TestActiveCoverageReclassification` suite
   runs a different path — `_actively_covered()` and the `toplevel` equality
   set up in `assemble()` for `attention_items()` — so it does NOT cover the
   attach loop; still re-run it to confirm no regression, but it is not the
   guard for R2).
3. **R3** — a spec whose tasks declare in-spec `Depends on:` edges renders
   those edges in the existing `viz.dag()` SVG for **any** dep form
   `resolve_dep` supports (bare `01`, task-dir-relative path, `specs/...`-
   rooted path, glob), not just the bare-numeric form the current `isdigit()`
   filter passes. Deps are resolved via `resolve_dep`; cross-spec resolutions
   are not drawn; a spec with zero in-spec edges renders exactly as today (no
   `spec-dag` block — `viz.dag()` returns ""); a cyclic `Depends on:` set
   returns without hanging.
4. **R4** — when a scanned source is present but yields zero parseable records,
   the section shows a visible "source check" marker: a spec whose `tasks/`
   dir has files but none parse (per the pinned definition in C: no leading
   `NN-` prefix) marks that spec; a non-empty liveness source that yields no
   live ids (R1's `liveness_unknown`) marks liveness as "unknown". The transcript-sourced
   `viz.timeline()` session rows and spec rows are unaffected.
5. **R5** — no *new* write to the state the scanner reports on. The existing
   writes stay (the rendered-HTML `out.write_text` and the actions-script
   `actions_path.write_text`, both in `main()`; the `--abandon` marker
   `.workboard-abandoned` write in `abandon_conversations()`). No pip deps;
   `claude`/`git` subprocess is allowed (queries; `git` already shells out via
   `run_git`).

## Out of scope

- The Agent Console **service** form factor: no persistent HTTP server, daemon,
  launchd/systemd unit, caching, or auto-refresh. Stays a one-shot snapshot.
- Any **mutation/control**: no priority editing, no agent start/stop/resume, no
  new writes to reported state (the existing HTML/actions/abandon writes stay).
- **Skills/plugin enumeration** (Agent Console's separate "Skills" view).
- Multi-OS packaging, config files, or generalization beyond current behavior.
- Changing session *row* content to come from the CLI (liveness only; rows stay
  transcript-sourced).
- Reworking the merged shared-viz renderers themselves (`viz.timeline()`,
  `viz.dag()`, `VIZ_CSS`) — this spec only feeds and annotates them.

## Acceptance criteria

- [ ] `python3 -m unittest discover -s .claude/skills/workboard` passes,
      including the pre-existing `TestActiveCoverageReclassification` suite
      (R2 didn't regress it) and the merged shared-viz suites
      (`TestSessionStartTs`, `TestSessionTimelineRendering`,
      `TestSpecDagRendering`), plus new tests for R1 (CLI parse + PID
      fallback), R3 (resolve_dep-form edges + a cyclic input returns), R4
      (unparseable → marker).
- [ ] R1 fallback: a test monkeypatches the `claude agents --json` shim to (a)
      return a valid list → liveness from CLI, and (b) raise/return None →
      liveness from PID records; both return the 2-tuple whose first element
      is the same `{sid:…}` map shape.
- [ ] R2: a new test attributes a session whose `cwd` is a symlink into a repo
      to that repo (exercises `assemble()`'s attach-sessions loop directly;
      `TestActiveCoverageReclassification` does not).
- [ ] R3: a spec fixture whose `Depends on:` entries use a non-bare-numeric
      same-spec form (e.g. a task-dir-relative path) yields HTML containing
      `<svg` with the expected edge drawn (the current `isdigit()` filter
      draws zero edges for that fixture); a fixture with a dependency cycle
      returns (no hang); a spec with no deps yields no `spec-dag` block; the
      existing `TestSpecDagRendering` tests keep passing.
- [ ] R4: a spec fixture whose `tasks/` files all fail to parse (none has a
      leading `NN-` prefix) yields the "source check" marker for that spec,
      not an empty task section.
- [ ] R5: `grep -nE '\.write_text|\.write\(|\bopen\([^)]*[\x27"][wax]' .claude/skills/workboard/workboard.py`
      shows only the three known write sites (the HTML and actions-script
      writes in `main()`, the abandon marker in `abandon_conversations()`) —
      no new write to reported state — reviewed by hand.
- [ ] End-to-end: `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html`
      on this machine produces a self-contained HTML that (a) contains ≥1
      dependency-graph `<svg>` and (b) marks sessions active using CLI liveness
      (verify by diffing active sids against `claude agents --json`).

## Open questions

(none)

## Parallelization

Three tracks touch different functions but two have flagged blast radius:
- **A (sessions, R1+R2)** — rewrites `live_session_ids` and edits `assemble()`'s
  attach-sessions attribution; **must re-run
  `TestActiveCoverageReclassification`** (not fully independent — it shares
  the session code path).
- **B (dep graph, R3)** — `resolve_dep` wiring in `_spec_dag_tasks`;
  independent of A.
- **C (source-health, R4)** — `unparseable` counts in the spec/liveness parsers;
  touches A's liveness parser, so sequence C after A.
Reference for A and C: `~/agent-console/agent-console.py`
(`live_sessions_from_cli`, `parse_session_entries`). B's renderer is the
shared `viz.dag()` already imported by workboard.py — agent-console's
`_dep_graph_svg` no longer exists upstream.
