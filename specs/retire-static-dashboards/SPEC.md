# Drop static HTML output: /fleet prints a table instead of a file, workboard's HTML fallback goes

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
`TaskList` entries and `git worktree list` output for *this specific
session* — comes from in-process harness state only the invoking session
can see (`fleet/SKILL.md` step 1). `agent-console` is a separate,
shared server process reached via a bare URL with no session id passed;
`workboard.py`'s own `scan_sessions` only enumerates whole top-level
Claude Code sessions (one `.jsonl` transcript each) via `cwd`/timestamps —
it has no visibility into any session's live sub-agents. There is no way
for the live dashboard to reconstruct fleet's view. Retiring fleet in
favor of it would be a real capability loss, not a consolidation.

## Solution

Keep `/fleet` — its *data-gathering* mechanism (steps 1-2 of its current
SKILL.md: harness `TaskList` + `git worktree list`, normalized into one
record per agent) is correct and stays exactly as-is. Only its *output*
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
  alone — they don't refer to the skill.
- **R2**: `fleet/SKILL.md` no longer contains an HTML-rendering step;
  `fleet/reference.md` no longer exists.
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
  `--json` (used by `list-specs`, `workboard-auto-triage`, and step 2's
  inbox relay) is unaffected. With no `--out` path left, `main()`'s
  no-`--json`-flag behavior is: print the same one-line summary the HTML
  path used to log (repo/spec/task/session counts), no file of any kind.
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
  since `_shared` is used by workboard's mirror too). Two remaining
  antigravity-side mentions of the word "fleet" are explicitly left
  untouched by this spec: `antigravity/README.md:35`'s not-ported row
  itself (it correctly records that fleet isn't ported — it is not stale
  and is not reworded to "inline table," since there's no ported fleet
  skill there to describe) and `antigravity/AGENTS.md`'s "scale the fleet
  only for genuinely divisible" line (the mirror of
  `token-discipline.md`'s identical unrelated prose, already exempted for
  the `.claude/` copy in R1).
- **R7**: `.claude-plugin/plugin.json`'s version is bumped (skill behavior
  changed in two skills).
- **R8**: Any existing test that exercises `workboard.py --out ...`,
  fleet's old HTML template, or `viz.py --emit-fleet-css` is deleted or
  rewritten to match the new behavior — no dangling test referencing a
  removed code path, in either `.claude/` or its `antigravity/` mirror.

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
- [ ] `grep -n "_emit_fleet_css\|--emit-fleet-css" .claude/skills/_shared/viz.py`
      returns no matches.
- [ ] `grep -n "render_html\|build_actions_script\|--out\|--actions-out"
      .claude/skills/workboard/workboard.py` returns no matches (R4 — note
      this deliberately also catches `--actions-out`, not just `--out`).
- [ ] `grep -n "Fallback (machines without agent-console)"
      .claude/skills/workboard/SKILL.md` returns no match.
- [ ] `python3 .claude/skills/workboard/workboard.py --json` still runs
      and produces valid JSON (unaffected mode).
- [ ] `git grep -n '\bfleet\b' -- .claude/ antigravity/ docs/ AGENTS.md
      CLAUDE.md .claude-plugin/` shows only: (a) the new inline-table
      description, (b) the legitimate unrelated prose uses named in R1
      (including `antigravity/AGENTS.md`'s "scale the fleet" line), or
      (c) `antigravity/README.md:35`'s not-ported row, left exactly as-is
      — no stale HTML-snapshot description remains anywhere else.
- [ ] `antigravity/.agents/skills/fleet/` does not exist (unchanged from
      before this spec — R6 confirms, doesn't create).
- [ ] The workboard/viz.py checks above (workboard `--out`/`--actions-out`
      gone, viz.py `--emit-fleet-css` gone, fallback bullet gone) also
      hold under `antigravity/.agents/skills/workboard/` and
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
- [ ] End-to-end: running `/fleet` in a session with at least one
      background agent prints the markdown table and summary line
      directly in the response — no `fleet.html` (or any file) is written
      anywhere. **Manual-pending**: this requires an attended session with
      a live harness `TaskList` and skill invocation, which a drained/
      unattended worker cannot exercise — mark this criterion
      manual-pending with this reason rather than deferring or guessing
      (docs/memory/unattended-worker-tool-limits.md); the orchestrator or
      a human runs it post-merge.

## Open questions

(none)
