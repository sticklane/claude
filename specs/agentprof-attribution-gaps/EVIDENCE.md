# Evidence: attribution gaps, 2026-06-27 → 2026-07-11

Source: `agentprof claude --days 14` run 2026-07-11 (94,182 samples, 295
sessions, $9,195). Regenerate:

    cd agentprof && ./agentprof claude --since 2026-06-27T00:00:00Z -o /tmp/win.jsonl --summary /tmp/summary.json

## Slash-command skill misses (R1)

Turn frames matching `tNN · /<cmd>` split by whether a skill frame was
attached (cost in $):

| cmd | attributed | (no skill) |
|---|---|---|
| /agentic:* | 836 | 1,020 |
| /idea | 421 | 353 |
| /drain | 134 | 216 |
| /parallel | 188 | 114 |
| /build | 176 | 55 |
| /breakdown | 92 | 36 |
| /verify | 1 | 16 |
| TOTAL (all cmds) | 1,882 | **1,962** |

(`/clear` $76, `/model` $41, `/reload-plugins` $24 are harness builtins —
correctly skill-less, hence R1's builtin denylist.)

## Project pollution (R2)

- `sjaconette` (home dir as project): $3,862 / 33,959 calls — 42% of all
  spend under a catch-all row.
- ~30 `tmp.*` mktemp projects: ~$35 combined (eval/scratch runs).
- `agent-a571c48f410951a76`: $0.90 / 8 calls — an agent sidecar
  transcript dir minted as a project.
- `.claude` as a project: $0.40.

## Pending-sample noise (R3)

- 8,854 samples (9.4% of 94,182) with frame `tool:(pending)` and
  completely empty `values{}` — ≈30/session.

## by_model leakage (R4)

- `--summary` by_model contains key `main` holding 110,825,468 ms
  (30.8h) of duration and nothing else — the sum of main-loop tool
  durations (Bash 26.5h, Agent 2.2h, TaskOutput 1.2h, …), because
  `modelLeaf()` skips `tool:` frames and lands on `main`.
- `<synthetic>`: 59 calls, 0 tokens, 2.4h duration, counted in calls.

## Missing instance identity (R5)

- Labels observed across the window: `session`, `source`, `turn`,
  `priced` only. Five parallel same-type agents in one turn are one
  indistinguishable blob; a parallelism analysis this week initially
  mis-read /breakdown as sequential (per-type interval merging) until
  re-measured via overlapping in-flight calls: true avg max-concurrency —
  drain 4.9, /parallel 10.5, deep-research 11.5, idea 5.6, breakdown 4.0.

## Frame content risk (R6)

- Skill frames embed skill names verbatim; one retired local-only skill
  name appeared in this window's frames (verified NOT present in the
  already-pinned specs/drain-wake-cost profile). Evidence profiles pinned
  in-repo must be denylist-scrubbed; the denylist itself never ships.
