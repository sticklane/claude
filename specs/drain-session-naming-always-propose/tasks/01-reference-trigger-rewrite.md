# Task 01: reference.md — drop the Generation:-keyed naming gate

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/drain/reference.md

## Goal

`.claude/skills/drain/reference.md`'s "Gen-1 startup advisories" opening
paragraph gets a pointer clause noting "Name the shell" has its own
trigger, and "Name the shell"'s own closing sentence drops the
`Generation:`-based gate in favor of the pre-existing "no custom name set
this conversation" / "no TTY" checks alone.

## Touch

Only `.claude/skills/drain/reference.md`. Do not touch
`.claude/skills/drain/SKILL.md` (task 02) or
`antigravity/.agents/workflows/drain.md` (task 03) — Touch-disjoint, no
shared design decision (this spec pins the exact wording each file needs).

## Steps

1. Read the "Gen-1 startup advisories" section (~line 42-69): the opening
   paragraph ("Four best-effort, never-blocking actions...") and the "Name
   the shell (best-effort)" sub-section.
2. In the opening paragraph, add one clause noting "Name the shell" below
   states its own more precise trigger, independent of this paragraph's
   `Generation:`-based gate — every other advisory (sweep foreign live
   sessions, hub-economics, mechanical preflight sweep) keeps this
   paragraph's gate unchanged. Do not otherwise rewrite the paragraph.
3. Replace "Name the shell"'s closing sentence — currently "Once, never
   re-set on baton generations (they inherit it), skip silently with no
   TTY." — with wording stating: fires once per session, the first time
   THIS conversation reaches step 1, regardless of the adopted owner
   lease's `Generation:` number; skip only if this conversation's tab
   already carries a custom name, or if there is no TTY (a detached
   headless baton self-relaunch, or an awaited subagent spawn, has
   neither). Per SPEC.md's Solution section: this is a correction, not new
   behavior — the no-TTY check already correctly excludes every relaunch
   path (headless `nohup` has no TTY; an awaited Task-tool subagent spawn
   has no TTY either), so dropping the `Generation:` gate doesn't newly
   admit any case that shouldn't fire.

## Acceptance

- [ ] `grep -c "regardless of the adopted owner lease's" .claude/skills/drain/reference.md` → ≥ 1
      (anchor deliberately stops short of "Generation" since the file's
      own idiom backticks that word, which would otherwise straddle the
      grep match unpredictably)
- [ ] `grep -c "states its own more precise trigger" .claude/skills/drain/reference.md` → ≥ 1
- [ ] `grep -c 'never re-set on baton generations' .claude/skills/drain/reference.md` → 0
      (the old unqualified clause must be replaced, not merely supplemented)
- [ ] End-to-end (semantic, not just phrase-presence — a fresh reader with
      no other context than the updated "Gen-1 startup advisories" /
      "Name the shell" sections can correctly classify): (a) "a human opens
      a new terminal and starts a `/drain` session that adopts an
      existing, in-progress owner lease at `Generation: 3` left by an
      earlier, session-refreshed session" → proposes a name; (b) "drain's
      own baton mechanism self-relaunches a successor generation headlessly
      via `nohup`" → does not propose (no TTY). Record both classifications
      as evidence.
