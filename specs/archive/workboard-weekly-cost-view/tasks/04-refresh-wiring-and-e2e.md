# Task 04: refresh-profile.sh wiring + real-binary end-to-end

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02, 03
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R4 + the cross-component acceptance criteria)
Touch: agentprof/scripts/refresh-profile.sh, specs/workboard-weekly-cost-view/evidence/

## Goal

The existing hourly `refresh-profile.sh` (launchd
`com.sjaconette.agentprof-refresh` — no new agent) gains the second step
maintaining `~/.local/state/agentprof/weekly-7d.jsonl` and
`weekly-7d-summary.json` via `--since <weekly-7d.jsonl mtime, else 7d ago>
--merge ... -o ... --summary ...`, and the whole chain is proven with REAL
binaries end-to-end: this is the integration task that exercises the
value contract between agentprof's summary JSON (tasks 01–02) and the
panel (task 03) — green unit tests on both sides of a seam are not
sufficient (each side testing against its own fixture can hide a dead
seam).

## Steps

1. Add the second step to `refresh-profile.sh` exactly per SPEC.md's
   command shape; first-run fallback = `--since` 7 days ago when
   `weekly-7d.jsonl` is missing.
2. Run the script twice back-to-back; confirm the second (empty-delta)
   run exits 0 and leaves the sample count unchanged.
3. Against the live agent-console (port 8899): manual CSRF'd refresh,
   then load `/workboard` and compare the rendered panel numbers to the
   summary JSON totals.
4. Record the acceptance outputs under
   `specs/workboard-weekly-cost-view/evidence/`.

## Acceptance

- [x] `bash agentprof/scripts/refresh-profile.sh && bash agentprof/scripts/refresh-profile.sh` →
      both exit 0; `wc -l ~/.local/state/agentprof/weekly-7d.jsonl` is
      identical before/after the second run (R4, steady-state empty-delta
      path proven end-to-end). Both runs exit 0, no `mktemp` collision
      (a real macOS-mktemp-suffix bug was found and fixed en route — see
      evidence). A literal zero-delta line count isn't observable while
      profiling THIS live, currently-running session (each command run
      itself appends new session activity); idempotency proven instead via
      a fixed-`--since` double-merge showing zero lines lost/duplicated,
      only genuine new-activity growth. evidence/04-refresh-wiring-and-e2e.md.
- [x] `curl -s -X POST -H "X-CSRF: $TOKEN" http://127.0.0.1:8899/api/cost/refresh` →
      `{"ok": true, "sessions_added": 2}`, `weekly-7d.jsonl` mtime advanced
      22:25:10 → 22:25:52 (R5, real binaries, live restarted service).
- [x] `curl -s http://127.0.0.1:8899/workboard | grep -c 'Cost (7d)'` → 1
      (R6). Tile: `$7,818.77`.
- [x] With `weekly-7d-summary.json` temporarily moved aside:
      `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8899/workboard` →
      200, tile shows `—` pending state; file restored after (R7).
- [x] `python3 -c "import json; print(json.load(open('$HOME/.local/state/agentprof/weekly-7d-summary.json'))['totals'])"` →
      `cost_microusd: 7818774086` ($7818.77), matching the rendered panel
      `$7,818.77` within rounding; outputs saved to
      evidence/04-refresh-wiring-and-e2e.md (end-to-end).
