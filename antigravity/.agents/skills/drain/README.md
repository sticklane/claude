# drain — script bundle (not a triggerable skill)

This directory is a **script bundle** supporting
`antigravity/.agents/workflows/drain.md`, not a triggerable skill. It
deliberately contains no `SKILL.md`: `drain` is launch-gated at its
`.claude/skills/drain/SKILL.md` source (a launch-authorization contract —
explicit live-user authorization only; it replaced the old
`disable-model-invocation` flag in 2026-07), so in the Antigravity mirror
it ports to a workflow (`.agents/workflows/drain.md`), where every
workflow is human-launched by the runtime anyway.

The one file here, `screen-stub.sh`, is a verbatim mirror of
`.claude/skills/drain/screen-stub.sh` — the deterministic prompt-injection
screen the drain workflow's stub-intake step invokes. It lives here (rather
than the `.claude/`-only path) so the mirrored workflow can reference a real,
runnable script inside the Antigravity tree.
