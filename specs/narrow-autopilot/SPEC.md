# Retire /autopilot, fold its distinct capability + reusable reference content into /build

## Problem

`/autopilot`'s mechanism table (`autopilot/SKILL.md:39-46`) has four rows.
Three overlap with capabilities `/drain` now covers at least as well
("fire-and-forget, this machine" and "CI/scripts" are `/drain`'s dispatch
mechanisms with retry ladders and verification gates autopilot lacks — its
"background worktree agent" row is, concretely, the same
worktree+Agent-tool+verdict-only pattern `/drain` already runs per queued
task). The fourth — never-auto-push, human-reviews-every-PASS — was
confirmed in conversation to be a *negative*, not a selling point, for a
user who values `/drain`'s auto-landing. That leaves exactly one
genuinely distinct capability worth keeping: same-session, `/goal`-bounded
runs with a pre-cap baton hand-off. `/goal` itself is a **runtime
built-in** (Claude Code's own transcript-evaluator command, not a
`.claude/skills/` file) that wraps *around* any procedure — autopilot
never implemented it, it only documented the pattern of wrapping its own
walk-away contract in a `/goal` invocation. `autopilot/reference.md` also
holds content with live consumers elsewhere: `onboard/SKILL.md:74` points
users at its scoped-permissions JSON template, and `drain/reference.md:388`
cites "the autopilot reference's headless rule" as the source of truth for
headless dispatch. Deleting autopilot without relocating that content
breaks both citations.

**Sequencing note**: `specs/build-doc-currency-check` also edits
`build/SKILL.md` (a citation/documentation addition near its "Close out"
section). This spec should land **first** — it restructures `build/
SKILL.md` (a new classification gate near the top, shifting every line
after it), so `build-doc-currency-check`'s anchors are written to be
found by section content, not a stale line number, and should be
re-verified against whatever this spec leaves behind.

## Solution

Delete `.claude/skills/autopilot/` (SKILL.md *and* reference.md) and
create `.claude/skills/build/reference.md` (new file) as the new home for
everything in the old reference.md that still has live consumers:

- **Scoped permissions JSON template** — moves verbatim. `onboard/
  SKILL.md:74`'s pointer is updated to `build/reference.md`.
- **Bounded goals (`/goal` pattern)** — moves verbatim, documenting that
  `/goal` is the *runtime's* mechanism: a human wraps `/build`'s own
  procedure in a `/goal "<criteria>, or stop after N turns"` invocation.
  `/build` itself parses no new flag and needs no code change to
  "support" this — bounded mode is a documented usage pattern, not a new
  code path.
- **Containment ladder** — moves verbatim.
- **Failure recovery** — moves verbatim into `build/reference.md`
  alongside the walk-away contract's escalation triggers (R2) — it's the
  same doctrine (a failed/capped run is evidence about the task file, not
  a debugging invitation: fix the spec, discard the branch, relaunch
  clean), directly relevant to bounded mode's failure path.
- **Headless template** — moves verbatim (becoming the canonical copy);
  `drain/reference.md:388`'s citation is updated to point at
  `build/reference.md`.
