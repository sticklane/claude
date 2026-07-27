# workboard reference — data sources and state model

Loaded on demand. The scanner (`workboard.py`) is the source of truth; this
documents what it reads and why, so a debugging session doesn't have to
reverse-engineer it.

## Data sources

One deliberate work-state write exists. `--abandon <conv-id>` /
`--abandon-stale` drop a `.workboard-abandoned` marker file into an
Antigravity conversation dir so the scanner skips it permanently;
Antigravity's own artifacts (`task.md`, metadata) are never modified, and
undo = delete the marker. Toolkit task state is read-only and comes from bd.
Tests:
`python3 -m unittest discover -s .claude/skills/workboard`.

| Source | Path | What it yields |
|---|---|---|
| Toolkit specs | authored definitions under `<repo>/specs/<slug>/`, `bd list --all --json`, and `bd show --json --include-comments` for blocked/deferred task issues | titles, evidence history, and filenames from markdown; live status, typed `blocks` dependencies, typed unblock details, deferred questions, and `verification_required` from bd metadata/notes/comments for issues whose external reference is `spec-task:<path>`. A blocked issue with `metadata.verification_required=true` renders as `needs-verification`, stays out of `bd ready`, and is not shown as an ordinary blocker. Frozen markdown status, dependency, unblock, and deferred-question text never drive the dashboard |
| Kiro specs | `<repo>/.kiro/specs/<name>/tasks.md` | checkbox states — `[ ]` todo, `[-]` doing, `[x]` done; phase = which of requirements/design/tasks files exist |
| Handoffs | `bd list --label handoff --status=open --json`, per scanned repo with a `.beads/` dir | parked work waiting on a human — always an inbox item. One bounded `bd` call per repo; a repo without `.beads/` is skipped without invoking `bd`, and a missing binary, timeout, non-zero exit, or unparseable output yields no handoffs rather than failing the scan |
| Claude Code sessions | `~/.claude/projects/<escaped-cwd>/<sessionId>.jsonl` | first user prompt (head read), `cwd`, `gitBranch`, last-record timestamp (64 KB tail read — transcripts are never read wholesale) |
| Claude Code live sessions | `claude agents --json`, with `~/.claude/sessions/<pid>.json` as the Claude-only fallback | sessionId → pid; `active` only when the runtime reports a live process |
| Codex sessions | `$CODEX_HOME/sessions/**/rollout-*.jsonl` (default `~/.codex`) | native resume ID, `cwd`, first user prompt, and last activity. Codex has no supported machine-wide live-process inventory, so these are never labeled `active` and carry `liveness_supported:false` |
| Antigravity CLI sessions | `$ANTIGRAVITY_DIR/cache/conversation_metadata.json` (default `~/.gemini/antigravity-cli`) | native conversation resume ID, workspace URI, summary, and last activity. Antigravity has no supported machine-wide live-process inventory, so these are never labeled `active` and carry `liveness_supported:false` |
| Claude Code todos | `~/.claude/todos/*.json` (when the install has them) | open in-session todo lists; not read under another runtime |
| Antigravity | `~/.gemini/antigravity*/brain/<conversation>/` | `task.md` checkbox counts + `task.md.metadata.json` summary/updatedAt; conversations containing a `.workboard-abandoned` marker are skipped |
| Git | the repo's VCS, queried in-repo | branch, dirty count, ahead/behind upstream, worktrees, last-commit time |

`AGENTIC_RUNTIME` selects `claude-code`, `codex`, or `antigravity`;
session discovery never crosses that boundary. `CLAUDE_CONFIG_DIR`,
`CODEX_HOME`, and `ANTIGRAVITY_DIR` override their respective defaults.
Repo discovery walks the given roots (depth ≤ `--max-depth`, pruning
`node_modules`, venvs, dot-dirs), plus the repo root of every native session
`cwd` when the runtime records one.

## State model

Two axes, following Antigravity (decision-oriented status) and Kiro
(artifact-derived progress):

- **Session states**: Claude Code can report `active` (live pid), then
  `recent` (<48 h) → `idle` → `stale` (> `--stale-days`, default 7).
  Codex and Antigravity use the time-derived states but never claim `active`
  because their supported local metadata does not expose machine-wide
  liveness.
- **Work states** (inbox): `blocked` (an open `handoff`-labeled bd issue, or a
  task whose bd status is neither open nor closed, or a tracker read that
  failed), `needs-review` (all tasks done but spec not archived; dirty repo
  with no live session when Claude Code liveness is known, or dirty work whose
  live-session state is explicitly unavailable under Codex/Antigravity;
  unpushed commits), `stale` (open tasks untouched past the threshold). A
  missing `.beads/` directory routes to tracker
  initialization; missing issues in a successfully read tracker route to
  create-only spec registration; command, timeout, and JSON failures route to
  a bd-read retry instead.

Severity order in the inbox: serious (blocked) before warning
(needs-review/stale), newest first within a tier. Every state renders as
glyph + word (`⚑ blocked`, `▲ needs-review`, `● active`) — color never
carries meaning alone. Palette is the toolkit's pre-validated reference set
(light and dark both selected, not auto-flipped); light-mode warning/serious
use darkened text-safe variants since they render as text, not fills.

## JSON schema (`--json`)

Top-level keys: `generated_at`, `runtime`, `stale_days`, `totals` (`repos`,
`specs_open`, `tasks_open`, `sessions_active`, `attention`), `inbox[]`
(`severity`, `state`, `repo`, `what`, `why`, `age_ts`, plus `cmd` — a
runnable shell command — on items with a one-command fix), `repos[]` (`path`,
`name`, `git`, `specs[]`, `handoffs[]`, `sessions[]`), `sessions[]`,
`orphan_sessions[]` (sessions whose cwd is outside every scanned repo),
`antigravity[]`, `todos[]`. Each `handoffs[]` record is one open
`handoff`-labeled bd issue: `id`, `title`, `tracked_ids` (the ids it
`tracks`), `updated_ts`. Each session record carries `runtime` and
`liveness_supported`. It also carries `spawn_tree` — the nested agent-spawn
tree for Claude Code sessions (see `scan_session_spawns` under Extending);
`[]` for Codex/Antigravity or a Claude Code session with no recorded spawn.
Toolkit spec records also carry `tracker_state` and `tracker_error`, so an
unavailable tracker never masquerades as an empty, successfully read one.

## Extending

New work sources follow the same shape: a `scan_*` function returning
records with a `last_touched`/`last_ts`, wired into `assemble()` and (if it
can demand a human decision) `attention_items()`. Keep each durable source
artifact-first and query a live inventory only when the selected runtime
provides one; never query another runtime as a fallback.

`scan_session_spawns(claude_home)` is an instance of this contract keyed to
sessions rather than repos: it returns `{session_id -> {spawn_tree,
last_touched, last_ts}}`, running `extract_agent_tree()` over each
`projects/<proj>/<sid>.jsonl` transcript. `assemble()` runs it only for
Claude Code and merges each `spawn_tree` onto that session's existing record;
other runtimes receive `[]` rather than reading Claude transcripts.
