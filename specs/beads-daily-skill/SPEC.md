# A daily-driver skill: beads + native orchestration with tier discipline

Breakdown-ready: true
Rigor: prototype

## Problem

The 2026-07-22 worth-it review (research + this session's measurements)
found the minimal stack — bd for state, native ultracode for fan-out,
per-stage model routing for cost — covers most ATTENDED daily work at a
fraction of the custom machinery's cost, but the toolkit ships no skill
teaching it. Meanwhile the community-reported failure of exactly this
stack is model non-compliance ("agents forget beads by hour two"), the
same 0%-compliance disease this repo measured with ctx.

## Solution

One skill, `/queue` (working name), that makes the minimal stack the
attended default: it teaches (1) session start = `bd prime` + `bd
ready`; (2) work lands in bd — claim before starting, close on done,
file discovered work with `discovered-from`; (3) fan-out via native
ultracode WITH the cost discipline inline in every script it authors —
per-stage `model:` routing (scout tier for mechanical stages), capped
schema'd returns, script-variable context isolation; (4) results that
matter are filed to bd before the run ends (ultracode results
evaporate). Compliance is not left to prose alone: the skill's
description triggers on queue/task/what's-next phrasing, and the
session-start injection comes from `bd prime` (bd's own mechanism),
not a new hook.

## Acceptance criteria

- [ ] the skill file exists with trigger phrases covering "what's
      next", "work the queue", "track this", and fan-out asks; passes
      `bash evals/lint-ultra-gate.sh` if it mentions ultracode
- [ ] a fresh-session eval scenario (evals/, stub-CLI tier) shows the
      skill: claiming before work, closing on done, and authoring a
      fan-out script whose mechanical stages carry a cheap-tier
      `model:` option
- [ ] AGENTS.md names the skill as the attended daily default; the
      heavy pipeline (drain/agentic) is positioned as the unattended
      queue mode

Next stage: /breakdown specs/beads-daily-skill/SPEC.md
(human-launched) — or build directly; it is one skill file plus one
eval scenario.
