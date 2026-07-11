# Orchestrator-share findings: /breakdown, /build, /idea

Phase 1 (measure) of `specs/orchestrator-share-audit`. Resolves the puzzle in
the spec: why 70–84% of these skills' cost stays in the frontier-priced
main context despite explicit "use scouts, don't read the codebase" doctrine.

**Answer, up front:** the doctrine *is* followed — main-line tool activity is
delegated to sub-agents, and the handful of main-line `tool:Read` frames are
spec/task files (breakdown, idea) or edit-targets (build), none of them
codebase "looking-around." The main-line spend is **accumulated-context
re-billing**: `cache_read` is the single largest cost category for all three
(46–62%), i.e. each turn re-bills the growing cached prefix (spec + task files
+ interview + code under edit). This is intrinsic to the coupling/synthesis
work the spec requires stay main-line, not a delegation failure.

## Method and reproducibility

All snapshot-derived numbers below come from **one** command against the frozen
snapshot checked in at `specs/orchestrator-share-audit/samples-2026-07-04-to-11.jsonl.gz`:

```
python3 specs/orchestrator-share-audit/analyze.py
```

- **Main-line** = a sample whose `stack` contains `skill:{breakdown|build|idea}`
  and **no** `agent:`/`wf:` frame (no delegation).
- **Cost by token category** is derived from the snapshot itself: per-model
  USD/Mtok rates are recovered by least squares over every model-call sample of
  that model (cost is linear in the four token counts). Haiku recovers exactly
  ($1 / $5 / $0.10 / $1.25, R²=1.0), validating the method; frontier models fit
  R²≈0.95 because Anthropic's >200k long-context premium is a second rate tier a
  single-rate fit cannot separate — so **category dollars carry ~5% model
  error**. `analyze.py` prints the derived per-skill total beside the exact
  measured total as a fit check (deltas −0.6% to −3.7%). **Token counts and
  `tool:Read` counts are exact.**
- **Rewrite subset** = samples with `cache_write > max(cache_read, 50k)` — large
  rewrites, the re-billing mechanism for accumulated context (these *overlap*
  cache_read cost, they do not partition it).
- `tool:` frames carry `duration_ms` only, never file paths or cost — filenames
  are recovered from raw `~/.claude` transcripts (§ per skill, labeled
  **unpinned (raw transcripts, mutable)**).

Measurement caveat surfaced by this audit: in this snapshot every *in-flight*
tool frame is `tool:(pending)` (name unresolved); only *completed* tool frames
carry a resolved name (`tool:Read` etc.). The per-turn counts below use the
resolved frames. See "Discovered" note in the task report re: agentprof frame
naming.

---

## /breakdown — main-line $141.51 (baseline orchestrator share 84%)

Command: `python3 specs/orchestrator-share-audit/analyze.py` → `## /breakdown` block.

**(i) Cost by token category** (derived total $136.25, fit delta −3.7%):

| category | cost | share |
|---|---|---|
| input | $0.98 | 0.7% |
| output | $25.49 | 18.7% |
| cache_read | **$84.37** | **61.9%** |
| cache_write | $25.41 | 18.6% |

output + cache_write = **37.4%** (does **not** dominate; cache_read 61.9% dominates).

**(ii) Rewrite subset** (`cw>max(cr,50k)`): n=6 samples, **$18.98** (13% of main-line).

**(iii) Main-line `tool:Read` counts per turn:** 6 frames over 3 turns —
`{(33719413, turn05): 4, (9744b993, turn02): 1, (b89f3cb1, turn01): 1}`.

*unpinned (raw transcripts, mutable)* — recovered filenames + emitting step:
- `33719413` (t05 `/critique and /breakdown these tasks`): reads are the spec's
  own task files under decomposition plus a scratchpad working list
  (`.../scratchpad/unverified_tasks.txt`) and one memory note — Procedure step 1
  ("Read the spec") / step 3 ("Write task files"). No codebase file.
- `9744b993` (t02 `/breakdown agentprof`): reads are `SPEC.md` + task files —
  step 1/3.
