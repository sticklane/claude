# Task 04: agent-console.py dispatch-resume-handoff consumes bd-native handoff data

Status: pending
Depends on: 03
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements R6, R7)
Touch: agent-console/agent-console.py, agent-console/tests/test_dispatch_kinds.py, agent-console/tests/test_drilldown_registry.py, agent-console/tests/test_parsers.py

## Goal

`agent-console.py`'s `dispatch-resume-handoff` action and every other
consumer of `repo["handoffs"]` use task 03's new bd-issue-shaped fields
instead of the retired `path`/`title`/`mtime` shape. The dispatched
action still ultimately triggers `/resume-handoff`.

## Touch

Task 03 must be `done` first — `agent-console.py` dynamically loads
`workboard.py` as a module
(`workboard = _load_module("workboard", SKILLS_ROOT / "workboard" /
"workboard.py")`, confirmed this session) and consumes its `assemble()`/
`attention_items()`/`ready_items()` output directly, which includes
`scan_handoffs()`'s output shape. Do not start this task until task 03's
`scan_handoffs()` and `scanner_resume_prompt()` have actually landed —
read their final field names from the real committed code, not from this
task file's guesses.

## Steps

1. Confirm task 03 is done: `grep -c "HANDOFF" .claude/skills/workboard/
   workboard.py` → 0. If not 0, stop and report blocked rather than
   guessing at field names.
2. Read task 03's final `scan_handoffs()` return shape directly from the
   committed `workboard.py`, and read `scanner_resume_prompt`'s new
   signature/output.
3. Find every `repo["handoffs"]` / `repo.get("handoffs")` /
   `h["path"]`-on-a-handoff-record site in `agent-console.py`
   (`grep -n "handoffs\b" agent-console/agent-console.py` — this session's
   scout found sites around lines 827-836, 979, 1115, 1180-1242,
   2541-2599, 2770, 2909; treat those as a starting map, not a guarantee
   nothing else references it, since line numbers shift). Update each to
   read the new field names. The `dispatch-resume-handoff` action's argv
   construction (~1237-1242, 2541-2599) is the one that most directly
   needs the new identifier (a bd issue id) instead of a file path — it's
   what actually gets passed to whatever invokes `/resume-handoff`.
4. Update the three test files' fixtures/mocks accordingly:
   `tests/test_dispatch_kinds.py`'s `TestResumeHandoffGeneration` (builds
   a fake `repo["handoffs"]` entry and asserts the generated dispatch
   argv), `tests/test_drilldown_registry.py` (integration coverage of
   `scan_handoffs()` via the registry), `tests/test_parsers.py` (parses a
   `handoffs[]` field from repo JSON — update the shape it parses).

## Acceptance

- [ ] `grep -c "HANDOFF" agent-console/agent-console.py` → 0
- [ ] `cd agent-console && python3 -m pytest tests/test_dispatch_kinds.py -k ResumeHandoff -q` → pass, exit 0
- [ ] `cd agent-console && python3 -m pytest tests/test_drilldown_registry.py tests/test_parsers.py -q` → pass, exit 0 (run separately from the `-k` command above — a combined `-k ResumeHandoff` filter across all three files collects only 2 of ~40+ tests, verified 2026-07-24 during this spec's critique)
- [ ] **Non-vacuous forcing check (verified 2026-07-24 during breakdown: all
      three checks above pass on the UNCHANGED tree today — this repo's
      agent-console tests use hand-built fixtures fully decoupled from
      workboard's real output, e.g. `test_drilldown_registry.py:81` and
      `test_parsers.py:182` both hard-code `{"title": "H", "path":
      "HANDOFF.md", "mtime": 5.0}`, so none of the above actually proves
      task 03's field-shape change was consumed).** Add a new test
      (in whichever of the three test files best fits — likely
      `test_dispatch_kinds.py`) that constructs a handoff record using
      ONLY task 03's actually-committed field names (no `path` or `mtime`
      keys at all — read them from the real landed `workboard.py`, not
      this task file), feeds it through `dispatch-resume-handoff`'s argv
      construction, and asserts a valid, non-crashing argv results.
      `grep -c 'h\["path"\]\|h\.get("path")\|\["mtime"\]' agent-console/agent-console.py`
      → 0 (today: not yet measured, but must go to 0 once task 03's
      shape lands — the retired field names must not still be read
      anywhere in this file).
