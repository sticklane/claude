# Tech debt / follow-ups

- **workboard: surface per-session token/cost.** Anthropic's multi-agent
  research guidance (docs/agent-dashboards.md) says cost belongs on any
  agent-management surface — token usage explains ~80% of performance
  variance. Session records may carry usage data; if so, add a cost column
  to the sessions tables and a total tile. (2026-07-03)
- **workboard: `--abandon` for stale toolkit specs.** The abandon-marker
  mechanism only covers Antigravity conversations; stale `specs/<slug>`
  dirs still require manual `Status: deferred` edits or deletion. Consider
  a symmetric one-command defer. (2026-07-03)
- **agentprof: surface pricing-table staleness.** The rate table's only
  freshness marker is a comment (`internal/pricing/table.go`, "fetched
  2026-07-02"), and the table already knowingly diverges (Sonnet's
  introductory $2/$10 through 2026-08-31 "is not modeled" per its own
  note) with nothing flagging it at runtime. Add a fetched-date constant
  surfaced in summary output plus a documented refresh procedure;
  `pricing_test.go` only re-does the arithmetic, so it can never catch
  drift from real prices. (2026-07-10)
- **agent-console: make the pprof URL configurable.** The sibling
  agentprof UI is hardcoded as `http://127.0.0.1:8901` at
  `agent-console.py:1793` and `:2138` while the console's own `PORT`/
  `HOST` are env-configurable; `tests/test_profile_links.py:70` pins the
  literal. Introduce an `AGENTPROF_URL`-style env default and update the
  test. (2026-07-10)
- **agent-console: log the silent broad excepts.** `_running_pid_for`
  (`agent-console.py:567`) and `_claude_run_bg` (`:2334`) catch
  `Exception` and drop it with no logging, unlike the two commented
  request-boundary catches — a lookup or repo-scan failure vanishes. Add
  a debug log line. (2026-07-10)
- **agent-console: collapse duplicated row/section rendering.** The
  `line/trunc/meta` row skeleton is hand-built at `agent-console.py:1933`,
  `:1984`, `:1992`, `:2000`, and the three detail-page renderers
  (`render_repo_page:1193`, `render_session_page:1380`,
  `render_spec_page:1442`) each rebuild the same `parts=[]` + section-div
  scaffold. A `row(...)` and `section(title, html)` helper pair removes
  the copies. (2026-07-10)
