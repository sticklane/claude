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
not a new hook. Two mechanical companions ship with it, per the
2026-07-22 pivot: (a) a **compliance Stop hook** — the session cannot
end "done" while bd issues it claimed sit unclosed, converting the
community-reported "forgets beads by hour two" failure into a
mechanical refusal; (b) a **pre-flight budget check** — a small
script the skill runs before authoring a fan-out, estimating agent
count x per-agent floor against a configured threshold and requiring
an explicit override above it (advisory-plus-thin-guard, the ratified
cost posture). The injection screen (screen-stub.sh) applies to any
tracker-sourced text entering an authored script's prompts.

## Acceptance criteria

- [ ] the skill file exists with trigger phrases covering "what's
      next", "work the queue", "track this", and fan-out asks; passes
      `bash evals/lint-ultra-gate.sh` if it mentions ultracode
- [ ] a fresh-session eval scenario (evals/, stub-CLI tier) shows the
      skill: claiming before work, closing on done, and authoring a
      fan-out script whose mechanical stages carry a cheap-tier
      `model:` option
- [ ] a hook test: a fixture session state with a claimed-open bd
      issue → the Stop hook blocks completion with the issue named;
      close it → the hook passes
- [ ] the pre-flight check, fed a fixture plan of 30 agents against a
      20-agent threshold, refuses without the override flag and
      passes with it
- [ ] AGENTS.md names the skill as the attended daily default; the
      unattended queue mode is the same skill run headless

Next stage: /breakdown specs/beads-daily-skill/SPEC.md
(human-launched) — or build directly; it is one skill file plus one
eval scenario.
