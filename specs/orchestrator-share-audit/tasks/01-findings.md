# Task 01: Measure — per-skill main-line findings doc

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2 identification half, R4)
Touch: docs/orchestrator-share-findings.md, specs/orchestrator-share-audit/analyze.py

## Goal

`docs/orchestrator-share-findings.md` exists with, for each of /breakdown,
/build, /idea: the main-line cost split by token category, the rewrite
subset's cost, main-line `tool:Read` counts per turn from the frozen
snapshot plus transcript-recovered filenames for nonzero turns (labeled
unpinned), and a keep/restructure verdict applying the spec's routing
rule. The doc ends with the R4 regression-check command + thresholds.
Analysis code is checked in at `specs/orchestrator-share-audit/analyze.py`
so every snapshot number is reproducible.

## Touch

The findings doc and the analysis script only. Do NOT edit any skill
files (task 02 acts on the verdicts), agentprof source (out of scope —
gaps route to specs/agentprof-instrumentation as new task suggestions in
## Deferred questions), or the frozen snapshot.

## Steps

1. Read ../SPEC.md fully — the Measurement constraint and routing rule
   sections are the method.
2. Write `analyze.py` to read
   `specs/orchestrator-share-audit/samples-2026-07-04-to-11.jsonl.gz`
   directly via Python's `gzip` module (never a transient gunzipped copy —
   the acceptance command must be self-contained for a fresh verifier):
   for samples whose stack contains
   `skill:breakdown|build|idea`, split main-line (no `agent:`/`wf:`
   frames) vs delegated; per skill report cost by token category
   (output/input/cache_read/cache_write), the rewrite subset
   (cache_write > max(cache_read, 50k)) and its cost, and `tool:Read`
   frame counts per turn (records without a `values` key carry tool
   frames; `tool:` frames have no cost — never price them).
3. For turns with nonzero main-line Read counts, open the raw transcripts
   (`~/.claude/projects/...`, session IDs from the sample labels) and
   recover filenames + the skill step that emitted them. Label this
   section "unpinned (raw transcripts, mutable)".
4. Decide /idea's interview handling (spec open question): compute its
   TTL-expiry rewrite share; if user think-time gaps dominate, report its
   share both with and without them and say which the verdict uses.
5. If any skill's week sample is too thin to judge, capture a wider
   snapshot per the spec's Solution, check it in alongside, and label
   which numbers come from which.
6. Apply the routing rule per skill → keep/restructure verdict with a
   one-paragraph rationale each.
7. Close the doc with the regression-check one-liner + thresholds (R4).

## Acceptance

- [x] `test -f /Users/sjaconette/claude/docs/orchestrator-share-findings.md` → exit 0, with all four elements per skill and a verdict each — verifier PASS; doc carries token-category split, rewrite subset, tool:Read-per-turn + unpinned filenames, and a KEEP verdict for each of breakdown/build/idea (evidence/01-findings.md)
- [x] `python3 /Users/sjaconette/claude/specs/orchestrator-share-audit/analyze.py` → runs clean against the checked-in .gz with no other inputs and prints the doc's headline numbers — verifier ran it self-contained; prints breakdown $141.51 (cache_read 61.9%), build $57.55, idea $81.50, matching the doc (evidence/01-findings.md)
- [x] Every snapshot-derived number in the doc names its producing command; transcript-recovered filename sections are labeled unpinned — verifier confirmed producing command per number and all three recovery subsections labeled "unpinned (raw transcripts, mutable)" (evidence/01-findings.md)
- [x] Findings doc ends with the regression-check command + thresholds — verifier confirmed the `## R4 — regression check` section (capture+rerun command + 3 thresholds) is last (evidence/01-findings.md)
