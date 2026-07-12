# Drain terminal distill: capture lessons automatically when autonomous work ends

Status: open
Priority: P1

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
model-invocable (a light artifact stage with no launch contract), so this
is a self-chain drain already has precedent for (3b's /breakdown, critique
intake's /critique — the sanctioned in-session Skill-tool exception).
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

- R1 **Exhaustion-path auto-distill.** Drain SKILL.md step 4: after the
  exit checklist is delivered (and any lease/baton cleanup committed),
  the session invokes /distill via the Skill tool — the same sanctioned
  in-session exception 3b uses — announced in one line. The existing
  conditional suggestion at ~600 is replaced by this unconditional
  terminal step (a run with nothing to distill reports "nothing worth
  keeping" through distill itself, not by skipping it). Distill's file
  writes commit per its own conventions; the run's final message appends
  distill's one-line-per-learning summary after the checklist.
- R2 **Generation-cap-path auto-distill.** SKILL.md 3a: the generation
  that hits the max-generations cap runs the same terminal distill after
  writing the baton + needs-attention note and before ending its turn —
  the cap is precisely when accumulated lessons would otherwise strand.
  A mid-run baton pass (normal generation handoff) does NOT distill; only
  the cap stop and exhaustion do — intermediate generations' lessons
  survive in committed artifacts the terminal distill mines.
- R3 **Unattended-safe distill contract.** One paragraph in distill
  SKILL.md (or its terminal-invocation clause in drain): when invoked
  from an unattended context, distill never uses AskUserQuestion; a
  candidate learning that needs a human decision is filed as a `decide`
  entry under the repo HUMAN.md's `## Agent-filed blockers` section
  (human-blockers-doc grammar) and named in the summary; repo-file
  routing (CLAUDE.md line / rules file / docs/memory topic / skill) is
  otherwise unchanged. Distill sources for a drain run explicitly include
  the run's committed artifacts: task-file `## Decisions`/`## Progress`
  entries, critique-findings files, screen/sweep incidents, and the exit
  checklist.
- R4 **Mirror + plugin closing.** Content-equivalent lines in the
  antigravity drain workflow (and its distill port if one exists —
  check; distill may be ported as a skill) and the codex drain wrapper
  where its text covers the terminal sequence; plugin bump in the
  closing task's own commit; `claude plugin validate .` and
  `bash evals/lint-ultra-gate.sh` green (drain is ultra-path).

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
  4 invokes /distill unconditionally after the exit checklist, one-line
  announcement, replacing the ~600 conditional suggestion (R1)
- [ ] MANUAL: 3a's cap stop runs the same terminal distill; ordinary
  baton passes explicitly do not (R2)
- [ ] `grep -qi 'never uses AskUserQuestion' .claude/skills/distill/SKILL.md || grep -qi 'never uses AskUserQuestion' .claude/skills/drain/SKILL.md`
  (phrase 0-hit today) AND MANUAL: unattended learnings needing judgment
  route to HUMAN.md `decide` entries; run-artifact sources enumerated
  (R3)
- [ ] `grep -qi 'terminal distill' antigravity/.agents/workflows/drain.md`
  (0 today) AND `claude plugin validate .` passes AND
  `bash evals/lint-ultra-gate.sh` OK AND plugin version line modified in
  the closing task's own commit (R4)

## Open questions

(none — invocation mechanism reuses 3b's sanctioned exception; the
unattended interview problem routes through human-blockers-doc's grammar)

## Parallelization

Task map (/breakdown owns final shape): 01 = R1+R2+R3 skill text (drain
SKILL.md + distill SKILL.md — single writer); 02 = R4 closing
mirror/bump. Serialized. Cross-spec caution: drain SKILL.md is also
touched by human-blockers-doc/02 and drain-wake-cost/04 (extraction) —
Touch-disjoint admission serializes; prefer dispatch AFTER the extraction
merges. R3 depends conceptually on human-blockers-doc/01's rule existing;
if this spec drains first, the HUMAN.md grammar reference cites the spec
rather than the not-yet-landed rule file (acceptable — grammar is pinned
in that spec).