- **Pre-cap baton boundary** — moves verbatim (unchanged: it already cites
  `/drain`'s baton grammar rather than restating it).
- **"Background worktree agent" section is dropped, not moved** — it's the
  redundant-with-`/drain` capability the Problem section identifies;
  `build/reference.md` instead has one line pointing unattended
  fire-and-forget work at `/drain`.

`.claude/skills/build/SKILL.md` gains, near its start, the go/no-go
classification gate (autopilot's step 1: peripheral/prototype/
mechanically-verifiable is fine for a `/goal`-bounded run; core business
logic, security-sensitive code, or "looks right"-only verification is
not — use unbounded attended `/build`, today's default, instead) and the
walk-away contract's escalation triggers (same-step-fails-twice; reaching
a high-risk action), with a pointer to `build/reference.md` for the
concrete mechanism templates.

## Requirements

- **R1**: `.claude/skills/autopilot/` (SKILL.md and reference.md) is
  deleted; `.claude/skills/build/reference.md` is created with the six
  relocated sections named in Solution (permissions, `/goal` pattern,
  containment ladder, headless template, pre-cap baton, failure
  recovery), each moved verbatim, not summarized.
- **R2**: `.claude/skills/build/SKILL.md` gains: the go/no-go
  classification gate, the walk-away contract's two escalation triggers,
  and a pointer to `build/reference.md`'s pre-cap baton section for long
  `/goal`-bounded runs. `disable-model-invocation: true` on `/build` is
  unchanged — this was already true for both `/build` and the old
  `/autopilot`, so nothing about invocation gating changes.
- **R3**: `onboard/SKILL.md:74`'s pointer to the scoped-permissions
  template is updated from `autopilot/reference.md` to `build/
  reference.md`. `drain/reference.md:388`'s citation of "the autopilot
  reference's headless rule" is updated to cite `build/reference.md`.
- **R4**: Every skill with a `Next stage:` line naming `/autopilot` gets a
  concrete replacement, not a deletion that leaves it dangling:
  - `gate/SKILL.md`'s closing `Next stage: /autopilot specs/<slug>/
    tasks/NN-*.md (human-launched)` becomes
    `Next stage: /build specs/<slug>/tasks/NN-*.md (human-launched;
    /goal-bound it per build/reference.md for an unattended-feeling run)`.
  - `breakdown/SKILL.md:98`'s routing sentence recommending `/autopilot`
    "for unattended execution of peripheral tasks" is reworded to
    recommend `/drain` for queue/unattended work and `/build` (optionally
    `/goal`-bounded) for a single task.
- **R5**: `docs/human-gates.md` is corrected, not just reworded:
  - Its opening count ("Four skills carry `disable-model-invocation` —
    `/build`, `/autopilot`, `/drain`, `/evals`") becomes "Three skills ...
    `/build`, `/drain`, `/evals`".
  - Reason 2's "`/autopilot` and `/drain` open with ... a classification
    gate" becomes "`/build`'s bounded mode and `/drain`".
  - Reason 5's "The gated five" (or wherever a stale count/list appears)
    is corrected to match the new count of three.
- **R6**: Every reference to `/autopilot` across the **whole repo** is
  updated or removed — the verifying grep is
  `grep -rln '\bautopilot\b' .claude/ docs/ CLAUDE.md .claude-plugin/`,
  not a narrower subset. Known hits beyond SKILL.md/reference.md/
  human-gates.md, confirmed present today: `docs/external-playbooks.md`
  (the `/drain`-and-`/autopilot` worker-prompt hardening clause, and a
  citation pointer to autopilot's walk-away contract),
  `docs/decisions/orchestrator-context.md`,
  `docs/decisions/orchestration.md`, `docs/memory/
  unattended-worker-tool-limits.md`, `docs/memory/
  worktree-base-tracking-ref.md`, `docs/memory/
  skill-retirement-checklist.md`, `.claude/skills/fleet/SKILL.md` (its
  frontmatter description's trigger phrase "watch a /drain or /autopilot
  dispatch," and a body mention), `.claude/skills/gate/reference.md`
  ("workers (drain/autopilot dispatch, and the verifier)"), and
  `CLAUDE.md`'s own execution-stages doctrine line ("Execution stages
  (`/build`, `/autopilot`, `/drain`, `/evals`) keep
  `disable-model-invocation: true`" — becomes "`/build`, `/drain`,
  `/evals`"). Each is updated to describe `/build`'s bounded mode where it
  previously described `/autopilot`. **Exempted**:
  files that are explicitly historical research dumps rather than living
  doctrine (e.g. `docs/orchestration-research-2026-07.md`) — these keep
  their `/autopilot` mentions as a record of what was researched at the
  time; list any file treated as exempt in the implementation's own
  evidence so the exemption is a visible decision, not a silent skip.
- **R7**: Per CLAUDE.md's mirroring convention, the equivalent change
  (autopilot's mirror deleted, its content folded into build's mirror)
  lands in `antigravity/.agents/skills/` in the same commit, if an
  `antigravity/.agents/skills/autopilot/` exists (confirm before
  implementation; antigravity's own human-gate model may differ, per
  antigravity/README.md's gotchas — fold in only what actually applies
  there).
- **R8**: `.claude-plugin/plugin.json`'s `version` is bumped.

## Out of scope

- Any change to `/drain`'s own mechanics — this spec only removes
  autopilot's redundant overlap with it and redirects docs, not `/drain`
  itself.
- Reworking `/build`'s unbounded (default) behavior.
- Migrating in-flight autopilot runs — none expected at merge time; flag
  rather than silently discard if one is found.
- Building any new code path in `/build` to parse a `--goal`/turn-cap
  argument — per Solution, `/goal` is a runtime feature applied *around*
  `/build`'s invocation, not a flag `/build` itself implements.

## Acceptance criteria

- [ ] `.claude/skills/autopilot/` does not exist.
- [ ] `.claude/skills/build/reference.md` exists and contains the six
      named sections (permissions template, `/goal` pattern, containment
      ladder, headless template, pre-cap baton, failure recovery) —
      diffed against the old
      `autopilot/reference.md` to confirm verbatim content, not a rewrite.
- [ ] `.claude/skills/build/SKILL.md` contains the classification gate and
      the two escalation triggers, plus a pointer to
      `build/reference.md`'s baton section.
- [ ] `onboard/SKILL.md` and `drain/reference.md` point at
      `build/reference.md`, not `autopilot/reference.md`.
- [ ] `gate/SKILL.md` and `breakdown/SKILL.md` close with the replacement
      `Next stage:`/routing text named in R4 — neither is left pointing
      at a deleted skill.
- [ ] `docs/human-gates.md` says "Three skills," lists exactly `/build`,
      `/drain`, `/evals`, and its reason-2/reason-5 text no longer says
      "gated five" or otherwise implies a fourth gated skill.
- [ ] `grep -rln '\bautopilot\b' .claude/ docs/ CLAUDE.md .claude-plugin/`
      returns only files explicitly listed as exempt in R6's evidence (if
      any) — every other hit has been updated.
- [ ] `antigravity/.agents/skills/autopilot/` does not exist (if it existed
      before this change), and `antigravity/.agents/skills/build/`
      reflects the equivalent fold-in (R7).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before.
- [ ] **Manual-pending** (not verifiable by an unattended worker, since
      `/build` is `disable-model-invocation`): a human wraps `/build`
      against a fixture task in `/goal "tests pass, or stop after 5
      turns"` and confirms it completes within the cap, following the
      classification gate and escalation triggers now documented in
      `build/SKILL.md` — recorded as evidence, not an automated check.

## Open questions

(none)
