# Shared Visualization Renderer (`viz.py`)

## Problem
Three dashboards on this machine each hand-roll their own visualization, and none reuses another's:
- **`/fleet`** skill (LLM-rendered; `SKILL.md:34` "Fill the HTML template in reference.md") owns a Gantt **timeline** — geometry `~/claude/.claude/skills/fleet/reference.md:31-37`, CSS `:106-121`, template `:154-163`. Uses a CVD-validated `:root` palette + CSS vars (`reference.md:41-45,57-71`).
- **`/workboard`** skill (Python `~/claude/.claude/skills/workboard/workboard.py`, has `test_workboard.py`) has **no graph at all** — progress bars + tables only.
- **`agent-console`** (separate repo `~/agent-console/agent-console.py`, live server) has a dependency **DAG** (`_dep_graph_svg` at `agent-console.py:891-958`, wired `:1057-1068`; colors via `_task_stroke` returning hex `:880-888`) but renders Sessions as **flat text** (`:1082-1097`). It never draws the timeline `/fleet` already implemented, and hardcodes a dark palette (`#161922/#2f3644/#d98a63`).

Result: the timeline exists but two dashboards don't use it; the DAG exists but only one dashboard has it; each status→color mapping is redefined independently against *different* status vocabularies. Fixing or restyling a graph means editing up to three places, and they drift.

## Solution
Create one self-contained, **pure-Python-stdlib** module `viz.py` (source of truth in the toolkit) and distribute it three ways, because the consumers cannot all `import` one module (`/fleet` is an LLM-filled markdown template; `agent-console` is a separate repo whose `CLAUDE.md` forbids deps, network, and cross-repo imports):

- **Source of truth:** `~/claude/.claude/skills/_shared/viz.py` (new — no shared-module precedent; `workboard.py` is stdlib-only). First line after the docstring: `# viz-sha256: <hex>` = sha256 of the module body *below that line*.
- **`/workboard` skill** — *imports* it: `sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))` then `import viz`.
- **`agent-console`** — *vendors* a byte-identical copy at `~/agent-console/viz.py` (stays pure-stdlib). Deletes `_dep_graph_svg`/`_task_stroke`, calls `viz.dag()`/`viz.timeline()`.
- **`/fleet` skill** — its timeline CSS region in `reference.md` is regenerated from `viz.py --emit-fleet-css` and bracketed by sentinel markers, so it stays LLM-filled but structurally identical.

### Color model (resolves class-vs-hex ambiguity)
`viz.py` defines ONE canonical status set and both a class name and a hex per canonical status, so HTML colors via CSS class + host `:root` var, and SVG colors via an inline hex — both keyed on the same token:
- **Canonical statuses** (6): `running`, `open`, `done`, `failed`, `stale`, `blocked`.
- `canonical_status(raw: str) -> str` maps every real term (case-insensitive) to one canonical token via this table (terms taken from the actual code — `agent-console.py:196-205,424-430`, `workboard.py:567-573`, `fleet/reference.md`):
  - `running` ← `running, in-progress, in_progress, claimed, active`
  - `open` ← `open, pending, todo, ready, queued`
  - `done` ← `done, completed, closed, deferred, skipped`
  - `failed` ← `failed, error`
  - `stale` ← `recent, stale, idle`
  - `blocked` ← `blocked`
  - anything else → `open` (never raises)
- `STATUS_HEX: dict[str,str]` — canonical token → SVG hex (seeded from the current DAG palette: running `#d98a63`, open `#6ea3c0`, done `#3a4150`; new: failed `#c96262`, stale `#5a6070`, blocked `#d9b063`).
- HTML uses CSS classes `viz-<canonical>`; each colored via `var(--viz-<canonical>, <STATUS_HEX fallback>)` — i.e. `VIZ_CSS` carries the canonical hex **as an inline fallback**, so bars/nodes are ALWAYS colored with zero host wiring, and a host that wants its own theme *may* (but need not) define `--viz-*` in its `:root` to override. No host is *required* to define the vars; no separate `:root` block ships in `VIZ_CSS`. This collapses the earlier "each host must supply vars" gap — the fallback is the single canonical palette, `STATUS_HEX` is its source, and HTML + SVG therefore agree by construction.

