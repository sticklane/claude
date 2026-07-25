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
| Toolkit specs | authored definitions under `<repo>/specs/<slug>/` plus `bd list --all --json` | titles, evidence/unblock prose, and filenames from markdown; live status and typed `blocks` dependencies from issues whose external reference is `spec-task:<path>`. Frozen markdown status/dependency headers never drive the dashboard |
| Kiro specs | `<repo>/.kiro/specs/<name>/tasks.md` | checkbox states — `[ ]` todo, `[-]` doing, `[x]` done; phase = which of requirements/design/tasks files exist |
| Handoffs | `bd list --label handoff --status=open --json`, per scanned repo with a `.beads/` dir | parked work waiting on a human — always an inbox item. One bounded `bd` call per repo; a repo without `.beads/` is skipped without invoking `bd`, and a missing binary, timeout, non-zero exit, or unparseable output yields no handoffs rather than failing the scan |
| Sessions | `~/.claude/projects/<escaped-cwd>/<sessionId>.jsonl` | first user prompt (head read), `cwd`, `gitBranch`, last-record timestamp (64 KB tail read — transcripts are never read wholesale) |
| Live sessions | `~/.claude/sessions/<pid>.json` | sessionId → pid; `active` iff the pid is alive (`kill -0`) |
| Todos | `~/.claude/todos/*.json` (when the install has them) | open in-session todo lists |
| Antigravity | `~/.gemini/antigravity*/brain/<conversation>/` | `task.md` checkbox counts + `task.md.metadata.json` summary/updatedAt; conversations containing a `.workboard-abandoned` marker are skipped |
| Git | the repo's VCS, queried in-repo | branch, dirty count, ahead/behind upstream, worktrees, last-commit time |

`CLAUDE_CONFIG_DIR` overrides `~/.claude`. Repo discovery: walk the given
roots (depth ≤ `--max-depth`, pruning `node_modules`, venvs, dot-dirs), plus
the repo root of every session `cwd` — so a repo you only
ever touched via Claude Code still appears.

## State model

Two axes, following Antigravity (decision-oriented status) and Kiro
(artifact-derived progress):

- **Session states**: `active` (live pid) → `recent` (<48 h) → `idle` →
  `stale` (> `--stale-days`, default 7).
- **Work states** (inbox): `blocked` (an open `handoff`-labeled bd issue, or a
  task whose bd status is neither open nor closed), `needs-review` (all tasks done but
  spec not archived; dirty repo with no live session; unpushed commits),
  `stale` (open tasks untouched past the threshold).

Severity order in the inbox: serious (blocked) before warning
(needs-review/stale), newest first within a tier. Every state renders as
glyph + word (`⚑ blocked`, `▲ needs-review`, `● active`) — color never
carries meaning alone. Palette is the toolkit's pre-validated reference set
(light and dark both selected, not auto-flipped); light-mode warning/serious
use darkened text-safe variants since they render as text, not fills.

## JSON schema (`--json`)

Top-level keys: `generated_at`, `stale_days`, `totals` (`repos`,
`specs_open`, `tasks_open`, `sessions_active`, `attention`), `inbox[]`
(`severity`, `state`, `repo`, `what`, `why`, `age_ts`, plus `cmd` — a
runnable shell command — on items with a one-command fix), `repos[]` (`path`,
`name`, `git`, `specs[]`, `handoffs[]`, `sessions[]`), `sessions[]`,
`orphan_sessions[]` (sessions whose cwd is outside every scanned repo),
`antigravity[]`, `todos[]`. Each `handoffs[]` record is one open
`handoff`-labeled bd issue: `id`, `title`, `tracked_ids` (the ids it
`tracks`), `updated_ts`. Each session record also carries `spawn_tree` —
the nested agent-spawn tree for that session (see `scan_session_spawns` under
Extending); `[]` for a session that spawned no sub-agents.

## Extending

New work sources follow the same shape: a `scan_*` function returning
records with a `last_touched`/`last_ts`, wired into `assemble()` and (if it
can demand a human decision) `attention_items()`. Keep every source
artifact-first — parse files on disk, never live transcripts or APIs — per
the labs' guidance collected in `docs/agent-dashboards.md`.

`scan_session_spawns(claude_home)` is an instance of this contract keyed to
sessions rather than repos: it returns `{session_id -> {spawn_tree,
last_touched, last_ts}}`, running `extract_agent_tree()` over each
`projects/<proj>/<sid>.jsonl` transcript. `assemble()` merges each
`spawn_tree` onto that session's existing record; because it is a separate
read-only scan, no other `scan_*()` function's output shape changes.
