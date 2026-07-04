# workboard reference — data sources and state model

Loaded on demand. The scanner (`workboard.py`) is the source of truth; this
documents what it reads and why, so a debugging session doesn't have to
reverse-engineer it.

## Data sources (all read-only)

One deliberate write exists: `--abandon <conv-id>` / `--abandon-stale` drop
a `.workboard-abandoned` marker file into an Antigravity conversation dir so
the scanner skips it permanently. Antigravity's own artifacts (`task.md`,
metadata) are never modified; undo = delete the marker. Tests:
`python3 -m unittest discover -s .claude/skills/workboard`.

| Source | Path | What it yields |
|---|---|---|
| Toolkit specs | `<repo>/specs/<slug>/SPEC.md` + `tasks/*.md` | spec title; per-task `Status:` line (`pending`/`in-progress`/`claimed` open; `done`/`deferred`/`skipped` closed; anything else = blocked-ish and flagged) |
| Kiro specs | `<repo>/.kiro/specs/<name>/tasks.md` | checkbox states — `[ ]` todo, `[-]` doing, `[x]` done; phase = which of requirements/design/tasks files exist |
| Handoffs | `HANDOFF.md` (repo root, `.claude/`, `specs/*/`, ≤2 dirs deep) | parked work waiting on a human — always an inbox item |
| Batons | `DRAIN-BATON.md` (repo root, `specs/*/`) | a parked drain generation to relaunch — generation number, relaunch command, and any needs-attention/deferred section; a repo card, NOT the handoff's resume-then-delete prompt (drain self-manages the file) |
| Sessions | `~/.claude/projects/<escaped-cwd>/<sessionId>.jsonl` | first user prompt (head read), `cwd`, `gitBranch`, last-record timestamp (64 KB tail read — transcripts are never read wholesale) |
| Live sessions | `~/.claude/sessions/<pid>.json` | sessionId → pid; `active` iff the pid is alive (`kill -0`) |
| Todos | `~/.claude/todos/*.json` (when the install has them) | open in-session todo lists |
| Antigravity | `~/.gemini/antigravity*/brain/<conversation>/` | `task.md` checkbox counts + `task.md.metadata.json` summary/updatedAt; conversations containing a `.workboard-abandoned` marker are skipped |
| Git | `git -C <repo> …` | branch, dirty count, ahead/behind upstream, worktrees, last-commit time |

`CLAUDE_CONFIG_DIR` overrides `~/.claude`. Repo discovery: walk the given
roots (depth ≤ `--max-depth`, pruning `node_modules`, venvs, dot-dirs), plus
`git rev-parse --show-toplevel` of every session `cwd` — so a repo you only
ever touched via Claude Code still appears.

## State model

Two axes, following Antigravity (decision-oriented status) and Kiro
(artifact-derived progress):

- **Session states**: `active` (live pid) → `recent` (<48 h) → `idle` →
  `stale` (> `--stale-days`, default 7).
- **Work states** (inbox): `blocked` (handoff parked, or a task whose
  `Status:` is neither open nor closed), `needs-review` (all tasks done but
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
`name`, `git`, `specs[]`, `handoffs[]`, `batons[]`, `sessions[]`), `sessions[]`,
`orphan_sessions[]` (sessions whose cwd is outside every scanned repo),
`antigravity[]`, `todos[]`.

## Extending

New work sources follow the same shape: a `scan_*` function returning
records with a `last_touched`/`last_ts`, wired into `assemble()` and (if it
can demand a human decision) `attention_items()`. Keep every source
artifact-first — parse files on disk, never live transcripts or APIs — per
the labs' guidance collected in `docs/agent-dashboards.md`.