### Shared API (`viz.py`, pure stdlib)
- `timeline(rows: list[dict]) -> str` — HTML Gantt. Row: `{label:str, status:str, start_ts:float, end_ts:float, tooltip:str, href:str|None}`. Bars positioned `left`/`width` normalized to `[min(start_ts), now]`, floored at 0.75%, rows ordered by `start_ts` (per `fleet/reference.md:31-37`). Empty input → a fixed empty-state `<div>` string (no crash). Bar class = `viz-{canonical_status(status)}`.
- `dag(tasks: list[dict]) -> str` — SVG dependency DAG. Task: `{num:int, deps:list[int], status:str, title:str}`. Geometry/layout lifted **verbatim** from `agent-console.py:891-958` (cycle-guarded longest-path layering, Bézier edges). Only one color change vs. the original: the node **stroke** (and num-text) = `STATUS_HEX[canonical_status(status)]` (replacing `_task_stroke`). The node **fill**, **edge** stroke, and **title text** stay their current constants, now named module constants `_DAG_NODE_FILL="#161922"`, `_DAG_EDGE="#2f3644"`, `_DAG_TEXT="#c7ccd6"`. The DAG SVG carries its own dark mini-canvas background (as agent-console's `.viz-graphwrap` does today), so it renders correctly embedded in *either* a light (workboard) or dark (agent-console) host. Returns `""` when there are zero in-list edges.
- `VIZ_CSS: str` — structural stylesheet for both (`.viz-lane/.viz-track/.viz-bar/.viz-axis`, `.viz-graphwrap/.viz-node/.viz-edge`; `.viz-track` is the absolute-positioning wrapper each bar sits in); each color rule is `var(--viz-<token>, <hex>)` with the `STATUS_HEX` hex as the literal fallback. No `:root` block inside.
- `canonical_status(raw)`, `STATUS_HEX` — as above.
- CLI: `viz.py --emit-fleet-css` prints exactly `VIZ_CSS` (no `:root` block) wrapped in the sentinel markers `/* >>> viz:timeline-css BEGIN */` … `/* <<< viz:timeline-css END */`. `viz.py --self-sha256` prints the computed body hash (for the conformance check).

### Session start timestamp (enables the Sessions timeline)
`timeline()` needs a start and end per row; collected session records today carry only *last-activity* (`agent-console.py:432-440`, `workboard.py:574-582`) — no start. This spec therefore makes a **narrow, explicit** collection addition: add `start_ts` to each session record, resolved in order — (1) the timestamp of the **earliest** record in the session transcript (`.jsonl` first line); (2) the transcript file's `st_birthtime` if it's present but unreadable; (3) for **PID-injected live sessions that have no transcript file at all** (`agent-console.py:468-480`), `start_ts = end_ts` (the session's `last`), yielding a minimum-width bar rather than a crash. `end_ts` = existing last-activity. This is the *only* sanctioned data-collection change.

## Requirements
1. **R1** — `viz.py` exists at `~/claude/.claude/skills/_shared/viz.py`, imports only stdlib, exposes `timeline`, `dag`, `VIZ_CSS`, `canonical_status`, `STATUS_HEX`, and the `--emit-fleet-css`/`--self-sha256` CLI. First post-docstring line is `# viz-sha256: <hex of body below>`.
2. **R2** — `dag(tasks)` reproduces the current agent-console DAG for the same input: one `<g>` node per task, one `<path>` per in-list edge, node **stroke** + num-text = `STATUS_HEX[canonical_status(task.status)]` (fill/edge/title stay the named constants per the API); returns `""` when zero in-list edges; a cyclic `deps` set does not infinite-loop (cycle guard preserved).
3. **R3** — `timeline(rows)` returns HTML with one `.viz-lane`/`.viz-bar` per row; each bar `left`/`width` normalized to `[min(start_ts), now]`, floored at 0.75%; rows ordered by `start_ts`; bar class `viz-{canonical}`. Empty `rows` → the fixed empty-state string. A row missing `start_ts` raises `ValueError` (caller contract, not silent).
4. **R4** — `canonical_status(raw)` maps EVERY term in the table above (case-insensitive) to its listed canonical token, and any unlisted term to `open`, without raising. `STATUS_HEX` has a hex for all 6 canonical tokens.
5. **R5** — `/workboard` skill imports `viz` and (a) renders a **Sessions timeline** via `viz.timeline()` in place of its session list, using the new `start_ts`/`end_ts`; (b) renders spec DAGs via `viz.dag()`. `test_workboard.py` still passes and adds assertions for both (a `.viz-bar` appears for a session; a `<path>` appears for a spec with deps).
6. **R6** — session collection in BOTH `workboard.py` (`scan_sessions`) and `agent-console.py` (`collect_sessions`/`live_sessions`) adds `start_ts` (earliest transcript record ts; `st_birthtime` fallback) alongside the existing last-activity as `end_ts`.
7. **R7** — `agent-console` vendors `viz.py` byte-identically, deletes `_dep_graph_svg` + `_task_stroke`, calls `viz.dag()` (wiring at former `:1057-1068`) and `viz.timeline()` (replacing flat-text Sessions `:1082-1097`); stays pure-stdlib/no-network.
8. **R8** — `~/agent-console/scripts/check.sh` gains a conformance step: **(primary, load-bearing)** when `~/claude/.claude/skills/_shared/viz.py` exists, `diff` it against the vendored copy and hard-fail on any difference; **(secondary)** always recompute the vendored body sha256 and hard-fail if it ≠ the `# viz-sha256:` header (corruption guard); when the toolkit source is absent, print `conformance: SKIPPED (toolkit source not present — corruption-check only)` and pass. *Known limitation, stated in the check output: offline-without-toolkit catches corruption, not deliberate divergence.*
9. **R9** — the fleet skill is migrated to the shared structural rules: (a) `viz.py --emit-fleet-css` output appears verbatim between the sentinel markers in `fleet/reference.md`; (b) fleet's TIMELINE ROWS **markup** and its fill-rule prose (`reference.md:24-38,107-118,156-162`) are renamed from `.lane`/`.track`/`.bar`/`.axis` to their `.viz-*` equivalents so the shared CSS actually styles them; (c) fleet **preserves its CVD-validated colors** by defining its four validated `--viz-*` overrides (`running`, `done`←completed, `failed`, `open`←queued) in its `:root`; `stale`/`blocked` (no CVD value in fleet) fall back to the shared hex. Verifiable by diffing the emitted CSS block and grepping that no bare `.bar`/`.lane`/`.axis`/`.track` timeline class remains in `reference.md`.

## Out of scope
- **Merging the two workboard tools.** `/workboard` (snapshot) and `agent-console` (live server) overlap in purpose; this unifies only their **renderer**. Whether both should exist is a separate future question — do not merge/delete either.
- **No collection changes beyond the single `start_ts` addition** (R6). Scanners, git state, spec/task parsing, session state classification stay as-is.
- No new graph *types* (no force-directed layout, no cross-spec/cross-repo edges, no charts beyond timeline + DAG).
- No PyPI/installable packaging; distribution is import (toolkit) + vendor (agent-console) only.
- No change to each host's *displayed* palette: agent-console and workboard adopt the shared canonical fallback colors; **fleet keeps its exact CVD-validated colors** by overriding `--viz-*` in its `:root` (R9c). Only the structural CSS + class names are shared, not a forced palette.

## Acceptance criteria
- [ ] **R1 (stdlib-only, real audit):** `python3 -m py_compile ~/claude/.claude/skills/_shared/viz.py` succeeds, and this audit exits 0:
  ```sh
  python3 - <<'PY'
  import ast, sys
  src = open("/Users/sjaconette/claude/.claude/skills/_shared/viz.py").read()
  roots = set()
  for n in ast.walk(ast.parse(src)):
      if isinstance(n, ast.Import): roots |= {a.name.split('.')[0] for a in n.names}
      elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module: roots.add(n.module.split('.')[0])
  bad = sorted(r for r in roots if r not in sys.stdlib_module_names)
  assert not bad, f"non-stdlib imports: {bad}"; print("stdlib-only: ok")
  PY
  ```
- [ ] **R2–R4:** `pytest ~/claude/.claude/skills/_shared/test_viz.py` passes — golden `dag()` (incl. empty + a cyclic-deps case), `timeline()` (incl. empty + 0.75% floor + missing-`start_ts` raises), full `canonical_status` table + unknown→`open`, `STATUS_HEX` covers all 6.
- [ ] **R5, R6:** `pytest ~/claude/.claude/skills/workboard/test_workboard.py` passes with the new session-`start_ts`, `.viz-bar`, and DAG assertions — including one asserting a rendered `.viz-bar` carries a color (the `var(--viz-*, #hex)` fallback is present in the emitted HTML, so bars are colored with no host vars defined).
- [ ] **R7, R8:** `bash ~/agent-console/scripts/check.sh` passes including conformance; then a temporary 1-byte edit to `~/agent-console/viz.py` makes it **fail** the toolkit-diff (proves the primary guard bites, with `~/claude` present).
- [ ] **R9:** `diff <(python3 ~/claude/.claude/skills/_shared/viz.py --emit-fleet-css) <(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' ~/claude/.claude/skills/fleet/reference.md)` is empty; AND `! grep -nE 'class="(bar|lane|axis|track)[ "]' ~/claude/.claude/skills/fleet/reference.md` (fleet's timeline markup was migrated to `.viz-*`, none of the old classes remain).
- [ ] **End-to-end:** start `agent-console`, open `/workboard`; the Sessions section renders a **timeline of `.viz-bar`s** (session start→last-activity), not flat text, styled by the shared `.viz-*` rules; expanding a spec still shows its DAG — both from `viz.dag`/`viz.timeline`.

## Open questions
(none — ready for breakdown)

## Parallelization
- **Wave 1 (blocker):** `01-extract-viz-module` — the shared `viz.py` + tests. Everything imports or vendors it; nothing else may start until it is green.
- **Wave 2 (parallel — disjoint Touch, no shared undecided design):** once 01 lands, run concurrently:
  - `02-wire-workboard-skill` — Touch: `.claude/skills/workboard/*`
  - `03-vendor-into-agent-console` — Touch: `~/agent-console/*` (separate repo + gate)
  - `04-migrate-fleet-reference` — Touch: `.claude/skills/fleet/reference.md`
  Decision-coupling check passes: all three consume the fully-specified `viz.py` API (`canonical_status`, `STATUS_HEX`, `timeline`, `dag`, `VIZ_CSS`, CLI) from the spec — no naming/interface/schema choice is left for a task to invent. Each repo's session `start_ts` change (R6) is folded into its own consumer task (02 for workboard, 03 for agent-console), so there is no cross-repo task.

Dispatch: `/build specs/shared-viz-renderer/tasks/01-*.md` first; after it merges, `/parallel specs/shared-viz-renderer` runs wave 2.
