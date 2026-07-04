# Task 02: Companion actions script + HTML link

Status: done
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R4, R5; cross-cutting R8, R9)
Touch: .claude/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/workboard.py, .claude-plugin/plugin.json, tests/test_workboard_actionability.sh, tests/fixtures/workboard-actionability/

## Goal
`workboard.py` writes an executable companion actions script alongside
`--out` (default: `--out` stem + `.actions.sh`; `--actions-out <path>`
override) containing only safe, mechanical batch fixes — repo pushes and
verifier invocations — in labeled independently-runnable sections, and the
HTML surfaces the script path plus its `bash <path>` run command. The test
file (created in task 01) gains R4/R5 assertions and a `bash -n` validity
check. Mirrored to antigravity in the same commit with a `version` bump.

## Touch
Extend `tests/test_workboard_actionability.sh` and add any fixtures needed
(a repo with unpushed-ahead commits; an all-done unarchived toolkit spec
with `tasks_total > 0`; a `.kiro/specs/<slug>` done-spec to prove exclusion)
— do NOT rewrite task 01's existing assertions. Do NOT touch inbox grouping
or filter tiles (task 03). The script generation is new code; reuse the
board's existing unpushed-ahead detection and done-spec detection (:527)
rather than reimplementing scans.

## Steps
1. **RED** — extend the test: assert the actions script contains a
   `git -C <repo> push` line for the unpushed fixture repo; a
   `claude "Use the verifier agent to verify specs/<slug> ..."` line
   (preceded by `cd <abs-repo>`) for the all-done toolkit fixture spec; and
   that the Kiro fixture done-spec produces NO verify line. Assert the script
   contains NO `git mv`, NO `push --force`/`-f`, NO `rm`, NO `/build`/`/drain`.
   Assert the HTML contains the script path and the `bash <path>` invocation
   rendered inside a `<td><code>`. Add a top-level acceptance that
   `bash -n <actions-script>` exits 0. Run; confirm it fails for the right
   reason.
2. **GREEN (R4)** — emit the script: resolve its path from `--actions-out`
   or the `--out` stem + `.actions.sh`; write `#!/usr/bin/env bash`, `set -u`,
   and an echoed one-line "review before running" banner. Up to two
   `# === <label> ===` sections, each line independently runnable:
   - **Pushes** — `git -C <abs-repo> push` per repo the board found with
     unpushed-ahead commits (mirror the needs-review push cmd).
   - **Verify done specs** — `cd <abs-repo>` then
     `claude "Use the verifier agent to verify specs/<slug> against its
     acceptance criteria"` per all-tasks-done unarchived **toolkit** spec
     with `tasks_total > 0`; exclude `.kiro/specs/<slug>` done-specs even
     though inbox done-spec detection (:527) fires for them.
   Never emit `git mv`/archive moves, `push --force`/`-f`, `rm`, or any
   `/build`//`/drain` launch. Both sections empty ⇒ still write the file with
   header + `# no batch actions available`. `chmod +x` the file.
3. **GREEN (R5)** — in the HTML near the top, show the actions-script path
   and the exact `bash <path>` invocation, the invocation inside a
   `<td><code>` so the existing `closest('td code')` copy handler
   (workboard.py:902) applies. One line stating pushes run immediately and
   verify lines launch review sessions.
4. **Mirror + bump (R9)** — port to the antigravity workboard in the same
   commit (port equivalently if diverged, note in commit message); bump
   `plugin.json` `version`.

## Acceptance
- [x] `bash tests/test_workboard_actionability.sh` → passes (R1–R5) — verifier: `PASS: workboard actionability (R1-R5 subset)`, exit 0 (evidence/02-actions-script-and-link.md)
- [x] `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html --actions-out /tmp/wb.actions.sh` → exits 0, then `bash -n /tmp/wb.actions.sh` → exits 0 and `test -x /tmp/wb.actions.sh` succeeds (R4, R8) — verifier: all three exit 0 (evidence/02-actions-script-and-link.md)
- [x] `grep -Eq 'git mv|push (--force|-f)|(^|[^[:alnum:]])rm |/build|/drain' /tmp/wb.actions.sh` → NO match (exit 1) (R4) — verifier: exit 1, no unsafe commands (evidence/02-actions-script-and-link.md)
- [x] `/tmp/wb.html` contains the actions-script path and a `<td><code>...bash ...</code>` run invocation (R5) — verifier: `<td><code class="cmd">bash …</code></td>`, `td code` copy handler applies (evidence/02-actions-script-and-link.md)
- [x] `python3 -c "import ast; ast.parse(open('antigravity/.agents/skills/workboard/workboard.py').read())"` → exits 0, and the commit touches both workboard paths + `plugin.json` (R9) — verifier: ast ok, mirror byte-identical, plugin.json 0.7.9→0.7.10 (evidence/02-actions-script-and-link.md)
