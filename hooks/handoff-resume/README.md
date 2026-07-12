# handoff-resume hook

A `SessionStart` hook that auto-resumes from a `HANDOFF.md` left by
`/handoff`. On every session start it searches the project for any file
named `HANDOFF.md` and, if found, injects an instruction to read it and
continue — so the only manual step left after a heavy session is `/clear`
itself; the resume instruction is no longer something you type by hand.

## Why this is a hook, not a skill

`/clear` is a hard context reset — it ends whatever is currently running,
including a skill invocation. Nothing can "clear and then keep going" in
one action: the clearing IS the end of that action. A `SessionStart` hook
is the actual mechanism for "when a NEW context begins, do X automatically"
— it fires the moment the fresh context starts, after `/clear` or a new
launch alike.

## What it does

- Silent (empty stdout, exit 0) when no `HANDOFF.md` exists anywhere under
  the project root — a repo with no in-flight handoff sees zero behavior
  change.
- Searches for any file literally named `HANDOFF.md`, not just
  `.claude/HANDOFF.md` — `/handoff` places it next to the active task/spec
  file when there is one, falling back to `.claude/HANDOFF.md` only when
  there isn't (see `.claude/skills/handoff/SKILL.md`).
- One match → names it and instructs "read it and continue." Multiple
  matches (a repo with more than one stale/in-flight handoff — a known
  real scenario in a heavily concurrent repo, since `.claude/HANDOFF.md`
  is a single rolling slot that different sessions' `/handoff` runs
  overwrite) → lists all of them and asks the resuming session to pick the
  one matching the task, rather than guessing.
- Skips `.git` and any worktree/`node_modules` directories, so drain's
  throwaway worktree copies under `.claude/worktrees/` never produce false
  matches.
- Never deletes or archives the handoff file — that stays the resuming
  session's job once the work it describes is actually done (normal
  handoff hygiene), not this hook's.

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

`bash hooks/handoff-resume/test.sh` — synthetic fixtures only, never
touches real session data or a real `HANDOFF.md`.