- **agent-console: name the magic numbers.** Scattered literals — panel
  top-N `[:5]` (`agent-console.py:1930`), prompt truncation `[:90]`
  (`:2000`), `tail_events` defaults `n=50, window=65_536` (`:1287`), 4s
  git timeout (`:364`) — should be named constants (env-configurable only
  where there's a real reason, matching the existing stop-grace model).
  (2026-07-10)
- **agentprof: collapse cmd_* flag/positional boilerplate.** The
  FlagSet-setup → `parsePositionals` → "expected exactly one … file"
  head block is near-identical across `cmd_gcp.go:14-26`,
  `cmd_vertex.go:13-24`, `cmd_otel.go:31-41`, and the `-o` flag string is
  repeated verbatim in five files; `run_adapter.go` already collapsed the
  shared tail — add the companion head helper. (2026-07-10)
- **drain/SKILL.md is at 501 lines.** CLAUDE.md requires SKILL.md bodies
  "well under 500 lines"; drain is the only breach (next largest is 184).
  Move detail into its (already TOC'd) reference.md. (2026-07-10)
- **Normalize `Next stage:` closers on the execution skills.**
  `build`, `drain`, and `autopilot` SKILL.md files have no `Next stage:`
  line at all despite producing artifacts (evals/SKILL.md:56 shows the
  execution-stage form), and `fleet/SKILL.md:52` uses the wrong label
  ("Next pipeline step:"). Either add conforming closers or write the
  execution-stage carve-out into CLAUDE.md's convention — currently it
  reads as drift. (2026-07-10)
- **distill's `model: opus` frontmatter vs the no-bare-model convention.**
  CLAUDE.md says skills use tier language, "never a bare model name", but
  `distill/SKILL.md:4` pins `model: opus` in frontmatter. Decide: exempt
  frontmatter `model:` pins explicitly in the convention (agents already
  pin aliases by design) or route distill through tier language.
  (2026-07-10)
- **install-gates: HOOK_TEMPLATES relies on word-splitting.** The
  `for h in $HOOK_TEMPLATES` loops (`bin/install-gates:586`, `:617`)
  word-split a fixed literal — safe today, the one shellcheck (SC2086)
  flag in bin/; a bash array is future-proof. (2026-07-10)
- **~/claude checkout-location fallbacks in shipping code.**
  `workboard.py:1248` falls back to `Path.home()/"claude/agentprof/agentprof"`
  and `bin/sync-workflows:18` defaults SRC to `$HOME/claude/.claude/workflows`
  — both env-overridable, but a plugin installed elsewhere gets a dead
  fallback. Derive from the script's own location where possible.
  (2026-07-10)
- **implementation-worker.md has no self-contained output budget.**
  scout (≤300 words), verifier ("under a page"), and critic all bound
  their output per the conventions; implementation-worker defers entirely
  to the dispatch prompt. Add a fallback cap or document the
  dispatch-prompt-owns-it decision in the agent file. (2026-07-10)
- **agent-console: duplicate `claude agents --json` spawn per board rebuild.**
  `workboard.assemble()` fetches it (`.claude/skills/workboard/workboard.py:687`)
  and `agents_view()` fetches it again (`agent-console/agent-console.py:541`) —
  two subprocess spawns, each with an 8s timeout, on every rebuild. Share one
  fetch per rebuild cycle. (2026-07-10, from archived-repo review; the GitHub
  `sticklane/agent-console` repo is an archived stale snapshot — all fixes land
  here)
- **agent-console: `gh_visibility` has no negative caching.** The cache
  timestamp advances only on success, so a present-but-failing `gh` re-runs a
  12s-timeout `gh repo list` on every post-TTL rebuild — contradicts CLAUDE.md's
  "off the hot path". Cache failures with a shorter TTL. (2026-07-10)
- **agent-console: `set_priority` invalidates the wrong cache.**
  `agent-console.py:2879` zeroes `_plugins_cache["ts"]` (self-described no-op)
  forcing a needless plugin-list respawn instead of invalidating the board
  cache it actually affects. (2026-07-10)
- **agent-console: doc drift.** Docstring still says "Run: skills-dashboard.py"
  (`agent-console.py:14`); README claims board cache "~20s" vs `BOARD_TTL = 45`
  (`:310`); env naming split `AGENT_CONSOLE_PORT` (install.sh) vs runtime
  `SKILLS_DASHBOARD_PORT`. Align all three. (2026-07-10)
- **agent-console: test gaps beyond the mutation-endpoints spec.**
  `parse_repos` is only ever mocked, never tested directly; `apply_priority`'s
  insert-after-H1 branch is untested. (2026-07-10)
- **workboard: live server hangs on /workboard.** The agent-console
  workboard server (port 8899, launchd) hangs — `curl
  http://127.0.0.1:8899/workboard` timed out 3x (60-85s, 0 bytes) on
  2026-07-13 while the process idled (~8s CPU over minutes); suspected
  slow/disconnected filesystem mount in its scan path. Investigate and
  fix; do NOT restart the service as part of filing this — the hung
  state is the evidence. (2026-07-13, verification sweep)
- **drain/SKILL.md length rebound: 520 lines.** `.claude/skills/drain/SKILL.md`
  is at 520 lines vs the 500-line convention; drain-wake-cost task 04 got
  it to 495 but task 05 (d35fc9e), follow-up a87a324, and the 473cb51
  one-liner pushed it back up. Trim/relocate prose (the d51ce4b9
  reference.md pattern) without content loss. (2026-07-13, verification
  sweep)
