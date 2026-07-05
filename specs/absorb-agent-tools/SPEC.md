# Absorb agentprof and agent-console into the toolkit repo

## Problem

The agentic toolkit's supporting tools live in two sibling repos:
`~/agentprof` (Go CLI: Claude/GCP/Vertex/OTEL spend data → pprof flame
graphs) and `~/agent-console` (Python stdlib dashboard server, launchd
`com.agent-console` on port 8899, serving the skills view and the
`/workboard` tab that the toolkit's workboard skill launches). The split
costs real coordination: agent-console vendors `viz.py` from this repo
behind a byte-identity conformance gate, the workboard skill bundles its
own scanner (`workboard.py`) parallel to the console's in-server scanner
(`scan_specs`/`build_board`), and toolkit specs (shared-viz-renderer,
workboard-cli-graphs-health) have had to reach across repos to change
console behavior. The tool code is generic (config via env vars, templated
launchd installer, no personal data in agent-console's tracked files) —
the one exception is agentprof's archived spec/evidence files, which embed
`/Users/sjaconette/...` absolute paths and are handled below. Both belong
in `sticklane/claude` as first-class components, with the standalone repos
archived.

## Solution

Fresh file copy (no history import) of each repo's tracked files into two
new top-level, repo-only directories — `agentprof/` and `agent-console/` —
alongside `evals/` and `runtimes/`. Neither ships in the plugin
(`.claude-plugin/` manifest points only at `.claude/skills/`; nothing new
lands under `.claude/skills/` except edits to existing files). Dedupe in
one direction: the skill tree is the single source of scan/render logic —
`agent-console/` loses its vendored `viz.py` (imports
`.claude/skills/_shared/viz.py`) and its in-server scanner (imports
`.claude/skills/workboard/workboard.py`, which already exposes an
importable API: `assemble()`, `attention_items()`, `ready_items()`).
The console KEEPS its own `render_workboard` tab renderer, fed by a thin
adapter that maps `workboard.assemble()`'s result shape
(`{repos, sessions, inbox, ready, totals, ...}`) to the board dict
`render_workboard` expects — the adapter is the only new logic, and the
console's `scan_specs`/`scan_tasks`/`scan_handoffs`/`build_board` are
deleted. The conformance gate dies with the vendored copy. The workboard
skill's bundled fallback behavior for plugin consumers is unchanged.
Close-out (attended): archive both GitHub repos, reinstall the launchd
service from the toolkit checkout, delete the old working copies.

Component internals otherwise stay as-is: agentprof keeps its Go module
path `github.com/sticklane/agentprof` (binary-only, no external importers)
and its own `scripts/check.sh`; agent-console keeps `install.sh`/
`uninstall.sh` and its env-var config (`AGENT_CONSOLE_REPOS`,
`SKILLS_DASHBOARD_PORT/HOST`).

## Requirements

- R1: `agentprof/` at the repo root contains agentprof's tracked files
  (copied from `~/agentprof` HEAD), excluding: `.git/`, any nested
  `.claude/` directory (standalone-checkout hooks/settings don't apply in
  a subdirectory), and `specs/` (the archived spec/evidence files embed
  `/Users/sjaconette/...` absolute paths; that history stays readable in
  the archived GitHub repo). `docs/TASKS.md` IS copied (open tech-debt
  items travel with the code). `bash agentprof/scripts/check.sh` exits 0
  from the new location.
- R2: `agent-console/` at the repo root contains agent-console's tracked
  files (same `.git/`/`.claude/` exclusions). Its `scripts/check.sh` is
  UPDATED in the same change: the `viz.py --self-sha256` /
  `# viz-sha256:` conformance block is removed (R3), and the inline smoke
  test is rewritten from `build_board()`/`render_workboard(model)` to the
  new seam — it feeds a small fixture dict shaped like
  `workboard.assemble()` output through the R4 adapter into
  `render_workboard` and asserts the fixture's repo name appears in the
  rendered HTML. `bash agent-console/scripts/check.sh` exits 0 from the
  new location.
- R3: `agent-console/viz.py` (the vendored copy) and the byte-identity
  conformance check are deleted; the server resolves the renderer from
  `.claude/skills/_shared/viz.py` in the same checkout (path derived from
  the server file's own location, overridable by env var for non-checkout
  layouts).
- R4: the server's `/workboard` route obtains ALL scan data by importing
  `.claude/skills/workboard/workboard.py` as a module (same resolution
  rule as R3) and calling its API (`assemble()` /
  `attention_items()` / `ready_items()`); the console's own scanner
  functions (`scan_specs`, `scan_tasks`, `scan_handoffs`, `build_board`)
  are deleted. The console keeps `render_workboard`, fed by a new
  adapter function that maps the `assemble()` result to the board shape
  `render_workboard` consumes (including inbox item fields
  `sev/state/item/repo/why/age/cmd`). `workboard.py` itself stays
  stdlib-only and its CLI contract (`--json`, `--out`, ROOTS,
  `--stale-days`, `--abandon*`) is unchanged.
- R5: `agent-console/install.sh` renders the launchd plist against the
  new location; after an attended reinstall,
  `launchctl print gui/$(id -u)/com.agent-console` names
  `<repo>/agent-console/agent-console.py`, and
  `curl -fsS http://127.0.0.1:8899/healthz` returns ok with `/` and
  `/workboard` serving.
- R6: repo wiring — root `AGENTS.md` Map lists both directories with
  one-line roles, and its Commands section gains both check.sh lines
  (verified by running). EVERY occurrence of the literal
  `~/agent-console/agent-console.py` is replaced with
  `~/claude/agent-console/agent-console.py`: two in
  `.claude/skills/workboard/SKILL.md` (the launch fallback and the
  scanner-note), and the two body-line occurrences in the antigravity
  mirror's workboard skill (its frontmatter description carries no path
  literal — leave it). Because skill text changes, the antigravity
  mirror is updated in the
  same commit and `.claude-plugin/plugin.json` version is bumped (per
  CLAUDE.md authoring conventions).
- R7: no personal data rides in: case-sensitive
  `grep -rn "sjaconette\|Jaconette" agentprof/ agent-console/` → zero
  matches, and no rendered plist, cache, transcript, or profile artifact
  (`*.pb.gz`, `*.plist` without `.tmpl` suffix) is committed.
- R8 (attended close-out, human-gated): `sticklane/agentprof` and
  `sticklane/agent-console` are archived on GitHub; the old launchd
  install is removed and reinstalled from the toolkit checkout (R5); the
  `~/agentprof` and `~/agent-console` working copies are deleted only
  after R1–R7 are green on pushed `main`.

## Out of scope

- Any functional change to agentprof (the workflow run-id linkage gap is
  its own future spec) or new plugin skills wrapping it (no `/profile`
  skill now).
- Porting agent-console to Antigravity, or shipping either component in
  the plugin payload.
- Resolving `specs/shared-viz-renderer` blocked tasks 05–06 — but this
  migration deletes the vendoring conformance machinery that spec
  introduced, so those tasks must be re-triaged by a human afterward
  (their premise may be superseded).
- Visual/behavioral changes to the console's tabs beyond the R4 data
  seam — `render_workboard`'s output stays equivalent for equivalent
  data.
- Multi-machine install automation; the launchd reinstall is a one-off
  attended step on this machine.

## Acceptance criteria

- [ ] `bash agentprof/scripts/check.sh` → exit 0 (R1)
- [ ] `test ! -d agentprof/specs && test -f agentprof/docs/TASKS.md` (R1 exclusions)
- [ ] `bash agent-console/scripts/check.sh` → exit 0, and its source shows no `viz-sha256`/`--self-sha256` conformance block (R2, R3)
- [ ] `test ! -f agent-console/viz.py` (R3)
- [ ] `grep -cE "def (scan_specs|scan_tasks|scan_handoffs|build_board)" agent-console/agent-console.py` → 0, AND `grep -n "workboard" agent-console/agent-console.py | grep -c "import"` → ≥1 (R4: old scanner gone, skill module imported)
- [ ] `python3 .claude/skills/workboard/workboard.py --json` still emits the inbox JSON, and `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html` writes a page (R4 CLI contract)
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` and `./bin/check-agent-model-pins` and `./evals/runner-selftest.sh` all green (repo gates unchanged)
- [ ] `grep -rn "sjaconette\|Jaconette" agentprof/ agent-console/ | wc -l` → 0 (R7)
- [ ] `grep -rn "~/agent-console/agent-console.py" .claude/skills/ antigravity/ | wc -l` → 0, `grep -c "~/claude/agent-console/agent-console.py" .claude/skills/workboard/SKILL.md` → 2, and `git diff` shows plugin.json version bumped (R6)
- [ ] MANUAL (R5+R8, attended): reinstall launchd from checkout, `launchctl print gui/$(id -u)/com.agent-console | grep "claude/agent-console"` hits; `curl -fsS http://127.0.0.1:8899/healthz` → ok; `gh repo view sticklane/agentprof --json isArchived` and same for agent-console → true; old dirs removed
- [ ] End-to-end: with the reinstalled service running, `curl -fsS http://127.0.0.1:8899/workboard` returns a page whose inbox rows match `python3 .claude/skills/workboard/workboard.py --json` inbox items (same repos named), proving the console serves the skill-tree scanner's data

## Open questions

(none)

## Parallelization

- Group A (concurrent-safe): tasks 01 and 02 — disjoint Touch
  (`agentprof/` vs `agent-console/`), no dependency edge, and no shared
  undecided design (01 is a mechanical copy; 02's adapter seam is fully
  pinned in R4).
- Task 03 serializes after both (it wires what they created and runs
  their check.sh commands).
- Task 04 is ATTENDED ONLY (external services + machine state + working-
  copy deletion — fails drain's peripheral/core gate); run via /build
  after 03 is merged and pushed.
