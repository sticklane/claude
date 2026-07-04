# Task 01: Drain baton-pass step + relaunch flag set

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: pending
Depends on: ../../drain-liveness-sweep/tasks/01-liveness-and-rescue.md
Priority: P1
Budget: 45 turns
Spec: ../SPEC.md (requirements R1, R1a)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

Drain has a baton-pass step: after N recorded verdicts (default 4,
`Relaunch-every: N` override read from the drained spec's SPEC.md header
block) or on self-observed degradation, drain writes
`specs/<slug>/DRAIN-BATON.md`, spawns a fresh detached headless generation
of itself with a new orchestrator flag set, reports the pass, and ends its
turn. Generation 1 is always attended; the `attended` word makes every
trigger an offer instead of a self-relaunch. The fresh-instance ritual
(baton → Status lines → git log → one cheap verification → dispatch) is in
SKILL.md; the exact relaunch command and flag set are in reference.md with
the recorded verdict of the background-dispatch verification.

## Touch

Serialized after drain-liveness-sweep 01 (same two drain files). Must NOT
touch: autopilot or parallel (task 02 owns them), breakdown or runtimes/
(task 03), the workboard scanner (task 04), docs/decisions (task 05),
`.claude-plugin/plugin.json` (task 05 bumps).

## Steps

1. Confirm the acceptance greps fail (RED).
2. **Mandatory verification first:** live-test whether a headless
   `claude -p` session supports background-agent dispatch with completion
   notifications (spawn a trivial `claude -p` probe that tries a
   background Task dispatch). Record the verdict verbatim in
   reference.md; if unsupported, the relaunch template documents drain's
   sequential headless-worker fallback instead.
3. Add the baton step to SKILL.md in ≤ 20 lines: trigger (N=4 default,
   `Relaunch-every:` override, degradation override signs), baton
   artifact grammar pointer, max-generations cap (10), attended opt-out,
   one-writer end-of-turn statement, the R1a ritual, batch-interview
   behavior for headless generations (write needs-attention into the
   baton and stop), and final-generation baton deletion.
4. Put the exact relaunch command template
   (`claude -p "/drain <spec> (generation G+1, baton: <path>)"`) and the
   NEW orchestrator flag set (Task dispatch allowed, merge/gates
   allowlist, --max-turns) in reference.md, plus the `DRAIN_RELAUNCH_CMD`
   env override hook the e2e fixture (task 05) will use.
5. Mirror to antigravity as "write the baton and stop" per R8's porting
   note (mirror text only; no self-relaunch).
6. Run acceptance.

## Acceptance

- [ ] `grep -n "baton" .claude/skills/drain/SKILL.md` → hits inside a step of ≤ 20 lines naming the default (every 4 verdicts), the override signs, the cap (10), and the read-state-then-verify ritual
- [ ] `grep -n "Relaunch-every" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` → hit(s); override location is the drained spec's SPEC.md header block
- [ ] `grep -n "generation" .claude/skills/drain/reference.md` → relaunch command template present with the orchestrator flag set AND the recorded background-dispatch verification verdict
- [ ] `grep -qi "attended" .claude/skills/drain/SKILL.md` → gen-1 attended rule + `attended` opt-out present
- [ ] `grep -q "DRAIN_RELAUNCH_CMD" .claude/skills/drain/reference.md` → exit 0
- [ ] `grep -qi "baton" antigravity/.agents/workflows/drain.md` → exit 0 ("write the baton and stop" adaptation)
