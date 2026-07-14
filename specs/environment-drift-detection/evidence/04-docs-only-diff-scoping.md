# Verification: 04-docs-only-diff-scoping

Verdict: PASS

## Criterion 1 — literal phrase present

Command: `grep -c "docs-only diff" templates/stop-gate.sh bin/install-gates | awk -F: '{sum+=$2} END {print sum}'`
Output: `2` (> 0). Both occurrences are in `templates/stop-gate.sh` (comment block +
warn message); `bin/install-gates` was intentionally left untouched, consistent
with the task's "leave bin/install-gates untouched" fallback since it installs
`stop-gate.sh` verbatim.

## Criterion 2 — test_hook_templates.sh

Command: `bash tests/test_hook_templates.sh`
Output: `pass: 85, fail: 0` — exit 0.
Confirmed new cases present (diff vs base 16c2ed1, lines added to
tests/test_hook_templates.sh):

- "stop-gate: docs-only diff scoping (R4)" section
- clean-tree-not-docs-only case (`check.sh runs on a clean tree (not skipped as docs-only)`)
- docs-only `.md` diff → skip case (`check.sh NOT run for docs-only (.md) diff`)
- `docs/` subtree-only diff → skip case
- mixed docs+non-docs diff → full check still runs (`check.sh DID run when a non-docs file changed`) — the anti-regression case

## Criterion 3 — test_install_gates.sh (no regression)

Command: `bash tests/test_install_gates.sh`
Output: `pass: 168 fail: 0` — exit 0.

## MANUAL criterion A — docs-only edit skips full check

Setup: scratch git repo (`pyproject.toml`, python stack) at
`/private/tmp/.../scratchpad/manual-gate-repo`, gates installed via
`bin/install-gates <repo>`, `scripts/check.sh` instrumented to `touch
check-ran.marker` before running its stages, clean baseline committed
(including installed `.claude/hooks/stop-gate.sh`).

Trigger: appended a line to `HUMAN.md` (docs-only diff, uncommitted), then
fed `{"stop_hook_active": false, "cwd": "<repo>"}` on stdin to the
_installed_ `.claude/hooks/stop-gate.sh`.

Observed:

```
stop-gate: docs-only diff since last commit; skipping check
hook exit: 0
MARKER ABSENT (check.sh skipped)
```

PASS — full check.sh was skipped for the docs-only diff.

## MANUAL criterion B — product-code edit still runs full check

Trigger (same repo, reset to clean baseline): added `app.py` with `x = 1`
(untracked non-docs file), fed the same hook JSON to the installed
stop-gate.sh.

Observed:

```
hook exit: 0
MARKER PRESENT (check.sh ran)
```

PASS — check.sh ran in full (marker created) for the non-docs-only diff.

## Scope / Touch-list check

`git diff 16c2ed1 --stat`:

```
 templates/stop-gate.sh       | 32 +++++++++++++++++++++++++
 tests/test_hook_templates.sh | 57 ++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 89 insertions(+)
```

Only `templates/stop-gate.sh` and `tests/test_hook_templates.sh` touched —
both within the task's Touch list (`templates/stop-gate.sh, bin/install-gates,
tests/test_hook_templates.sh, tests/test_install_gates.sh`). `bin/install-gates`
and `tests/test_install_gates.sh` were NOT modified — allowed per the task
Steps ("otherwise leave bin/install-gates untouched"). Confirmed
`templates/check.sh.tmpl` was NOT touched (absent from the diff stat), matching
the task's explicit prohibition.

## Append-only task-file check

`git diff 16c2ed1 -- 'specs/environment-drift-detection/tasks/*.md'` produced
NO output — no task file (including this one) was modified relative to base.
This means the task file's `Status:` line still reads `in-progress` (not
flipped to `done`/`review`), i.e. the implementer did not mark the task
complete despite the code/tests being in place and green. Not a FAIL by
itself (append-only check trivially passes — nothing to flag as
out-of-bounds), but noted as a process gap: the task's Status and checkbox
ticks were never updated to reflect the finished work.

## Gates

No repo-wide `scripts/check.sh` run beyond the two acceptance test scripts
above (this repo's canonical checks per task instructions are the two test
files; both green).

## Findings

- Task file Status left at `in-progress` with acceptance checkboxes
  unchecked, even though all automated and manual criteria pass. Not a
  content violation of the append-only rule (no diff exists at all), but the
  task was not marked done.
- No scope creep detected — diff strictly limited to `templates/stop-gate.sh`
  and `tests/test_hook_templates.sh`.
