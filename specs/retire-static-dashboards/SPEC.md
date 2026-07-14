# Drop static HTML output: /fleet prints a table instead of a file, workboard's HTML fallback goes

Breakdown-ready: true

## Problem

Two skills produce static HTML snapshots, confirmed not useful in
practice. `/fleet` (`.claude/skills/fleet/SKILL.md`) has no other mode —
its entire job is rendering `fleet.html` to the scratchpad and presenting
it. `/workboard` already runs a live, always-current dashboard
(agent-console, re-scanning every request) but still carries a documented
fallback (`workboard/SKILL.md` lines 24-26: "**Fallback (machines without
agent-console):** ... `--out <scratchpad>/workboard.html`") that also
produces a static file.

An earlier version of this spec proposed retiring `/fleet` entirely and
folding its capability into `/workboard`'s live dashboard as a session
filter. That's unbuildable as described: `/fleet`'s data — background
`TaskList` entries and `git worktree list` output for _this specific
session_ — comes from in-process harness state only the invoking session
can see (`fleet/SKILL.md` step 1). `agent-console` is a separate,
shared server process reached via a bare URL with no session id passed;
`workboard.py`'s own `scan_sessions` only enumerates whole top-level
Claude Code sessions (one `.jsonl` transcript each) via `cwd`/timestamps —
it has no visibility into any session's live sub-agents. There is no way
for the live dashboard to reconstruct fleet's view. Retiring fleet in
favor of it would be a real capability loss, not a consolidation.

## Solution

Keep `/fleet` — its _data-gathering_ mechanism (steps 1-2 of its current
SKILL.md: harness `TaskList` + `git worktree list`, normalized into one
record per agent) is correct and stays exactly as-is. Only its _output_
changes: instead of rendering an HTML template to a scratchpad file and
presenting that file, it prints a markdown table directly in the
response (the same output shape `/list-specs` already establishes) — no
file, static or otherwise, is produced. Separately and independently,
remove `/workboard`'s static-HTML fallback entirely, per the original
Solution below.

- **`/fleet` renders inline, not to a file.** Replace steps 3 ("Render") and
  4 ("Present") of `fleet/SKILL.md` with: print one markdown table (columns
  `Label | Kind | Status | Elapsed | Snippet`) plus the existing one-line
  summary ("3 running · 1 queued · 2 completed · 0 failed — snapshot
  HH:MM:SS; re-run /fleet to refresh"). Delete `fleet/reference.md` (the
  HTML template) — it has no remaining consumer once step 3 no longer
  renders HTML.
- **Remove workboard's static-HTML fallback entirely.** Delete the
  `--out`/HTML-rendering code path from `workboard.py` (`render_html` and
  the `main()` branch that calls it) and the "Fallback (machines without
  agent-console)" bullet from `workboard/SKILL.md`. When the live server
  genuinely cannot start, `/workboard` reports the startup error and what
  to check — it no longer degrades to a file.
- **`viz.py`'s fleet-CSS generation goes too.** Per
  `specs/shared-viz-renderer/SPEC.md` (R9), `fleet/reference.md`'s CSS was
  regenerated verbatim from `.claude/skills/_shared/viz.py`'s
  `--emit-fleet-css` flag / `_emit_fleet_css()` function between sentinel
  markers. Since `reference.md` is deleted, that flag/function and its
  docstring/comment mentions in `viz.py` are deleted too — nothing else
  consumes it (verify with a repo-wide grep before removing, per R1).

## Requirements

