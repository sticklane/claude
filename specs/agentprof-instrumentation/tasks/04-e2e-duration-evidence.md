# Task 04: End-to-end duration evidence from a real /drain run

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02, 03
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md (final acceptance criterion, manual-pending)
Touch: specs/agentprof-instrumentation/evidence/

## Goal

Recorded evidence exists that the whole chain works on real data: a real
`/drain` (or `/build`) session run AFTER tasks 01–03 landed, profiled with
agentprof, shows at least one `tool:` frame with non-zero cumulative
`duration_ms` in `go tool pprof -top` output. This is the spec's explicitly
manual-pending criterion — marker EMISSION is a runtime prompt-following
question no deterministic test can force (SPEC.md, Out of scope, last item;
docs/memory/unattended-worker-tool-limits.md).

## Touch

Writes only the evidence file. No source, skill, or mirror changes — if the
profile looks wrong, file a follow-up task instead of patching here.

## Steps

1. Confirm a real `/drain` or `/build` session has run since task 03
   landed (`/drain` is human-launched — do NOT launch one; wait for one to
   have happened naturally, or ask the human to run one).
2. `cd agentprof && go run . claude --days 1 -o /tmp/agentprof-e2e.pb.gz`
   (or the installed `agentprof claude --days 1 -o ...`).
3. `go tool pprof -top -sample_index=duration_ms /tmp/agentprof-e2e.pb.gz`
   — capture the text output.
4. Save the `-top` text (and, if markers were emitted in that session, a
   `-top` slice showing `stage:`/`role:` frames) to
   `specs/agentprof-instrumentation/evidence/e2e-duration-top.txt` with a
   dated header naming the profiled session.

## Acceptance

- [x] `test -s specs/agentprof-instrumentation/evidence/e2e-duration-top.txt`
      → file exists and is non-empty. Verified 2026-07-08.
- [x] `grep -c 'tool:' specs/agentprof-instrumentation/evidence/e2e-duration-top.txt`
      → 14 (6 distinct tool: frames, each with non-zero cumulative duration —
      e.g. `tool:Bash` 731.90s, `tool:AskUserQuestion` 92.58s, down to
      `tool:Read` 0.19s). Eyeballed by the drain orchestrator directly (this
      session) on real production data from this same live /drain run,
      profiled via `agentprof claude --days 1` after task 03 landed.
      Default `pprof -top` pruning (nodefraction) hides these small-duration
      nodes; `-nodefraction=0 -edgefraction=0` surfaces them — see the
      evidence file's header for the exact commands. `stage:` markers
      (task 03's work) were also observed as a bonus confirmation.

## Discovered

- `go tool pprof -top`'s default node-fraction pruning hides `tool:` frames on real day-scale profiles (each tool call's individual duration is tiny relative to the total span across all projects), so the plain command from Step 3 shows zero `tool:` lines even though the data is present and correct — `-nodefraction=0 -edgefraction=0` (or a narrower `--days`/project filter) is needed to see them. Worth a one-line note in agentprof's own docs or `agentprof/README.md` so a future human running this command by hand doesn't conclude the feature is broken.
