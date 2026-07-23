# `agentic init` fails opaquely on a stale committed `sync.remote`

`agentic init` (`agentic/initialize.py`) wraps `bd init` to undo its
auto-commit side effect (already documented in
`specs/agentic-core-redesign/SPEC.md`'s "Ops facts" and mechanized in
`agentic/bd.py`'s `bd_init()`). That wrapper calls `bd init
--non-interactive` with no `--remote` override. If the repo's
committed `.beads/config.yaml` carries a `sync.remote` pointing at a
host unreachable from the current machine — observed case: a
session/container-local proxy address
(`git+http://local_proxy@127.0.0.1:<port>/...`) baked in by a prior
run on different infrastructure — `bd init`/`bd bootstrap` tries to
clone from it and fails with an opaque connection error rather than
falling back to a fresh local-only database.

**Workaround (until `agentic/bd.py`'s `bd_init()` passes an explicit
override itself):** run `bd init --prefix <name> --non-interactive
--remote "" --skip-agents` directly instead of `agentic init` when this
happens — `--remote ""` forces a local-only database ignoring the
config value; `--skip-agents` skips the AGENTS.md/CLAUDE.md/Codex-hook
provisioning step so it doesn't also duplicate content into those
files (see the "Ops facts" section above for why that provisioning is
risky to run unattended). Curate the AGENTS.md/CLAUDE.md snippet by
hand afterward if the repo needs it.

**Worth fixing at the source:** `bd_init()` could pass `--remote ""`
itself (or catch this specific connection failure and retry with it)
so `agentic init` doesn't need this manual escape hatch. Flagged, not
yet filed as a task.

When to read: `agentic init` fails with a "Failed to connect" / "Couldn't
connect to server" error, or you're bootstrapping bd fresh in a repo
whose `.beads/` state was committed from a different machine or
container.
