# Drain session naming: always propose, on the right trigger

Breakdown-ready: true

## Problem

`/drain`'s "Gen-1 startup advisories" (`.claude/skills/drain/reference.md:42-69`,
mirrored in `antigravity/.agents/workflows/drain.md:42-49`) already derives a
queue-context descriptor (sorted spec slugs, comma-joined, 40-char cap) for
naming the terminal tab — but "Name the shell"'s trigger is keyed on the
owner lease's/baton's `Generation:` counter equalling 1: "At gen-1 startup
ONLY (never on baton generations — they inherit gen 1's)... Once, never
re-set on baton generations (they inherit it)". That counter tracks the
_queue's_ baton lineage, not _this conversation's_ history. A session that
resumes a stalled or session-refreshed run by adopting an existing owner
lease via the baton-lineage exception — a genuinely new, unnamed terminal
tab/conversation, just one that happens to inherit someone else's
in-progress `DRAIN-OWNER.md` at `Generation: 2` or higher — reads that
non-1 `Generation:` value and silently skips the naming proposal, even
though nothing has named THIS conversation's tab yet.

This is not hypothetical: it happened in this very session, which resumed a
stalled `codebase-context-tree` run via `.claude/HANDOFF.md` (pointing at a
baton whose `Generation:` was already 2/3), adopted the existing
`DRAIN-OWNER.md` lease under the baton-lineage exception, and never
proposed a terminal-tab name — the `Generation: 1` gate never matched.

## Solution

**The `Generation:` counter was always the wrong proxy.** What "Name the
shell" actually needs to distinguish is: a genuine, TTY-attached terminal
session that hasn't named itself yet (fire) vs. a process with no terminal
to name at all (skip). The existing text already has that exact
discriminator, right in its own closing sentence — "skip silently with no
TTY" — and it's sufficient on its own:

- A detached, headless baton self-relaunch (`nohup … &`, output redirected
  to a logfile — `.claude/skills/drain/reference.md`'s "Baton pass" section,
  the relaunch command template) has **no TTY** — already skipped by the
  existing no-TTY rule, with no need for any `Generation:`-based reasoning.
- An **awaited** baton self-relaunch (spawned as a background subagent
  "where an attended parent can supervise" — same "Baton pass" section) is
  a Task-tool subagent invocation, not an interactive terminal — it has no
  TTY either, so it's likewise already covered by the existing rule.
- A human opening a genuinely fresh terminal and launching `/drain` (literal
  `Generation: 1`) HAS a TTY and hasn't named this tab yet — fires, as it
  does today.
- A human opening a genuinely fresh terminal and resuming a stalled run via
  the baton-lineage exception (adopting `Generation: 2` or higher) ALSO has
  a TTY and hasn't named THIS tab yet — this is the case that's broken
  today, purely because of the extra `Generation:`-keyed gate layered on
  top of the TTY check.

So the fix is a **deletion**, not an addition: drop the `Generation:`-based
gating language from "Name the shell" specifically, and let the pre-existing
"no custom name set this conversation" + "no TTY" checks do all the work
they were already sufficient to do. No new vocabulary, no new discriminator
to invent or get wrong.

**Scope.** This changes only "Name the shell"'s own trigger. Every other
advisory under the same "Gen-1 startup advisories" umbrella (reference.md's
current text groups four: sweep foreign live sessions, hub-economics, and
the mechanical preflight sweep, alongside naming) keeps its existing
`Generation: 1`-only gate exactly as-is — the umbrella's shared opening
sentence gets one added clause noting "Name the shell" is now the exception
with its own trigger, not a full rewrite of the shared framing (deliberately
narrow, to avoid an unexamined behavior change to the other advisories —
e.g. hub-economics re-printing on every resumed session — which is
explicitly out of scope below).

## Requirements

R1: `.claude/skills/drain/reference.md`'s "Name the shell" sub-section's
closing sentence — currently "Once, never re-set on baton generations (they
inherit it), skip silently with no TTY." — is replaced with wording stating:
fires once per session, the first time THIS conversation reaches step 1,
regardless of the adopted owner lease's `Generation:` number; skip only if
this conversation's tab already carries a custom name, or if there is no
TTY (a detached headless baton self-relaunch, or an awaited subagent spawn,
has neither).

R2: `.claude/skills/drain/reference.md`'s "Gen-1 startup advisories" opening
paragraph gets one added clause (not a full rewrite) noting that "Name the
shell" below states its own more precise trigger, independent of this
paragraph's `Generation:`-based gate — every other advisory keeps this
paragraph's gate unchanged.

R3: `.claude/skills/drain/SKILL.md`'s "Gen-1 startup advisories" summary
line is updated so it no longer states unqualified that naming fires "At
gen-1 startup ONLY (never on baton generations)" — note inline that naming
has its own precise trigger, not gen-1-restricted, pointing to reference.md
for detail; the other advisories' gen-1-only framing is unchanged.

R4: `antigravity/.agents/workflows/drain.md`'s mirrored "Name the run"
section gets the same re-scoped trigger as R1, adapted to that file's
phrasing (naming surface rather than TTY, since Antigravity's mechanism
differs) — and, unlike R1, this requires editing the WHOLE section, not
just its closing clause. Reference.md's naming sub-section carries no
inline gen-1 phrasing of its own (that framing lives in the shared umbrella
paragraph R2 handles separately), but antigravity's mirror has no such
umbrella: each advisory is its own self-contained, gen-1-labeled block.
Concretely, three parts of the section all currently assert or imply
gen-1-only and must all change together, or the section ends up
self-contradictory: (a) the header "**Name the run (gen 1,
best-effort).**" — drop or requalify the "(gen 1, ...)" tag; (b) the
opening sentence "At gen-1 startup, if the run/tab has no custom name
already, name it..." — replace with the re-scoped trigger statement:
fires once per session, the first time this run reaches step 1, regardless
of the adopted **owner lease's** `Generation:` number (same "owner lease's
Generation" phrasing as R1), since a resumed run's own tab has never yet
been named; (c) the closing clause "skip silently where none exists, and
never re-name on baton generations." — replace with: skip if already named
this run, or if no naming surface exists (a headless baton self-relaunch or
an awaited subagent spawn has neither).

