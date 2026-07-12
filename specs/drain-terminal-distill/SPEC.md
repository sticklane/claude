# Drain terminal distill: capture lessons automatically when autonomous work ends

Status: open
Priority: P1
Breakdown-ready: true

## Problem

Drain's two terminal states end autonomous work without capturing what it
learned. Today drain SKILL.md merely SUGGESTS distillation ("if any
verdict exposed a decomposition or spec problem, run /distill before the
next queue", SKILL.md:~600) and names /distill as the next pipeline step
(~648) — both depend on a human remembering to launch it, which the
2026-07-11/12 runs show doesn't happen: 8+ generations, 17+ merged tasks,
multiple worker Decisions, critic findings, a screen false-positive, and
a spec-defect deferral, and no /distill ran. Steven's ask (2026-07-12):
"we should auto distill when autonomous work completes either because we
run out, or because we hit the generation limit." /distill is
model-invocable (a light artifact stage with no launch contract), but the
self-chain conventions' condition (a) — a critic-READY artifact — cannot
apply to it (distill consumes a run, it ships no gated artifact), so
unlike 3b's /breakdown and critique intake's /critique, this needs an
explicit new terminal-capture carve-out in CLAUDE.md's self-chain bullet
(R1 adds it).
The timing is also exactly right for cache economics: distill batches
CLAUDE.md/rules writes "at session end" (token-discipline, Cache
economics) — a drain terminal state IS session end.

## Solution

Drain self-chains into /distill at both terminal states — queue
exhaustion (after the exit checklist) and the max-generations-cap stop
(after the baton + needs-attention note) — announced in one line, invoked
via the Skill tool. The distill pass mines the RUN, not just the hub's
conversation: worker `Decisions:` and `## Progress` entries committed
this run, critique/gate findings, sweep/screen incidents, and the exit
checklist itself. Unattended-safe: no AskUserQuestion — a learning
needing a human judgment becomes a `decide` entry in HUMAN.md's
Agent-filed blockers section (the human-blockers-doc grammar) instead of
an interview; "nothing worth keeping" stays a valid outcome.

## Requirements

- R1 **One terminal distill, in step 4.** Drain SKILL.md step 4: after
  the exit checklist is delivered (and any lease/baton cleanup
  committed), the session invokes /distill via the Skill tool, announced
  in one line — AT MOST ONCE PER SESSION. This is a NEW explicit
  self-chain carve-out, not a reuse of 3b's: the self-chain conventions'
  condition (a) (critic-READY artifact) cannot apply to distill (it
  consumes a run, it doesn't ship a gated artifact), so CLAUDE.md's
  self-chain bullet gains one sentence sanctioning terminal-capture
  self-chains (drain's terminal distill) gated by the terminal state
  itself rather than a READY verdict. The existing conditional
  suggestion at ~600 is replaced by this unconditional terminal step
  (a run with nothing to distill reports "nothing worth keeping"
  through distill, not by skipping it), and the closing
  "Next pipeline step: /distill after a drained queue" line (~648) is
  rewritten to state distill self-chains in-session at terminal states
  ("(self-chains per conventions)" marking), covering both exhaustion
  and the cap stop. Distill's file writes commit per its own
  conventions; the run's final message appends distill's
  one-line-per-learning summary after the checklist.
- R2 **Cap path reaches the same distill via step 4.** The
  max-generations cap stop already routes through step 4 (SKILL.md
  ~396-398: the cap generation "leads its exit checklist (step 4) with
  the resume command") — so the cap path gets the terminal distill FROM
  R1's step-4 insertion, not from a second one. 3a gains only a
  one-line pointer noting the cap generation's distill fires in step 4.
  Ordinary mid-run baton passes do NOT distill (they are not step-4
  entries); intermediate generations' lessons survive in committed
  artifacts the terminal distill mines. The once-per-session guard in
  R1 is the double-fire protection.
- R3 **Unattended-safe distill contract — pinned to distill SKILL.md.**
  One paragraph in `.claude/skills/distill/SKILL.md` (governing distill
  wherever invoked; NOT the drain-side clause): distill uses
  AskUserQuestion only where an interactive human is available (the
  skill's existing "where available, else…" idiom is the detection
  mechanism — no new signal invented); otherwise it never asks — a
  candidate learning that needs a human decision is filed as a `decide`
  entry under the repo HUMAN.md's `## Agent-filed blockers` section
  (human-blockers-doc grammar) and named in the summary; repo-file
  routing is otherwise unchanged. Detection ADOPTS drain's
  "AskUserQuestion where available, else…" idiom (drain SKILL.md:~594) —
  distill itself has NO interview today, so this paragraph adds the
  behavior; do not hunt for an existing clause in distill.
  The paragraph also extends the harvest
  step for orchestrated runs: sources include the run's committed
  artifacts (task-file `## Decisions`/`## Progress` entries,
  critique-findings files, screen/sweep incidents, the exit checklist),
  not only the session transcript. distill SKILL.md is a ported skill:
  the antigravity distill port (`antigravity/.agents/skills/distill/SKILL.md`)
  gets the content-equivalent paragraph in the same commit (codex
  reaches it via symlink — no codex work).
- R4 **Mirror + plugin closing.** Content-equivalent lines in the
  antigravity drain workflow and the codex drain wrapper where its text
  covers the terminal sequence (the antigravity DISTILL port is owned by
  R3/task 01, not here); plugin bump in the closing task's own commit;
  `claude plugin validate .` and `bash evals/lint-ultra-gate.sh` green
  (drain is ultra-path).

## Out of scope

- Distilling at environment kills (the runtime is dying; nothing should
  run) or at ordinary mid-run baton passes (R2's carve-out).
- Auto-distill for attended /build sessions (the human is present; the
  existing proactive-distill guidance covers it).
- Changing distill's routing table or file formats.
- Retroactively distilling past runs.

## Acceptance criteria

- [ ] `grep -qi 'terminal distill' .claude/skills/drain/SKILL.md`
  (anchor 0-hit everywhere today — verified 2026-07-12) AND MANUAL: step
  4 invokes /distill unconditionally after the exit checklist, at most
  once per session, one-line announcement, replacing the ~600
  conditional suggestion; the ~648 closing line rewritten with the
  "(self-chains per conventions)" marking covering both terminal states
  (R1)
- [ ] `grep -qi 'terminal-capture' CLAUDE.md` (0-hit today) AND MANUAL:
  the self-chain bullet's new sentence sanctions terminal-capture
  self-chains without a critic-READY artifact (R1)
- [ ] MANUAL: 3a carries only the one-line pointer (cap path distills
  via step 4); ordinary baton passes explicitly do not distill;
  no second insertion exists (R2)
- [ ] `grep -qi 'Agent-filed blockers' .claude/skills/distill/SKILL.md`
  (0-hit in distill today) AND MANUAL: interactive-detection uses the
  existing where-available idiom; run-artifact harvest sources
  enumerated (R3)
- [ ] `grep -qi 'Agent-filed blockers' antigravity/.agents/skills/distill/SKILL.md`
  → content-equivalent paragraph ported (R3)
- [ ] `grep -qi 'terminal distill' antigravity/.agents/workflows/drain.md`
  (0 today) AND `claude plugin validate .` passes AND
  `bash evals/lint-ultra-gate.sh` OK AND plugin version line modified in
  the closing task's own commit (R4)

## Open questions

(none — invocation is a NEW explicit terminal-capture carve-out added to
CLAUDE.md's self-chain bullet (R1), not a reuse of 3b's critic-READY
exception; the unattended interview problem routes through
human-blockers-doc's grammar with the existing where-available idiom as
the detection mechanism)

## Parallelization

Task map (/breakdown owns final shape): 01 = R1+R2+R3 skill text (drain
SKILL.md + distill SKILL.md + CLAUDE.md carve-out sentence +
antigravity distill port — single writer); 02 = R4 closing
mirror/bump (antigravity drain workflow + codex drain wrapper check +
plugin). Serialized. Cross-spec caution: drain SKILL.md is also
touched by human-blockers-doc/02 and drain-wake-cost/04 (extraction) —
Touch-disjoint admission serializes; prefer dispatch AFTER the extraction
merges. R3 depends conceptually on human-blockers-doc/01's rule existing;
if this spec drains first, the HUMAN.md grammar reference cites the spec
rather than the not-yet-landed rule file (acceptable — grammar is pinned
in that spec).
