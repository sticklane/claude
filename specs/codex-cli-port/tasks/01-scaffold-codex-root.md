# Task 01: Scaffold the codex/ project root

Status: in-progress
Depends on: none
Priority: P0
Budget: 35 turns
Spec: ../SPEC.md (requirements R4, R7; Solution items 1a-root-symlinks, 1b-AGENTS.md, 2, 4)
Touch: codex/.agents/skills/_shared, codex/.agents/skills/breakdown, codex/.agents/skills/critic, codex/.agents/skills/design, codex/.agents/skills/distill, codex/.agents/skills/factcheck, codex/.agents/skills/gate, codex/.agents/skills/handoff, codex/.agents/skills/idea, codex/.agents/skills/implementation-worker, codex/.agents/skills/list-specs, codex/.agents/skills/onboard, codex/.agents/skills/prioritize, codex/.agents/skills/scout, codex/.agents/skills/verifier, codex/.agents/skills/workboard, codex/AGENTS.md, .claude-plugin/plugin.json

## Goal

`codex/.agents/skills/` exists containing exactly 16 relative symlinks — one
per already-working `antigravity/.agents/skills/*` entry (the 15 skills
named in the spec's Out-of-scope list, plus `_shared`) — each resolving into
the real `antigravity/.agents/skills/` tree. `codex/AGENTS.md` exists as a
short real (non-symlinked) file. `.claude-plugin/plugin.json`'s version is
bumped in this same commit, since this is the commit that first adds
`codex/` (R7).

## Touch

Only the 16 symlink paths above, `codex/AGENTS.md`, and
`.claude-plugin/plugin.json`. Do NOT create `codex/.agents/skills/drain`,
`build`, `autopilot`, or `evals` — those four real directories are created
by sibling tasks 02 and 03, and a symlink at any of those four names would
collide with (or shadow) the sibling tasks' real directories.

**Landmine — read before symlinking.** `antigravity/.agents/skills/`
currently also contains a directory literally named `drain`. This is NOT
one of the 15 already-working skills: it has no `SKILL.md` and its own
`README.md` states "not a triggerable skill" — it is a script bundle
(holding `screen-stub.sh`) that supports
`antigravity/.agents/workflows/drain.md`. Do not symlink it. When you list
`antigravity/.agents/skills/` to enumerate what to symlink, exclude this
`drain` entry explicitly — it is not part of the 15-skill set this task
mirrors, and the name is reserved for task 02's real
`codex/.agents/skills/drain/` directory.

## Steps

1. `ls antigravity/.agents/skills` — confirm it lists `_shared` plus 16
   directories: the 15 real skills (`breakdown`, `critic`, `design`,
   `distill`, `factcheck`, `gate`, `handoff`, `idea`,
   `implementation-worker`, `list-specs`, `onboard`, `prioritize`, `scout`,
   `verifier`, `workboard`) and the non-skill `drain` script bundle. Exclude
   `drain` from the set you symlink.
2. From the repo root, for each of the 15 skill names above plus `_shared`,
   create a relative symlink:
   `ln -s ../../../antigravity/.agents/skills/<name> codex/.agents/skills/<name>`
   (matches the spec's own worked example for `list-specs`).
3. Verify every symlink resolves and is not dangling:
   `test -e codex/.agents/skills/<name>/.` for all 16 names.
4. Write `codex/AGENTS.md`: a short real file that points to
   `antigravity/AGENTS.md` for the shared pipeline orientation, and states
   the one Codex-specific fact `antigravity/AGENTS.md` doesn't know — that
   this project additionally exposes `drain`/`build`/`autopilot`/`evals` as
   explicit-invocation-only skills (`$drain`, `$build`, `$autopilot`,
   `$evals`, or the `/skills` command), with a one-line pointer to
   `codex/README.md` for the experimental-reliability caveat (don't
   duplicate that detail here — a sibling task owns `codex/README.md`).
5. Bump the `version` field in `.claude-plugin/plugin.json` in this same
   commit (this is "the commit that adds `codex/`" per R7 — later tasks add
   more content under `codex/` but do not bump the version again; see
   CLAUDE.md's own precedent of bundling a mirror + version bump into one
   task rather than every task that touches the mirrored tree).
6. Commit.

## Acceptance

- [ ] `find codex/.agents/skills -maxdepth 1 -type l | wc -l` → `16`
- [ ] `for n in _shared breakdown critic design distill factcheck gate handoff idea implementation-worker list-specs onboard prioritize scout verifier workboard; do test -e "codex/.agents/skills/$n/." || echo "BROKEN: $n"; done` → no output
- [ ] `test -f codex/AGENTS.md && grep -q "antigravity/AGENTS.md" codex/AGENTS.md`
- [ ] Version changed from base: `git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'` differs from `grep '"version"' .claude-plugin/plugin.json` (never compare against a hard-coded literal — a sibling task may have already moved it)
- [ ] `git show --stat HEAD -- .claude-plugin/plugin.json codex/` shows both paths touched in the same commit