R5: `.claude-plugin/plugin.json`'s `"version"` is bumped past its value at
implementation time (re-check the current value before implementing;
`"0.9.17"` as of this spec's authoring, but concurrent work bumps this
independently — the requirement is "bumped from whatever it currently is,"
never a hardcoded from/to pair) per CLAUDE.md's "bump version in
plugin.json whenever skill behavior changes" rule.

## Out of scope

- Changing the descriptor derivation logic (spec-slug sorting, the 40-char
  cap, the `…` truncation marker) — already adequate "context from the
  queue"; only the trigger condition changes.
- The "sweep foreign live sessions", "hub-economics", and "mechanical
  preflight sweep" advisories' own gating — R2/R3 add a pointer clause to
  the shared umbrella framing but do NOT change what triggers those; they
  keep firing gen-1-only, `Generation: 1`-gated, exactly as today. In
  particular, do not make hub-economics re-print its frontier-hub/heavy-hub
  recommendation on every resumed session — that would be an unexamined
  behavior change, not something this spec's Problem motivates.
- Building any new mechanical signal for "has this conversation already
  proposed a name" — the existing "no custom name set this conversation"
  check (kept, unchanged) already covers the only in-conversation
  re-trigger case that would be wrong.
- Codex's drain wrapper — check at breakdown/implementation time whether it
  duplicates this trigger language (CLAUDE.md's port-chain notes it's a
  thin overlay with some real-content files, not purely symlinks) and needs
  the same update; this spec does not pre-scope that as a requirement
  absent confirmation the text is actually duplicated there.

## Acceptance criteria

- [ ] `grep -c "regardless of the adopted owner lease's" .claude/skills/drain/reference.md`
      → ≥ 1 (R1; anchor deliberately stops short of "Generation" since the
      file's own idiom backticks that word — `` `Generation:` `` — which
      would otherwise straddle the grep match unpredictably; phrase absent
      today, verified via `grep -c` returning 0)
- [ ] `grep -c "states its own more precise trigger" .claude/skills/drain/reference.md`
      → ≥ 1 (R2; absent today)
- [ ] `grep -c "not gen-1-restricted" .claude/skills/drain/SKILL.md` → ≥ 1
      (R3; absent today)
- [ ] `grep -c "regardless of the adopted owner lease's" antigravity/.agents/workflows/drain.md`
      → ≥ 1 (R4; same shortened anchor as R1's check, absent today)
- [ ] Negative check (R1, confirms the old unqualified phrasing is actually
      gone, not merely supplemented): `grep -c 'never re-set on baton
generations' .claude/skills/drain/reference.md` → 0 (returns 1 today
      — this exact clause is being replaced, not appended to).
- [ ] Negative check (R4, same reasoning, antigravity — anchored on a
      single-line substring since the full phrase is line-wrapped in the
      file and would otherwise match 0 both before and after any edit):
      `grep -c 'never re-name' antigravity/.agents/workflows/drain.md` → 0
      (returns 1 today).
- [ ] R4's section-level fix (not just the closing clause): the mirror
      bakes its gen-1 gating into the section's own header and opening
      sentence too — unlike the source, which keeps that framing in a
      separate shared umbrella paragraph R2 handles. Negative check,
      section-scoped so it doesn't touch the unrelated "Startup session
      sweep" advisory right after it: `sed -n '/\*\*Name the run/,/\*\*Startup
session sweep/p' antigravity/.agents/workflows/drain.md | grep -c
'gen-1 startup'` → 0 (returns 1 today — the section's own opening
      "At gen-1 startup" must be removed or requalified, not left
      contradicting the new closing wording), and `grep -c 'Name the run
(gen 1, best-effort)' antigravity/.agents/workflows/drain.md` → 0
      (returns 1 today — the header's "(gen 1, ...)" tag is part of the
      same contradiction and must be dropped or requalified too).
- [ ] R5, version-agnostic: before editing, capture the current value with
      `grep -n '"version"' .claude-plugin/plugin.json`; after editing,
      `grep -c '"version"' .claude-plugin/plugin.json` → 1 (still exactly
      one version line) AND that line's value differs from the captured
      pre-edit value.
- [ ] End-to-end: a fresh reader (or a fresh agent session with no other
      context) reading only the updated "Gen-1 startup advisories" /
      "Name the shell" sections in `.claude/skills/drain/reference.md` can
      correctly classify, in one sentence each: (a) "a human opens a new
      terminal and starts a `/drain` session that adopts an existing,
      in-progress owner lease (at `Generation: 3`) left by an earlier,
      session-refreshed session" → proposes a name; (b) "drain's own baton
      mechanism self-relaunches a successor generation headlessly via
      `nohup`" → does not propose (no TTY). Both must be answered correctly
      from the updated text alone, with no reference to this SPEC.md.

## Open questions

(none)

## Parallelization

3 tasks. Task 01 (`.claude/skills/drain/reference.md`) and task 02
(`.claude/skills/drain/SKILL.md`) are Touch-disjoint with no shared
undecided design (this spec pins the exact wording each needs), so both
are immediately dispatchable and safe to run concurrently. Task 03
(`antigravity/` mirror + `plugin.json`) depends on task 01's landed
wording and runs alone.

- Group: 01, 02
