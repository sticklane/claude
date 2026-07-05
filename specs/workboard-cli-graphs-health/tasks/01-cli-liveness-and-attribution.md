# Task 01: CLI-sourced session liveness + realpath attribution (R1, R2)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2; Solution A; R5 invariant)
Touch: /Users/sjaconette/claude/.claude/skills/workboard/workboard.py, /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py

## Goal

`live_session_ids()` builds its liveness map from `claude agents --json` (parsing `pid`, `sessionId`, `status`), falling back to the existing PID-record + `pid_alive()` scan when `claude` is absent from PATH or returns a non-list, and returns the 2-tuple `(live, liveness_unknown)` pinned in SPEC.md Solution A — `live` keeps today's `{sid: {...}}` shape in both paths; `liveness_unknown` is True when the source is present and non-empty but yields zero live ids (consumed later by task 03). `scan_sessions` unpacks the tuple and plumbs `liveness_unknown` through. `assemble()`'s attach-sessions list-comprehension applies `os.path.realpath` to both the session cwd and the repo root before matching (R2).

## Touch

Only the two workboard skill files. Do NOT touch `_spec_dag_tasks`/`_spec_dag_html` (task 02's territory), the marker rendering/TEMPLATE (task 03's), `.claude/skills/_shared/viz.py`, or `antigravity/` (task 04 mirrors at the end). Port the *algorithm* from `~/agent-console/agent-console.py` (`live_sessions_from_cli` / `_live_sessions_from_pids`) — do not copy verbatim, and do not edit that repo.

## Steps

1. Write the failing tests first: (a) monkeypatch the `claude agents --json` shim to return a valid list → liveness from CLI; (b) raise/return None → liveness from PID records; both return the 2-tuple whose first element has the same `{sid: …}` map shape. (c) A session whose `cwd` is a symlink into a repo attributes to that repo via `assemble()`'s attach-sessions loop (SPEC.md R2 notes `TestActiveCoverageReclassification` does NOT cover this loop). (d) `liveness_unknown` is True for a non-empty source yielding zero live ids, False otherwise.
2. Rewrite `live_session_ids()` per SPEC.md Solution A: CLI primary, PID-scan fallback, 2-tuple return. Liveness predicate, pinned: every CLI record carrying a `sessionId` and a `pid` counts as live regardless of its `status` string (matches agent-console's behavior); do not filter on status values. Session *rows* keep rendering from the `.jsonl` transcript via `_first_prompt_and_meta`; CLI `cwd`/`name` are NOT used for row content.
3. Update `scan_sessions` (the only consumer) to unpack the tuple; keep `if sid in live` membership semantics; carry `liveness_unknown` outward (a return field or module-level plumbing that task 03 can render from — pick the smallest shape, it only needs to reach `assemble`).
4. Apply `os.path.realpath` to both sides of the attach-sessions comparison in `assemble()`.
5. Re-run the full suite including `TestActiveCoverageReclassification` (shares the session code path; must not regress) and the merged shared-viz suites.

## Acceptance

- [ ] `python3 -m pytest /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py -q` → all pass, including new R1 tests (CLI parse + PID fallback + 2-tuple shape + liveness_unknown) and the new R2 symlink-attribution test, with `TestActiveCoverageReclassification`, `TestSessionStartTs`, `TestSessionTimelineRendering`, `TestSpecDagRendering` unregressed
- [ ] `grep -nE '\.write_text|\.write\(|\bopen\([^)]*[\x27"][wax]' /Users/sjaconette/claude/.claude/skills/workboard/workboard.py` → still only the three known write sites (HTML + actions-script writes in `main()`, abandon marker in `abandon_conversations()`) — R5: no new writes
- [ ] `python3 /Users/sjaconette/claude/.claude/skills/workboard/workboard.py --out /tmp/wb-task01.html` → exits 0 and every HTML-active sid appears in `claude agents --json` (subset check, NOT set-equality — CLI-live sessions without a transcript under `~/.claude/projects` legitimately have no HTML row)
