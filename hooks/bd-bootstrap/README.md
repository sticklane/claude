# bd-bootstrap (SessionStart hook)

`ensure-bd.sh` makes the bd (beads) tracker usable before priming it, then
`exec`s `bd prime --hook-json`. It is a drop-in replacement for the bare
`bd prime --hook-json` SessionStart entry in `.claude/settings.json` —
**not wired in by default**; swapping the entry (with a `"timeout": 300`)
is a one-line settings change left to the repo owner.

## Why it exists

The bare wiring silently no-ops on any machine without the `bd` binary or a
hydrated database: every fresh cloud container ran outside the tracker while
CLAUDE.md named bd the source of truth, and the `bd-compliance` Stop hook —
correctly — skips when bd is missing rather than brick the repo. The result
was structural: remote sessions could not follow the tracking doctrine and
never learned they weren't. This hook is the programmatic close for that gap
(specs/... — filed as the skills-beads-tracking-gaps work).

## What it does, in order

1. Repo has no `.beads/` → silent exit 0.
2. bd off PATH but in a known install dir (`/root/go/bin`, `~/go/bin`,
   `~/.local/bin`, `/usr/local/bin`) → use it, and symlink into
   `/usr/local/bin` when writable so the session's later Bash calls resolve
   it.
3. bd missing entirely → start the documented installer (the same command
   `.beads/README.md` gives) detached in the background, once per container
   (marker under `$TMPDIR`), and print ONE advisory line so the session
   knows it is outside the tracker. `BD_BOOTSTRAP_NO_INSTALL=1` suppresses
   the attempt.
4. bd present but no database, committed `.beads/issues.jsonl` present →
   hydrate: `bd init --prefix <metadata.json's dolt_database>` +
   `bd import`.
5. `exec bd prime --hook-json`.

Output discipline: silent apart from `bd prime`'s own output when everything
is in place; exactly one line when the tracker is genuinely unavailable —
per `token-discipline.md`'s hook cost rule (fires on time-varying state
only).

## Env knobs (used by tests)

- `BD_BOOTSTRAP_NO_INSTALL=1` — never attempt an install.
- `BD_BOOTSTRAP_EXTRA_DIRS` — colon-separated install dirs to probe
  (defaults to the known set above).
- `BD_BOOTSTRAP_LINK_DIR` — where the off-PATH symlink goes (defaults to
  `/usr/local/bin`; tests point it at a temp dir).

## Tests

`bash hooks/bd-bootstrap/test.sh` — hermetic: stub `bd` on a temp PATH,
temp project trees, no network, never touches the real `.beads/`.
