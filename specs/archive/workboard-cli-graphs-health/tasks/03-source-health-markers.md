# Task 03: Source-health markers (R4)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R4; Solution C; R-note; R5 invariant)
Touch: /Users/sjaconette/claude/.claude/skills/workboard/workboard.py, /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py

## Goal

Sources that are present but yield zero parseable records show a visible "source check" marker instead of rendering silently empty. Spec-task side: `scan_toolkit_specs` counts a task file as unparseable **iff its filename lacks the leading `NN-` numeric prefix that `_TASK_NUM_RE` needs** (SPEC.md's pinned definition — today it appends a defaulted row for every file; tighten it to count exactly this case, no other rejection criterion), and a spec whose `tasks/` files are all unparseable gets the marker on its card. Liveness side: when task 01's `liveness_unknown` is True, the sessions area is marked "liveness unknown" (never "no sessions") — adjacent to the `viz.timeline()` render (e.g. beside the section heading), never inside the `.viz-bar` rows, in both the repo-card Sessions column and the "Sessions outside scanned repos" section.

## Touch

Only the two workboard skill files. Do NOT change `live_session_ids`'s R1 contract (its `liveness_unknown` bool already exists from task 01 — this task renders it), the DAG plumbing from task 02, `.claude/skills/_shared/viz.py`, or `antigravity/` (task 04). You MAY edit `assemble`/`render_html`/TEMPLATE placeholders as needed to thread `liveness_unknown` and the unparseable count from where task 01 left them (task 01 only guarantees the flag reaches `assemble`) out to the rendered HTML — that threading is this task's work, not a Touch violation. Per SPEC.md's R-note: marker HTML passed as a `.format` argument is brace-safe; prefer existing classes (`chip warning`, `muted-text`) or inline `style=` over adding TEMPLATE CSS (literal TEMPLATE CSS needs doubled braces).

## Steps

1. Write the failing tests first: (a) a spec fixture whose `tasks/` files all lack the `NN-` prefix yields the "source check" marker for that spec, not an empty task section; (b) a fixture with a mix parses the prefixed ones and counts the rest; (c) `liveness_unknown=True` renders the "liveness unknown" marker adjacent to the timeline (assert marker present AND `.viz-bar` rows unaffected); (d) `liveness_unknown=False` renders no marker.
2. Tighten `scan_toolkit_specs` to count unparseable files per the pinned definition; carry the count on the spec dict.
3. Render the spec-card marker when the count > 0 and the liveness marker from the plumbed `liveness_unknown`, following the R-note placement rules.
4. Re-run the full suite; transcript-sourced session rows and spec rows must be unaffected when sources are healthy.

## Acceptance

- [x] `python3 -m pytest /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py -q` → all pass, including the new R4 tests, with all pre-existing suites unregressed — verifier confirmed: 57 passed, new tests assert real structural content, not tautological.
- [x] `grep -nE '\.write_text|\.write\(|\bopen\([^)]*[\x27"][wax]' /Users/sjaconette/claude/.claude/skills/workboard/workboard.py` → still only the three known write sites — R5: no new writes — verifier confirmed: exactly 3 hits (abandon marker, actions_path, out.write_text render_html).
- [x] `python3 /Users/sjaconette/claude/.claude/skills/workboard/workboard.py --out /tmp/wb-task03.html` → exits 0; healthy sources on this machine render NO "source check" / "liveness unknown" markers (grep the HTML for the marker text → absent) — verifier confirmed: exit 0, both marker strings absent.
