# Evidence 09: R3 sample-drop re-measurement against real ~/.claude data

Measured 2026-07-13 against the local `~/.claude` data directory (read-only;
no data modified). Task 09 reproduces the R3 spec-level claim that tasks
03/08 honestly left MANUAL-PENDING from their isolated worktrees.

## Method

Two binaries built and run over the same live 14-day window (both invoked
within seconds of each other, so `time.Now()-14d` resolves to the same
cutoff for both):

- **current** — parser at task-branch HEAD (`2a4ca72`), consolidation on.
- **b4971fe** — the pre-change parser, the R3 baseline
  (`b4971fe drain: release owner lease …`), built from a clean tree extract.

```sh
# current parser (built from agentprof/ at HEAD)
go build -o /tmp/agentprof-current .
/tmp/agentprof-current claude --days 14 -o current.jsonl

# pre-change parser at b4971fe (extract whole tree — agentprof was the repo
# root at that commit — then build)
git archive b4971fe | tar -x -C /tmp/b4971fe && (cd /tmp/b4971fe && \
  go build -o /tmp/agentprof-b4971fe .)
/tmp/agentprof-b4971fe claude --days 14 -o b4971fe.jsonl

# counts
wc -l current.jsonl b4971fe.jsonl
grep -c 'tool:(pending)' current.jsonl        # pending frames, current
grep 'tool:(pending)' current.jsonl | grep -c pending_calls  # non-empty
grep -c 'tool:(pending)' b4971fe.jsonl        # pending frames, b4971fe
grep 'tool:(pending)' b4971fe.jsonl | grep -c '"values"'     # non-empty
```

## Re-measured numbers

| metric                               | b4971fe (pre-change) | current (HEAD) |
| ------------------------------------ | -------------------- | -------------- |
| total samples                        | 131,521              | 131,519        |
| `tool:(pending)` frame samples       | 11,663               | 4              |
| — of those, empty-valued             | 11,663               | **0**          |
| — of those, carrying `pending_calls` | 0                    | 4              |
| non-pending samples                  | 119,858              | 131,515        |

Derived:

- **Total-sample drop vs b4971fe: 0.0015% (2 samples).** The projected
  **≥8%** does **not** hold — not even close.
- **Empty-valued `tool:(pending)` samples in the current parser: 0.** All 4
  current pending samples carry `pending_calls=1`. (R3's first half holds.)
- b4971fe's 11,663 empty pending samples were **8.87%** of its total — this
  is the figure the original "≥8% drop" projection was built on.
- Current has **11,657 more** non-pending samples than b4971fe
  (131,515 − 119,858), ≈ the 11,663 pending samples b4971fe emitted.

## Diagnosis — why the ≥8% drop did not materialize

The projection assumed the ~8.87%-of-total pending samples would be
**eliminated** by consolidation, dropping the total by ~8%. They were not
eliminated; they were **re-attributed, sample-count-neutrally**:

1. **Tasks 03/08 match fixes.** b4971fe left the Agent-tool / TaskOutput
   tool_use blocks unmatched, emitting one empty `tool:(pending)` sample per
   call (11,663 of them). Tasks 03/08 taught the parser to match those result
   shapes, so in the current parser each such call now resolves to its **real
   tool frame** — still one sample, just correctly attributed instead of
   pending. Converting a pending sample into a matched tool sample changes the
   count by zero. The 11,657-sample rise in non-pending samples is exactly
   this re-attribution.

2. **Consolidation only collapses same-turn multiples.** Consolidation
   removes a sample only when _several_ unmatched calls share one turn (N→1,
   saving N−1). After the match fixes, only **4** unmatched calls remain in
   the whole window, each in a distinct turn, so consolidation collapses
   4→4 — zero net removal.

So the ≥8% figure conflated "pending samples are 8.87% of the total" with
"consolidation will remove 8% of the total." The pending volume was real,
but the fix that addressed it (result-matching) is count-neutral by
construction, and the residual consolidation savings are negligible. The
parser is behaving correctly: eliminating those samples would _lose_ the
cost attribution that tasks 03/08 exist to recover, so there is no parser
bug to fix here.

## Resolution

R3's empty-values-count-0 criterion **passes** as written. The ≥8%
total-drop criterion was based on a stale premise and is re-scoped by an
explicit maintainer decision recorded in `SPEC.md` (R3 requirement note and
acceptance criterion), citing this file.
