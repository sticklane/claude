# Three shell tests fail in root containers — pre-existing, not your diff

When to read: running `tests/test_*.sh` in a remote/container session
(Claude Code on the web, CI-as-root) and seeing failures unrelated to
your change.

## The gotcha

`test_hook_templates.sh`, `test_install_gates.sh`, and
`test_workboard_render.sh` fail when run as root — including on a clean
`main` checkout. At least one assertion class ("unreadable check.sh
warns with one stderr line") relies on `chmod 0` making a file
unreadable, but root ignores file modes, so the guarded branch never
fires and the expected warning never appears.

## What to do

- Confirm with the clean-HEAD test: `git stash`, re-run the three tests;
  if they fail there too, they are environmental — say so in your report
  and move on. Verified this way on 2026-07-04.
- Do not "fix" your diff to make them pass, and do not delete/weaken the
  assertions — they pass for non-root users, which is the intended
  environment.
- Real fix if ever prioritized: skip (or invert) permission-based
  assertions when `id -u` is 0.