- **R1**: Every reference to `/fleet` in this repo is inventoried via
  `git grep -n '\bfleet\b' -- .claude/ antigravity/ docs/ AGENTS.md
CLAUDE.md .claude-plugin/` (not a narrower guess — `git grep` excludes
  `.claude/worktrees/`'s transient full-repo copies, unlike a recursive
  `grep -rn`) and updated to describe fleet's
  new inline-table output instead of an HTML snapshot — including but not
  limited to: `.claude-plugin/plugin.json:3` ("a `/fleet` dashboard of
  open agents"), `.claude-plugin/marketplace.json` ("the /fleet
  open-agents dashboard"), `AGENTS.md` ("workboard/fleet views"),
  `docs/agent-dashboards.md` ("the session-scoped `/fleet`"),
  `docs/external-playbooks.md` ("`/fleet` covers the live view"),
  `drain/SKILL.md`'s "/fleet shows the workers live" mention,
  `workboard/SKILL.md`'s "For agents in THIS session only, use /fleet
  instead" line, and `.claude/skills/_shared/viz.py`'s docstring lines
  claiming "`/workboard`, agent-console, and `/fleet` render the same
  way" (false once fleet prints a plain table — reword) and its comment
  pointing at the now-deleted `fleet/reference.md`. Legitimate unrelated
  prose uses of the word "fleet" (e.g. `token-discipline.md`'s "scale the
  fleet", `human-gates.md`'s "a fleet of launched [workers]") are left
  alone — they don't refer to the skill. Separately, **every dangling
  citation of the deleted `fleet/reference.md` path anywhere in the
  repo** — not enumerated by file/line, since these are code comments and
  docstrings scattered across both the `.claude` and `antigravity` trees'
  `workboard.py`, `test_workboard.py`, `reference.md`, and `SKILL.md`
  (workboard reuses fleet's glyph+word status-chip visual convention in
  its own independently-rendered spawn-tree/status-chip code, and cites
  the file that documented it) — is reworded to stop citing a deleted
  file: either drop the file citation and describe the chip convention
  inline, or point at `fleet/SKILL.md` if it still documents the
  convention there. The convention itself (glyph + word status chips) is
  UNCHANGED by this spec — only fleet's own HTML-rendering mode and its
  now-orphaned `reference.md` are removed — so this is a citation fix,
  not a rewrite of workboard's chip-rendering logic.
- **R2**: `fleet/SKILL.md` no longer contains an HTML-rendering step;
  `fleet/reference.md` no longer exists. Its frontmatter `description`
  (currently: "...as a self-contained HTML snapshot with status tiles, a
  timeline, and per-agent detail") is rewritten to describe the new
  inline markdown-table output instead — this is the skill's actual
  auto-invocation trigger surface, not incidental prose, so it must match
  the new behavior, not just the body text.
- **R3**: `.claude/skills/_shared/viz.py`'s `_emit_fleet_css` function and
  `--emit-fleet-css` CLI flag are removed, along with any docstring/
  comment referencing fleet's CSS generation — confirmed via grep that
  nothing else in the repo invokes `--emit-fleet-css`.
- **R4**: `workboard.py`'s entire non-`--json` output path is deleted: the
  `render_html` function, the `build_actions_script` function, the
  `--out`/`--actions-out` CLI flags, and the `main()` branch that writes
  both the HTML file and its `.actions.sh` companion — `build_actions_script`
  and `render_html` have no consumer other than that branch (agent-console
  imports only `assemble`/`attention_items`/`ready_items`/`default_roots`).
  The rule for what else goes: delete every module-level function whose
  only call path — however many hops — starts inside `render_html` or
  `build_actions_script` and never reaches `main()`'s surviving `--json`
  branch or the four agent-console-imported entry points. A hardcoded
  name list goes stale as the file changes (this is the second round this
  spec has under-enumerated the orphan set — verify with the reachability
  check below, don't hand-count). As of this spec's authoring, that
  reachability check finds **27 orphaned functions**, illustrative and
  not exhaustive at implementation time: `render_batons`, `render_ready`,
  `render_actions`, `render_inbox`, `render_filter_tiles`,
  `render_spend_section`, `_session_timeline_html`, `_spawn_tree_html`,
  `_spawn_nodes_html`, `_agent_chip`, `_agent_time_html`,
  `_count_spawn_nodes`, `_inbox_group`, `_spec_dag_html`,
  `_spec_dag_tasks`, `_spec_health_marker`, `_unblock_marker`,
  `progress_bar`, `handoff_pickup_cmd`, `cmd_html`, `badge`, `esc`,
  `_fmt_dollars`, `_fmt_tokens`, `_short_model_name`, `_session_badge`,
  `_fmt_dur`. (Several — `_spawn_tree_html`'s docstring in particular —
  also cite the now-deleted `fleet/reference.md`; deleting the function
  removes the citation too, so R1's dangling-citation cleanup needs no
  separate pass over code this task deletes anyway. The embedded
  chip-CSS block lives inside the module-level `TEMPLATE` constant below
  — not inside `render_html`'s own body, which only does `return
TEMPLATE.format(...)` — so it is covered by the module-level-constant
  rule below, not automatically deleted along with the function itself.)
  The same reachability rule applies one level up, to **module-level
  constants** (a simple top-level `NAME = <expr>` assignment), not just
  functions: any such constant whose only referencing code sits inside
  the deleted function set is deleted too. As of this spec's authoring,
  that is **`TEMPLATE`** (`workboard.py:2577-2827`, 251 lines — the HTML
  template string itself, including the embedded chip-CSS above; its only
  consumer is `TEMPLATE.format(...)` inside `render_html`), plus
  `STATE_BADGE` (consumed only by `badge`), `INBOX_CATEGORIES` and
  `FILTER_CATEGORIES` (consumed only by `render_inbox`/
  `render_filter_tiles`), `_AGENT_CHIP_GLYPH` (consumed only by
  `_agent_chip`), `_NO_UNBLOCK_CHIP` (consumed only by `_unblock_marker`),
  and `_MODEL_DATE_RE` (consumed only by `_short_model_name`) — same
  illustrative-not-exhaustive caveat as the function list; verify with the
  reachability check below, which now covers both. `--json` (used by
  `list-specs`, `workboard-auto-triage`, and step 2's inbox relay) is
  unaffected — it does not call any function in the orphaned set. With
  no `--out` path left, `main()`'s no-`--json`-flag behavior is: print
  the same one-line summary the HTML path used to log (repo/spec/task/
  session counts), no file of any kind.
- **R5**: `workboard/SKILL.md` no longer documents a static-HTML fallback.
  If `curl .../healthz` fails AND the direct background-start attempt
  also fails, the skill reports the failure and what to check (is Python
  available, is the port free, `SKILLS_DASHBOARD_PORT`/`_HOST`) — it does
  not fall back to writing a file.
- **R6**: `/fleet` was **never mirrored to Antigravity** —
  `antigravity/README.md:35` records this as a deliberate decision
  ("`/fleet` open-agents dashboard | Not ported — Antigravity's Agent
  Manager is this surface natively"), and no
  `antigravity/.agents/skills/fleet/` exists today. This spec does not
  create one — confirm it stays absent, don't read R1/R2's fleet changes
  as requiring an Antigravity counterpart. Per CLAUDE.md's mirroring
  convention, only the `/workboard`-side changes need mirroring:
  `antigravity/.agents/skills/workboard/workboard.py` (its own
  `render_html`/`build_actions_script`/`--out`/`--actions-out` and its
  `test_workboard.py`) and `antigravity/.agents/skills/_shared/viz.py`
  (its own `_emit_fleet_css`/`--emit-fleet-css`, per R3 — this file exists
  in the Antigravity mirror independent of fleet not being ported there,
  since `_shared` is used by workboard's mirror too). R1's dangling-
  `fleet/reference.md`-citation cleanup applies here too — antigravity's
  own `workboard.py`, `test_workboard.py`, `reference.md`, and
  `SKILL.md` carry the same citation pattern independently (this mirror
  is not a copy of the `.claude` files, so its citations are a separate
  cleanup, not automatically fixed by R1's edit to the `.claude` leg).
  Exactly two antigravity-side mentions of the word "fleet" are
  explicitly left untouched by this spec — every OTHER antigravity
  mention (the dangling-citation set above, plus any generic "fleet-style"/
  "fleet convention"/"fleet's status chip(s)" phrasing describing
  workboard's reused visual convention, per R1) is in scope, not exempt
  by default: `antigravity/README.md:35`'s not-ported row itself (it
  correctly records that fleet isn't ported — it is not stale and is not
  reworded to "inline table," since there's no ported fleet skill there
  to describe) and `antigravity/AGENTS.md`'s "scale the fleet only for
  genuinely divisible" line (the mirror of `token-discipline.md`'s
  identical unrelated prose, already exempted for the `.claude/` copy in
  R1).
- **R7**: `.claude-plugin/plugin.json`'s version is bumped (skill behavior
  changed in two skills).
- **R8**: Every existing test that exercises a code path this spec
  deletes is removed, in both `.claude/` and its `antigravity/` mirror —
  no dangling test referencing removed functionality:
  - `tests/test_workboard_render.sh` and `tests/test_workboard_actionability.sh`
    are **deleted outright**, not rewritten — both files' entire premise
    is the `--out`/`--actions-out` HTML-and-actions-script output (copy
    buttons, filter tiles, inbox grouping, the actions-script content),
    and R4 removes that whole output surface; nothing of either file's
    assertions has anything left to assert against once `render_html`/
    `build_actions_script` are gone. Their fixture trees,
    `tests/fixtures/workboard/` and `tests/fixtures/workboard-actionability/`,
    are deleted too — confirmed today each is consumed exclusively by the
    one test file it's named for, nothing else references either path.
  - `tests/test_fleet_css_drift.sh` is **deleted outright**: both sides
    of the diff it runs (`viz.py --emit-fleet-css`, removed by R3;
    `fleet/reference.md`, removed by R2) are gone.
  - `.claude/skills/workboard/test_workboard.py`'s test methods that call
    `render_html(...)` **or any other function or constant in R4's
    orphaned-deletion set** directly (not via `--out` — these are unittest
    calls into the functions themselves, so R4's `--out`-focused language
    doesn't reach them on its own) are deleted along with those functions
    — not `render_html` alone: confirmed today, this file also directly
    calls `render_batons`, `render_inbox`, `render_filter_tiles`,
    `render_spend_section`, `_spec_dag_html`, `_spec_dag_tasks`, and
    `_short_model_name`, all seven in R4's orphaned set.
    Illustrative-not-exhaustive, same caveat as
    R4's own function list — verify against whatever the file's calls
    look like at implementation time, don't trust this name list blindly.
    The tests that genuinely survive (covering `assemble`/
    `attention_items`/`ready_items`/`default_roots`/`--json`) are the ones
    that call none of R4's orphaned names, not a fixed list assumed safe
    in advance.
  - The antigravity mirror's `test_workboard.py` gets the identical
    treatment — confirmed today to have the same orphaned-function calls
    at the same line numbers (R6).

## Out of scope

- Any change to `agent-console.py`'s own live-serving mechanism or the
  `/workboard` route's scan logic — untouched by this spec.
- Retiring `--json` or any other non-HTML `workboard.py` output mode.
- Building any cross-session or cross-process view of "this session's
  agents" inside `/workboard` — the earlier draft's premise, now
  rejected as unbuildable (see Problem).

## Acceptance criteria

- [ ] `.claude/skills/fleet/reference.md` does not exist;
      `.claude/skills/fleet/SKILL.md` describes printing a markdown table,
      not rendering/writing HTML.
- [ ] `grep -c "self-contained HTML snapshot" .claude/skills/fleet/SKILL.md`
      → 0 (confirmed present today, must go to 0 — the frontmatter
      `description` line is rewritten to describe the inline markdown-table
      output, per R2; this is the skill's auto-invocation trigger surface,
      not just body prose).
- [ ] `grep -n "_emit_fleet_css\|--emit-fleet-css" .claude/skills/_shared/viz.py`
      returns no matches.
- [ ] `grep -n "render_html\|build_actions_script\|--out\|--actions-out"
.claude/skills/workboard/workboard.py` returns no matches (R4 — note
      this deliberately also catches `--actions-out`, not just `--out`).
- [ ] `grep -n "^TEMPLATE = " .claude/skills/workboard/workboard.py` returns
      no match (R4's module-level-constant rule — a concrete backstop for
      the single largest orphaned item, the 251-line HTML template
      string; the reachability check below is the general-purpose
      catch-all, this is belt-and-suspenders for the biggest piece).
- [ ] Dead-code reachability check (R4 — count-independent, catches the
      full orphaned set rather than a fixed name list that will drift as
      the file changes again; covers **both functions and module-level
      constants** in one pass, per R4's constants rule): save the script
      from the "Reachability check script" section below as
      `/tmp/orphan_check.py` and run `python3 /tmp/orphan_check.py
.claude/skills/workboard/workboard.py` **after** deleting
      `render_html`/`build_actions_script` and their orphaned callees and
      constants — it prints `clean` (exit 0) once the deletion is
      complete; any remaining orphan (function or constant) fails loudly
      with the name list. Run it **before** any deletion first and
      confirm it prints `clean` too (expected: `render_html` is still
      reachable from `main()` pre-edit, so the whole file is "clean" in
      that state — this is a real behavior, not a bug; the check only
      fails when something is deleted incompletely, not when nothing is
      deleted yet). Don't mistake a pre-deletion `clean` for "nothing to
      delete."

- [ ] `grep -n "Fallback (machines without agent-console)"
.claude/skills/workboard/SKILL.md` returns no match.
- [ ] `python3 .claude/skills/workboard/workboard.py --json` still runs
      and produces valid JSON (unaffected mode).
- [ ] `git grep -n '\bfleet\b' -- .claude/ antigravity/ docs/ AGENTS.md
CLAUDE.md .claude-plugin/` shows only: (a) the new inline-table
      description, (b) legitimate unrelated prose (any generic idiom like
      "scale the fleet", "a fleet of launched [workers]", or a citation to
      workboard's own reused glyph+word status-chip visual convention —
      "fleet-style", "fleet's status chip(s)", "fleet convention" — not
      limited to the specific instances R1 happens to name, since new
      instances of these same patterns can appear as the tree changes),
      or (c) `antigravity/README.md:35`'s not-ported row, left exactly
      as-is — no stale HTML-snapshot description and no dangling citation
      of the deleted `fleet/reference.md` remains anywhere else.
- [ ] `git grep -rn 'fleet/reference\.md' -- .claude/ antigravity/`
      returns no matches (confirms R1/R6's dangling-citation cleanup is
      complete in both trees — a mechanical, count-independent backstop
      for the sweep AC above).
- [ ] `antigravity/.agents/skills/fleet/` does not exist (unchanged from
      before this spec — R6 confirms, doesn't create).
- [ ] The workboard/viz.py checks above (workboard `--out`/`--actions-out`
      gone, the dead-code reachability check clean, viz.py
      `--emit-fleet-css` gone, fallback bullet gone) also hold under
      `antigravity/.agents/skills/workboard/` and
      `antigravity/.agents/skills/_shared/viz.py` (R6).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change.
- [ ] `git grep -ln 'fleet\.html\|--out\|--emit-fleet-css' -- evals/`
      returns no matches (no fixture/eval case left pointing at fleet's
      old HTML output, the deleted `--out` flag, or `--emit-fleet-css`) —
      a static check, not `bash evals/run.sh` (the paid, human-launched
      `/evals` runner; drained/unattended workers may not gate on it).
- [ ] `bash evals/lint-ultra-gate.sh` exits 0 (R1's edit to
      `drain/SKILL.md`, an ultra-path skill, must not disturb the
      ultra-gate marker).
- [ ] R8 test deletions, deterministic: `[ ! -f tests/test_workboard_render.sh
] && [ ! -f tests/test_workboard_actionability.sh ] && [ ! -f
tests/test_fleet_css_drift.sh ] && [ ! -d tests/fixtures/workboard ] && [
! -d tests/fixtures/workboard-actionability ]` (all three test files and
      both fixture trees deleted outright, not rewritten — R8).
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` exits 0 —
      the full gated shell-test suite (AGENTS.md's canonical command) is
      green after R8's deletions, catching any other test this spec's
      removals broke beyond the three named above.
- [ ] `python3 -m unittest discover -s .claude/skills/workboard` exits 0,
      and the same command against `antigravity/.agents/skills/workboard`
      exits 0 — no `render_html`-calling test method survives in either
      tree's `test_workboard.py` (R8).
- [ ] End-to-end: running `/fleet` in a session with at least one
      background agent prints the markdown table and summary line
      directly in the response — no `fleet.html` (or any file) is written
      anywhere. **Manual-pending**: this requires an attended session with
      a live harness `TaskList` and skill invocation, which a drained/
      unattended worker cannot exercise — mark this criterion
      manual-pending with this reason rather than deferring or guessing
      (docs/memory/unattended-worker-tool-limits.md); the orchestrator or
      a human runs it post-merge.

## Reachability check script

Referenced by the R4 dead-code acceptance criterion above. Deliberately
placed at the top level, not nested inside a list item — a prior draft
embedded it inside the AC bullet's own fenced code block and this repo's
prose-formatter hook reflowed the indentation, breaking the script with
an `IndentationError` (caught by re-critique; see critique-findings.md).
This version generalizes the graph from function-call edges to general
Name-reference edges, so the same pass catches both orphaned functions
and orphaned module-level constants (e.g. `TEMPLATE`) in one run — a
constant-call-only graph would miss `STATE_BADGE.get(...)`-style
attribute/subscript access on a constant, since that isn't a `Call` whose
`func` is the constant's own name. Save verbatim as `/tmp/orphan_check.py`:

```python
import ast, sys
path = sys.argv[1]
tree = ast.parse(open(path).read())

class Refs(ast.NodeVisitor):
    def __init__(self):
        self.names = set()
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.names.add(node.id)
        self.generic_visit(node)

def is_simple_assign(node):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)) or (
            isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name))

def assign_name(node):
    return node.targets[0].id if isinstance(node, ast.Assign) else node.target.id

defs = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        defs[node.name] = node.body
    elif is_simple_assign(node):
        defs[assign_name(node)] = [node.value] if getattr(node, "value", None) else []

graph = {}
for name, body in defs.items():
    r = Refs()
    for stmt in body:
        r.visit(stmt)
    graph[name] = r.names

module_refs = Refs()
for node in tree.body:
    if not (isinstance(node, ast.FunctionDef) or is_simple_assign(node)):
        module_refs.visit(node)

entry = {"main", "assemble", "attention_items", "ready_items", "default_roots"} | module_refs.names
visited, frontier = set(), list(entry)
while frontier:
    n = frontier.pop()
    if n in visited:
        continue
    visited.add(n)
    frontier.extend(graph.get(n, set()))

orphaned = set(defs) - visited - {"main"}
if orphaned:
    print("ORPHANED:", sorted(orphaned))
    sys.exit(1)
print("clean")
```

Sanity-checked against both trees today: pre-deletion, both `.claude` and
`antigravity` copies of `workboard.py` print `clean` (expected — nothing
deleted yet, everything is still reachable through `render_html`). A
synthetic before/after/incomplete-deletion test (a function-only orphan
check would pass an incomplete deletion that leaves an orphaned constant
behind; this version correctly flags it) is in this spec's
`critique-findings.md`.

## Open questions

(none)