- `b89f3cb1` (t01, hub): a spec file + a doc — step 1.
- Doctrine check: breakdown step 2 forbids *reading the codebase to determine
  file-level dependencies* ("ask scout agents — don't read the codebase into
  this session"). **Zero** such reads occurred main-line; every recovered read
  is the spec or a task file it is authoring. **No violation.**

**(iv) Verdict — KEEP (already-optimal, number-backed).** Routing rule:
no doctrine-violating `tool:Read` frames exist, so the drafter restructure is
pre-approved *only if* output + cache_write dominate main-line cost. They are
37.4% — cache_read (61.9%) dominates — so **the drafter restructure is not
pre-approved by the rule.** The spend is re-billing of the spec plus the
growing set of *coupled* task files the main session must hold in context to
pin Status / Depends-on / Touch / Group — the coupling work the spec explicitly
keeps main-line. Drafting (output, 18.7%) is the only delegable slice and fails
the dominance bar. Residual lever (not triggered): delegating per-task Goal/Steps
*prose* would trim the 18.7% output and slow cache_read growth, but the rule was
designed to withhold that restructure until drafting-type cost dominates, which
it does not here.

## /build — main-line $57.55 (baseline orchestrator share 78%)

Command: `python3 specs/orchestrator-share-audit/analyze.py` → `## /build` block.

**(i) Cost by token category** (derived total $57.18, fit delta −0.6%):

| category | cost | share |
|---|---|---|
| input | $0.28 | 0.5% |
| output | $13.22 | 23.1% |
| cache_read | $26.07 | 45.6% |
| cache_write | $17.62 | 30.8% |

output + cache_write = **53.9%** (majority; reflects intrinsic implementation —
writing code + re-billing the code-under-edit prefix).

**(ii) Rewrite subset:** n=5, **$11.18** (19% of main-line).

**(iii) Main-line `tool:Read` counts per turn:** 22 frames over 6 turns —
`{(3912b902,t02):1, (44c55bfa,t02):7, (bf69c08e,t02):1, (c8d38e51,t02):3, (d866a2c1,t02):7, (26383f59,t03):3}`.

*unpinned (raw transcripts, mutable)* — recovered filenames + emitting step:
- Reads are the task file (step 0 "Read the task file") plus TypeScript
  edit-targets in `hub/packages/core/src/**` and `hub/domains/food/**`
  (`index.ts`, `TypedStorage.ts`, `createStorageService.ts`, `dateFormatters.test.ts`,
  `linkify.test.tsx`, `remote.ts`, `worker/index.ts`) — step 2 implementation.
- Doctrine check: build step 0/2 permits direct reads *of edit-targets* ("Read a
  file directly only when you're about to edit it") and delegates *unclear
  existing code* to scouts. Read-then-edit correlation: of ~13 main-line source
  reads, 11 were subsequently Edited/Written in the same session; the 2 not
  edited (`TypedStorage.ts`, `remote.ts`) are the interface/type files an
  adjacent edit implements against. **No systematic looking-around → no violation.**

**(iv) Verdict — KEEP (already-optimal, number-backed).** No doctrine violation;
the drafter restructure is breakdown-specific and does not apply. The 53.9%
output+cache_write share is intrinsic TDD implementation cost (authoring code and
tests, re-billing the growing edited-file context), not a delegable drafting
step. Small-sample note (spec open question): $57.55 is the smallest of the
three totals but rests on 484 main-line samples across 6 distinct build sessions
— adequate to judge; a 30-day widen was not required.

## /idea — main-line $81.50 (baseline orchestrator share 70%)

Command: `python3 specs/orchestrator-share-audit/analyze.py` → `## /idea` block.

**(i) Cost by token category** (derived total $80.82, fit delta −0.8%):

| category | cost | share |
|---|---|---|
| input | $0.68 | 0.8% |
| output | $14.31 | 17.7% |
| cache_read | **$47.80** | **59.1%** |
| cache_write | $18.03 | 22.3% |

output + cache_write = 40.0% (cache_read 59.1% dominates).

**(ii) Rewrite subset:** n=4, **$12.39** (15% of main-line).

**(iii) Main-line `tool:Read` counts per turn:** 7 frames over 3 turns —
`{(703f51d7,t01):1, (f76e4ec6,t03):2, (ae55a12f,t15):4}`.

*unpinned (raw transcripts, mutable)* — recovered filenames + emitting step:
- `ae55a12f` (t15 `/idea skill that collects specs`): reads are existing `SPEC.md`
  files and skill/agent reference files — the *artifact under design is itself a
  spec-collecting skill*, so reading specs/skills is the subject matter, gathered
  during "Scout before you ask" / draft (steps 1–2), not codebase exploration.
- `f76e4ec6` (t03): 4 skill-refs + task files + one memory note + one repo test
  script (`claude/tests/test_workboard_render.sh`) — spec-drafting context.
- `703f51d7` (t01): 2 spec files.
- Doctrine check: idea delegates codebase scouting to 2–4 parallel scouts; its
  main-line reads are spec/skill artifacts (the thing being specified), not code
  under investigation. **No violation.**

**Interview handling (spec open question).** Whether idea's user-paced TTL-expiry
rewrites should be excluded before judging its share: measured — of the $12.39
rewrite subset, only **$3.35 (1 sample)** follows a >5-min idle gap (cache-TTL
expiry = user think-time between AskUserQuestion turns); the other $9.04 are
active (<5 min) rewrites. Command:
```
python3 - <<'PY'
import gzip,json
from datetime import datetime
from collections import defaultdict
S="specs/orchestrator-share-audit/samples-2026-07-04-to-11.jsonl.gz"
ml=lambda s:not any(f.startswith(("agent:","wf:")) for f in s)
sk=lambda s:next((f.split(":",1)[1] for f in s if f.startswith("skill:") and f.split(":",1)[1]=="idea"),None)
p=lambda t:datetime.fromisoformat(t.replace("Z","+00:00"))
rows=defaultdict(list)
for L in gzip.open(S,"rt"):
    o=json.loads(L)
    if "values" in o and sk(o["stack"]) and ml(o["stack"]): rows[o["labels"]["session"]].append((p(o["time"]),o["values"]))
idle=act=0.0
for s,l in rows.items():
    l.sort(key=lambda x:x[0])
    for i,(t,v) in enumerate(l):
        if v.get("cache_write_tokens",0)>max(v.get("cache_read_tokens",0),50000):
            g=(t-l[i-1][0]).total_seconds() if i else 0
            (idle:=idle+v["cost_microusd"]) if g>300 else (act:=act+v["cost_microusd"])
print("idle(>5m) $%.2f  active $%.2f"%(idle/1e6,act/1e6))
PY
```
User think-time therefore does **not** dominate ($3.35 = 4% of $81.50). Excluding
it leaves ~$78.15 main-line / ~$34 delegated ≈ **68%** — essentially unchanged
from the 70% baseline. **The verdict uses the raw (with-think-time) figure**,
because idea's cost is driven by genuine cache_read synthesis re-billing across
interview turns (59.1%), not by idle TTL expiry.

**(iv) Verdict — KEEP (already-optimal, number-backed).** No doctrine violation;
codebase scouting is delegated. The 70% main-line share is intrinsic interview
synthesis (user-paced AskUserQuestion turns whose accumulating context is
re-billed as cache_read) plus spec authoring — not a delegation gap and not an
artifact of user think-time (measured at 4%).

---

## Summary

| skill | main-line $ | share | dominant category | doctrine violation | verdict |
|---|---|---|---|---|---|
| /breakdown | $141.51 | 84% | cache_read 61.9% | none | KEEP (intrinsic coupling re-billing) |
| /build | $57.55 | 78% | cache_read 45.6% / out+cw 53.9% | none | KEEP (intrinsic TDD implementation) |
| /idea | $81.50 | 70% | cache_read 59.1% | none | KEEP (intrinsic interview synthesis) |

R5 outcome (Phase 1): three number-backed **"already optimal"** certifications —
the spend is accumulated-context re-billing of work the spec keeps main-line
(coupling, implementation, interview), with zero doctrine-violating main-line
reads. No skill-text diff is warranted at a delegable step (R2: none found). No
drafter restructure is pre-approved (breakdown fails the output+cache_write
dominance precondition). Task 02 records these certifications.

### Task 02 — verdict outcomes

Task 02 mapped each verdict to its outcome branch (landed fix / deferral+reason
/ certified-optimal) and confirmed the mapping independently against this doc's
`tool:Read` recovery (§iii per skill) and the SPEC routing rule. Outcome, one
line per skill:

- **/breakdown — CERTIFIED-OPTIMAL (KEEP).** No doctrine-violating main-line
  read (§(iii): all recovered reads are the spec/task files under decomposition,
  none codebase looking-around), so no R2 skill-text fix; drafter restructure
  NOT pre-approved because output+cache_write = 37.4% < cache_read 61.9% (§(i)/(iv))
  — the routing-rule dominance precondition fails, so the 84% share is certified
  as intrinsic coupling re-billing, not a delegation gap.
- **/build — CERTIFIED-OPTIMAL (KEEP).** No doctrine violation (§(iii): 11 of
  ~13 main-line source reads were edit-targets; the 2 unedited are interface/type
  files an adjacent edit implements against), so no R2 fix; the breakdown-specific
  drafter restructure does not apply, and 53.9% output+cache_write (§(i)) is
  certified as intrinsic TDD implementation cost, not a delegable drafting step.
- **/idea — CERTIFIED-OPTIMAL (KEEP).** No doctrine violation (§(iii): main-line
  reads are the spec/skill artifacts being specified, codebase scouting is
  delegated), so no R2 fix; restructure N/A, and the 70% share is certified as
  intrinsic interview synthesis (cache_read 59.1%, §(i)) — measured NOT to be
  user think-time (TTL-idle rewrites = $3.35, 4% of $81.50).

No skill-file edit was warranted at any delegable step (R2: none found across all
three), and no restructure met the routing rule's pre-approval bar, so no
`.claude/skills/*` change ships from Task 02 — therefore no antigravity mirror
port and no `.claude-plugin/plugin.json` bump are required. The R5 no-op guard is
satisfied by the three number-backed certifications above.

---

## R4 — regression check

Re-run the audit against the trailing-7-day profile and compare per-skill shares
to the baselines below. Capture a fresh bounded snapshot the same way the frozen
one was captured (agentprof samples for the trailing week), then point the
checked-in analyzer at it via the `AUDIT_SNAPSHOT` env override:

```
# 1. capture trailing-7-day agentprof samples as gzipped jsonl (same emitter as the frozen snapshot):
agentprof claude --days 7 --emit-samples > /tmp/orch-share-week.jsonl && gzip -f /tmp/orch-share-week.jsonl
# 2. re-run the identical method against the fresh window:
AUDIT_SNAPSHOT=/tmp/orch-share-week.jsonl.gz python3 specs/orchestrator-share-audit/analyze.py
```

**Thresholds (alert / re-open the audit if any holds):**
- **Orchestrator share** climbs > **5 percentage points** above baseline for any
  skill (breakdown > 89%, build > 83%, idea > 75%).
- **Category flip:** for /breakdown or /idea, `output + cache_write` overtakes
  `cache_read` as the dominant category — signals drafting/rewrite (a delegable
  cost) became the driver, which *would* satisfy breakdown's drafter-restructure
  precondition; re-run the routing rule.
- **Rewrite subset** exceeds **30%** of a skill's main-line cost — large rewrites
  (not steady re-reads) dominate; investigate cache-TTL / context churn.

Baseline (frozen 2026-07-04→11): breakdown 84% (cache_read-dominant),
build 78% (out+cw 53.9%), idea 70% (cache_read-dominant), rewrite subsets
13% / 19% / 15%.
