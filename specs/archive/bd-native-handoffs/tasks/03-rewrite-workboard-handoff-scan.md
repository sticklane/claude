# Task 03: workboard.py scans bd for open handoff issues instead of HANDOFF*.md

Status: done
Depends on: none
Priority: P1
Budget: 35 turns
Spec: ../SPEC.md (requirements R5, R7)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/reference.md, .claude/skills/workboard/test_workboard.py

## Goal

`workboard.py`'s handoff-scanning path is bd-native: `scan_handoffs()`
queries `bd list --label handoff --status=open --json` per scanned repo
instead of globbing `HANDOFF*.md`, and every downstream consumer of its
output (`scanner_resume_prompt`, `attention_items`) uses the new
bd-issue-shaped fields. `reference.md`'s documented schema matches.

## Touch

Do not touch `agent-console/` — task 04 (depends on this task) owns it.
This task's new output shape for a handoff record is the contract task 04
consumes; pick concrete field names now (e.g. `id`, `title`,
`tracked_ids`, `mtime`) and use them consistently, since task 04 will read
them from this task's actual landed code, not guess.

## Steps

1. Read `.claude/skills/workboard/workboard.py`'s current handoff-related
   code exactly (verified structurally this session — no need to re-read the
   whole 2000+-line file):
   - `scan_handoffs(repo)` at line ~598: globs `HANDOFF*.md`, returns
     `[{"path": ..., "title": ..., "mtime": ...}, ...]`.
   - `scanner_resume_prompt(path)`: builds the string `"Resume the parked
     handoff in {path}; delete the file once fully resumed"` — this is a
     **pinned string a test asserts on exactly**
     (`TestScannerPromptBuilders.test_resume_prompt_builder_is_pinned`)
     and must change to bd-native wording (e.g. naming the issue id and
     `bd close`, not "delete the file").
   - `attention_items()` (called from `assemble()`) builds each inbox
     item's `cmd` field from `scanner_resume_prompt(h["path"])` for each
     entry in `repo["handoffs"]` — update the field name it reads to
     match whatever `scan_handoffs()` now returns.
2. Rewrite `scan_handoffs(repo)`: check `(repo / ".beads").is_dir()`
   first — return `[]` immediately if absent, no `bd` subprocess call.
   Otherwise run `bd -C <repo> list --label handoff --status=open --json`
   with a bounded timeout (e.g. `subprocess.run(..., timeout=5)`); catch
   `subprocess.TimeoutExpired`, non-zero exit, and JSON decode errors —
   any of these means "no handoffs for this repo," never an exception
   that aborts the whole workboard scan. Map each returned bd issue to a
   dict with the same intent as today's fields: an id, a title, and
   (for downstream display) whatever's cheapest to surface — do not
   fetch full comment bodies per issue during a workboard scan, that's
   `/resume-handoff`'s job, not a dashboard listing's.
3. Rewrite `scanner_resume_prompt` to reference the bd issue id and
   `/resume-handoff` (or `bd close`), not a file path or "delete the
   file."
4. Update every call site reading `repo["handoffs"][i]["path"]` (used by
   `attention_items` and every other bounded reference search for
   `scan_handoffs` or
   for `handoffs\[` surfaces) to read the new field names instead.
5. Update `.claude/skills/workboard/reference.md`'s documented
   `handoffs[]` schema (lines ~19, 38, 56 per this session's scout) to
   match the new field names.
6. Rewrite `test_workboard.py`'s handoff-related tests: `TestScanHandoffs`
   (currently builds a temp dir with `HANDOFF*.md` files — rewrite to a
   temp `.beads/` + a real `bd create --labels handoff` issue, or a bd
   subprocess mock, whichever proves less flaky), `TestScannerPromptBuilders`'s
   two pinned-string tests (update the expected strings to the new
   wording), `test_parked_handoff_item_carries_resume_command` and
   `test_resume_inbox_cmd_embeds_the_builder_output` (both currently
   build `repo["handoffs"] = [{"path": ..., "title": ..., "mtime": ...}]`
   by hand — update to the new field shape).

## Acceptance

- [x] `grep -c "HANDOFF" .claude/skills/workboard/workboard.py` → 0
- [x] `grep -c "bd list --label handoff\|--label.*handoff" .claude/skills/workboard/workboard.py` → 1
- [x] `cd .claude/skills/workboard && python3 -m pytest test_workboard.py -q` → 104 passed, 5 subtests passed, exit 0
- [x] `TestScanHandoffs` covers all three: `test_repo_without_beads_dir_yields_nothing_and_never_runs_bd` (patched `subprocess.run` raises if called), `test_bd_exceptions_yield_no_handoffs_instead_of_raising` (TimeoutExpired, OSError), `test_bd_bad_output_yields_no_handoffs_instead_of_raising` (non-zero exit, malformed JSON, non-list JSON).

## Decisions

- Handoff-record timestamp field named `updated_ts`, not the task's example
  `mtime` — a bd issue has no file mtime, and the value is the issue's
  `updated_at`. Reverse by renaming the key in `scan_handoffs`,
  `attention_items`'s `age_ts`, and the tests.
- Record shape is `{id, title, tracked_ids, updated_ts}`; `tracked_ids` reads
  the issue's `tracks`-typed dependency edges. This is task 04's contract.
