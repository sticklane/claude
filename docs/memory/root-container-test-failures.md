# Root-container test failures — pre-existing, not your diff

When to read: running the suite (`scripts/check.sh` or `tests/test_*.sh`)
in a fresh remote/container session (Claude Code on the web, CI-as-root)
and seeing failures unrelated to your change.

## The gotcha (PATH-based — what a fresh root container hits first)

`bd` is installed via `go install`, which drops the binary in
`/root/go/bin`. That directory is NOT on `PATH` by default in a fresh root
container, so anything that shells out to `bd` — `scripts/check.sh` and any
test that invokes the tracker — fails to find it until PATH is exported.
The bd-gated pytest tests (`tests/test_agentic_*.py`) `skipif bd.bd_which()
is None`, so they SKIP rather than fail; the visible breakage is the
missing-command errors from the scripts and shell paths that assume `bd` is
resolvable.

## What to do

- Export PATH before running the suite:
  `export PATH=$PATH:/root/go/bin` (the reason `scripts/check.sh` needs the
  export in these sessions). Re-run; the bd-dependent paths resolve.
- Confirm any remaining failure is environmental with the clean-HEAD test:
  `git stash`, re-run; if it fails on a clean `main` too, it is
  environmental — say so in your report and move on.
- Do not "fix" your diff to make an environmental failure pass.

## Also seen: chmod-based shell-test failures under root (history)

Previously this entry named the root-container set as three shell tests —
`test_hook_templates.sh`, `test_install_gates.sh`, and
`test_workboard_render.sh` — failing when run as root. At least one
assertion class ("unreadable check.sh warns with one stderr line") relies on
`chmod 0` making a file unreadable, but root ignores file modes, so the
guarded branch never fires and the expected warning never appears. These
pass for non-root users (the intended environment), so do not delete or
weaken the assertions. Real fix if ever prioritized: skip (or invert)
permission-based assertions when `id -u` is 0. Verified this way on
2026-07-04.
