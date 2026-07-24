# handoff-resume hook

A `SessionStart` hook that flags an open handoff issue left in bd by
`/handoff`. On every session start it asks bd for open `handoff`-labeled
issues and, if any exist, injects a pointer at the `resume-handoff` skill
(`.claude/skills/resume-handoff/SKILL.md`) — so the only manual step left
after a heavy session is `/clear` itself. Earlier versions injected raw
"read it and continue" prose instead of naming a skill; that was advisory
context a live user message asking for something else correctly outranked
(CLAUDE.md's precedence order), so the resume happened inconsistently.
Naming the skill explicitly is what makes the resume deterministic — the
skill (not this hook) does the actual locate/read/resume/cleanup work.

## Why this is a hook, not a skill

`/clear` is a hard context reset — it ends whatever is currently running,
including a skill invocation. Nothing can "clear and then keep going" in
one action: the clearing IS the end of that action. A `SessionStart` hook
is the actual mechanism for "when a NEW context begins, do X automatically"
— it fires the moment the fresh context starts, after `/clear` or a new
launch alike.

## What it does

- Runs `bd list --label handoff --status=open --json` from the project root
  (`CLAUDE_PROJECT_DIR`, else the current directory) and reads each open
  issue's id and title from the result. `/handoff` files exactly one
  `handoff`-labeled issue per parked session (see
  `.claude/skills/handoff/SKILL.md`), so an open one is an unresumed
  session.
- One open issue → names its id and title and instructs "read it and
  continue." Several (a repo with more than one stale/in-flight handoff —
  a known real scenario in a heavily concurrent repo) → lists all of them
  and asks the resuming session to pick the one matching the task, rather
  than guessing.
- Silent (empty stdout, exit 0) whenever no open `handoff`-labeled issue
  comes back, so a repo with no in-flight handoff sees zero behavior
  change. That covers three cases the hook must never turn into noise:
  no such issue, `bd` or `jq` missing from `PATH`, and a project with no
  `.beads` store — this hook is wired globally per user and fires in every
  repo, most of which carry no bd store. It is the same tolerance
  convention `hooks/bd-compliance/check.sh` follows: a missing binary is a
  reason to skip the check, never a reason to speak up.
- Never closes the handoff issue itself — that's the `resume-handoff`
  skill's job once it has actually resumed the described work, not this
  hook's.

## Wiring (one user-run step)

This hook ships with the toolkit but is **not** auto-installed, same as
`hooks/session-refresh/`. Wire it globally in `~/.claude/settings.json` so
it covers every repo's sessions (replace `<TOOLKIT>` with the toolkit
checkout root):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<TOOLKIT>/hooks/handoff-resume/resume-check.sh"
          }
        ]
      }
    ]
  }
}
```

Merge this `SessionStart` array into any existing `hooks` block rather than
replacing it — see `hooks/session-refresh/README.md`'s wiring section for
the same caveat if you're running both hooks.

## Testing

`bash hooks/handoff-resume/test.sh` — builds a scratch git repo and bd store
under `mktemp -d` and files real `handoff`-labeled issues there, never
touching this toolkit's own `.beads` store. Needs `bd` and `jq` on `PATH`.
