# Workboard: CLI-sourced session liveness, dependency graphs, source-health

## Problem

The `/workboard` scanner (`.claude/skills/workboard/workboard.py`) has three
gaps a sibling tool ("Agent Console") already solved and proved on this machine:

1. It determines which sessions are live by scraping `~/.claude/sessions/*.json`
   PID records and calling `os.kill` (`live_session_ids()` L533–548,
   `pid_alive()` L96–101). That's an undocumented Claude internal; Anthropic's
   docs say those formats change between versions. A supported CLI now exists:
   `claude agents --json`.
2. It parses each task's `Depends on:` line (`parse_deps()` L261–269,
   `DEPENDS_RE` L202) and even resolves refs (`resolve_dep`/`_glob_task`
   L272–283), but throws the graph away — it renders only counts
   (`tasks_total/done/doing/blocked`). The dependency structure is invisible.
3. When a source exists but parses to nothing (schema drift), the affected
   section renders empty and indistinguishable from "no work" — a silent lie
   after a Claude Code update.

This backports the three read-only improvements into `workboard.py`, keeping its
form factor: one-shot, stdlib-only, self-contained HTML snapshot.

## Solution

Adapt (do NOT copy verbatim) three pieces from the reference implementation
`~/agent-console/agent-console.py` — it's a separate repo, so the implementer
ports the *algorithm*, matching workboard's own data shapes. Preserve the
read-only-toward-reported-state + stdlib-only contract (`SKILL.md` L1–10,
`reference.md` L16).

**A. CLI-sourced session liveness (R1, R2).** Rewrite `live_session_ids()`
(L533–548) to build its `{sid: {...}}` liveness map from `claude agents --json`
(active records `[{pid, sessionId, status, ...}]`), falling back to the existing
PID-record + `pid_alive()` scan when `claude` is absent from PATH or returns a
non-list. **Keep the return shape a sid-keyed dict** — its only consumer,
`scan_sessions` (L556–566), uses it purely as a membership set (`if sid in
live`). Session *rows* keep rendering from the `.jsonl` transcript via
`_first_prompt_and_meta` (L477); CLI `cwd/name` are NOT used for row content.
Reference: agent-console `live_sessions_from_cli` / `_live_sessions_from_pids`
(port the parse + fallback logic; then reduce to the sid-keyed map). R2:
canonicalize both sides of the session→repo attribution at
`workboard.py:871–875` with `os.path.realpath` before the `==` / `startswith`
comparison (agent-console lesson: symlinked cwds otherwise mis-attribute).

**B. Dependency-graph SVG (R3).** workboard task dicts (L230–236) have no `num`
and store `deps` as *raw* strings; the reference matches deps by numeric
equality and would render **zero edges** if copied. So: (a) give each task a
`num` (the `NN` prefix of `NN-*.md`); (b) resolve `deps` to in-spec task `num`s
using the existing `resolve_dep`/`_glob_task` (L272–283), which also defines
in-spec vs cross-spec (cross-spec refs are excluded from the drawn graph); then
(c) feed `[{num, title, status, deps:[num...]}]` to a new pure
`dep_graph_svg(tasks)` that ports agent-console `_dep_graph_svg`'s layout
(left→right by longest-path depth, one node per task, one path per edge, node
stroke by status, cycle-guarded, returns "" when no in-spec edges). **Style the
SVG with inline `style=`/presentation attributes on its elements — add no CSS to
the TEMPLATE `<style>` block** (see R-note below). Wire it into the per-spec
render near `progress_bar()` (L950), inside a collapsible element so the
snapshot stays scannable.

**C. Source-health (R4).** Give the spec-task parser and the liveness source an
`unparseable` count: records that are present but yield no usable id/field
(e.g. a `tasks/` dir with files none of which parse; a liveness source that is
non-empty but yields no live ids). When a *work* source's count > 0, emit a
small "source check" marker on that section; for the liveness source, mark
"liveness unknown" (not "no sessions", since session rows come from transcripts,
not liveness). Reference: agent-console `parse_session_entries` returns
`(by_repo, unparseable)`.

**R-note (TEMPLATE):** `render_html` uses `TEMPLATE.format(...)` (L1271) and its
`<style>` block already doubles braces (`:root {{ }}`, L1293–1317). SVG passed as
a `.format` *argument* is safe; adding graph CSS to the TEMPLATE would require
doubling every brace. Avoid it by styling the SVG inline.

## Requirements

