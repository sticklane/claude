# drain — script bundle (not a triggerable skill)

This directory is a **script bundle** supporting
`antigravity/.agents/workflows/drain.md`, not a triggerable skill. It
deliberately contains no `SKILL.md`: `drain` is launch-gated at its
`.claude/skills/drain/SKILL.md` source (a launch-authorization contract —
explicit live-user authorization only; it replaced the old
`disable-model-invocation` flag in 2026-07), so in the Antigravity mirror
it ports to a workflow (`.agents/workflows/drain.md`), where every
workflow is human-launched by the runtime anyway.

`screen-stub.sh` is a verbatim mirror of `.claude/skills/drain/screen-stub.sh`
— the deterministic prompt-injection screen the drain workflow's stub-intake
step invokes. `admission.py` and `drain_frontier.py` are verbatim mirrors of
their `.claude/skills/drain/` counterparts — the spec-lease-claim/cross-spec
admission decision and the per-spec frontier report the workflow's step 1
and step 2 shell out to. All three live here (rather than the `.claude/`-only
path) so the mirrored workflow can reference real, runnable scripts inside
the Antigravity tree; `admission.py` depends on
`../_shared/touch_disjoint.py` and `drain_frontier.py` depends on
`../_shared/headers.py`, both already mirrored under `_shared/`.