1. **R1** — `live_session_ids()` returns the same `{sid: {...}}` liveness map,
   built from `claude agents --json` (parsing `pid`, `sessionId`, `status`).
   With `claude` absent from PATH or returning a non-list, it falls back to the
   current PID-record + `pid_alive()` scan, output shape unchanged.
2. **R2** — the session→repo attribution at `workboard.py:871–875` applies
   `os.path.realpath` to both the session cwd and the repo root before matching.
   A **new** test must exercise this loop directly: a session whose `cwd` is a
   symlink into a repo attributes to that repo (the L301–373 reclassification
   suite runs a different path — `_actively_covered`/`toplevel` at L689–724 — so
   it does NOT cover `:871–875`; still re-run it to confirm no regression, but it
   is not the guard for R2).
3. **R3** — a spec whose tasks declare in-spec `Depends on:` edges renders an
   inline `<svg>` DAG: one node per task (num + short title), one path per edge,
   layered by dependency depth, node stroke colored by status
   (done/in-progress/open/blocked). Deps are resolved via `resolve_dep`; a spec
   with zero in-spec edges renders exactly as today (no SVG); cross-spec refs are
   not drawn; a cyclic `Depends on:` set returns without hanging.
4. **R4** — when a scanned source is present but yields zero parseable records,
   the section shows a visible "source check" marker: a spec whose `tasks/`
   dir has files but none parse marks that spec; a non-empty liveness source
   that yields no live ids marks liveness as "unknown". Session/spec rows that
   come from transcripts are unaffected.
5. **R5** — no *new* write to the state the scanner reports on. The existing
   writes stay (rendered HTML `out.write_text` L1569; the actions script
   `actions_path.write_text` L1565; the `--abandon` marker
   `.workboard-abandoned` L640). No pip deps; `claude`/`git` subprocess is
   allowed (queries; `git` already shells out via `run_git`).

## Out of scope

- The Agent Console **service** form factor: no persistent HTTP server, daemon,
  launchd/systemd unit, caching, or auto-refresh. Stays a one-shot snapshot.
- Any **mutation/control**: no priority editing, no agent start/stop/resume, no
  new writes to reported state (the existing HTML/actions/abandon writes stay).
- **Skills/plugin enumeration** (Agent Console's separate "Skills" view).
- Multi-OS packaging, config files, or generalization beyond current behavior.
- Changing session *row* content to come from the CLI (liveness only; rows stay
  transcript-sourced).

## Acceptance criteria

- [ ] `python3 -m unittest discover -s .claude/skills/workboard` passes,
      including the pre-existing reclassification suite (R2 didn't regress it)
      plus new tests for R1 (CLI parse + PID fallback), R3 (node/edge counts +
      a cyclic input returns), R4 (unparseable → marker).
- [ ] R1 fallback: a test monkeypatches the `claude agents --json` shim to (a)
      return a valid list → liveness from CLI, and (b) raise/return None →
      liveness from PID records; both yield the same `{sid:…}` shape.
- [ ] R2: a new test attributes a session whose `cwd` is a symlink into a repo
      to that repo (exercises `:871–875` directly; the L301–373 suite does not).
- [ ] R3: a spec fixture with `Depends on:` edges yields HTML containing `<svg`
      with the expected node and edge counts; a fixture with a dependency cycle
      returns (no hang); a spec with no deps yields no `<svg`.
- [ ] R4: a spec fixture whose `tasks/` files all fail to parse yields the
      "source check" marker for that spec, not an empty task section.
- [ ] R5: `grep -nE '\.write_text|\.write\(|\bopen\([^)]*[\x27"][wax]' .claude/skills/workboard/workboard.py`
      shows only the three known write sites (HTML L1569, actions L1565, abandon
      L640) — no new write to reported state — reviewed by hand.
- [ ] End-to-end: `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html`
      on this machine produces a self-contained HTML that (a) contains ≥1
      dependency-graph `<svg>` and (b) marks sessions active using CLI liveness
      (verify by diffing active sids against `claude agents --json`).

## Open questions

(none)

## Parallelization

Three tracks touch different functions but two have flagged blast radius:
- **A (sessions, R1+R2)** — rewrites `live_session_ids` and edits the L871–875
  attribution; **must re-run the L301–373 reclassification tests** (not fully
  independent — it shares the session code path).
- **B (dep graph, R3)** — new `dep_graph_svg` + `num`/resolve wiring in the
  spec scan; independent of A.
- **C (source-health, R4)** — `unparseable` counts in the spec/liveness parsers;
  touches A's liveness parser, so sequence C after A.
Reference for all three: `~/agent-console/agent-console.py`
(`live_sessions_from_cli`, `_dep_graph_svg`, `parse_session_entries`).
