# idea: self-chain into /design instead of a printed pointer

Priority: P1

## Problem

`/idea`'s step 5 (`.claude/skills/idea/SKILL.md:89-95`) currently has two
fallback triggers that stop the pipeline and print a pointer instead of
self-chaining: (a) a technology/architecture choice is still open, or (b)
other non-interactive/scope-limited reasons. Case (a) is unnecessary
friction: `/design` is not `disable-model-invocation` (confirmed — only
`/build`, `/drain`, `/autopilot`, `/evals` carry that flag per this repo's
CLAUDE.md authoring conventions), so nothing prevents `/idea` from invoking
it the same way it already self-chains into `/breakdown`. Today, every
`/idea` session that surfaces an open design choice dead-ends with a
printed command the user has to type themselves in the same or a new
session — pure ceremony for a skill that's already safe to invoke
automatically.

## Solution

**Reposition, don't just reword, the trigger.** Today's "technology/
architecture choice is still open" fallback lives in step 5, which only
runs after step 4's critique-fix loop — but this spec requires design to
run *before* any `/critique` skill invocation, and a spec whose Open
Questions still names an unresolved architecture choice is exactly the
kind of thing critique would flag without being able to "fix" by editing
prose. So the check moves to a new step, inserted between today's step 3
(write the spec) and step 4 (the `/critique` skill invocation —
`idea/SKILL.md` invokes the `/critique` *skill*, not the `critic` agent
directly, specifically so the pass gets `/critique`'s
`Breakdown-ready: true` stamp; this spec never changes that): immediately
after the spec is first written, before the first `/critique` invocation,
check whether `## Open questions` names a technology/architecture choice.
The identical check re-runs after every subsequent `/critique` pass inside
step 4's fix loop too — this is what covers the case where a critic
finding causes the fix wave to add a new open-architecture-choice entry to
`## Open questions` that wasn't there right after step 3: there is no
separate "did a critic finding reveal a choice" judgment call to make: the
gate is always "does `## Open questions` currently name a technology/
architecture choice," re-evaluated at two points (right after step 3, and
after each step-4 fix wave) rather than two different mechanisms.

- **Technology/architecture choice open (at either check point above)** →
  self-chain: announce it in one line, then invoke
  `/design specs/<slug>/SPEC.md` via the Skill tool (same synchronous,
  in-session mechanism already used for `/breakdown` — not a
  background/detached agent). `/design` records its decision directly
  into the SPEC.md (Solution paragraph, deleted Open Questions entry,
  rejected-options appendix — per `.claude/skills/design/SKILL.md` step
  3) and prints its own closing `Next stage: /breakdown ...
  (human-launched...)` line — `/idea`'s flow **ignores that line** (it's
  written for design's other, human-launched entry point) and simply
  resumes step 4 (proceeds to `/critique` if this was the post-step-3
  check, or continues the fix loop without restarting from step 3 if this
  was a mid-loop check) once control returns. This self-chain fires at
  most once per `/idea` session (see R5) — a second occurrence instead
  takes the printed-pointer fallback (R4).
- **Everything else** (user asked for the spec only, non-interactive doubt
  in the interview) → unchanged: today's step 5 printed-pointer fallback.

This is a same-spec, in-place resolution sub-step, not a hand-off to a
downstream pipeline stage — it doesn't need the artifact to have already
passed critique's adversarial gate first (CLAUDE.md's self-chain
condition (a) governs *hand-offs* between stages, e.g. idea→breakdown;
resolving an open design question while still writing the same spec is
what step 3 already does when the interview itself resolves a simpler
tradeoff, just now extended to the cases that need real investigation
instead of conversation).

Step 5's existing `/design` fallback text
(`.claude/skills/idea/SKILL.md`'s current lines ~99-100, "or, on the
`/design` fallback, `Next stage: /design ... (human-launched)`") is
removed — nothing reaches step 5 needing that text anymore, since the
technology-choice case is now fully handled earlier. Step 5 keeps only its
non-technology fallback and its existing `/breakdown` self-chain.

## Requirements

- **R1**: `.claude/skills/idea/SKILL.md` gains a new step, inserted
  between today's step 3 ("Write the spec") and step 4 (the `/critique`
  skill invocation), that runs immediately after the spec is first
  written, before the first `/critique` invocation: if `## Open
  questions` names a technology/architecture choice, announce
  ("`/design` needed for <the open choice>, chaining now") in one line,
  then invoke the Skill tool for `design` with argument
  `specs/<slug>/SPEC.md`, in the same session, synchronously (blocking
  until it returns) — the identical self-chain mechanism already used for
  `/breakdown`, not `run_in_background`/a detached Agent-tool dispatch.
  Step 5 ("Hand off") is **not** where this trigger lives — step 5 only
  runs after step 4's critique loop reaches READY, which is too late for
  a choice the spec's Open Questions section itself declares unresolved.
- **R1b (mid-loop case)**: The SAME check R1 performs (`## Open
  questions` names a technology/architecture choice) re-runs after every
  `/critique` fix wave inside step 4's loop, not only once right after
  step 3. There is no separate detection mechanism for "a critic finding
  revealed a choice" — a fix wave that adds such an entry to `## Open
  questions` is caught by this re-run of R1's own file check, which is
  what interrupts the fix loop rather than requiring it to reach a READY
  it structurally cannot reach on its own by editing prose. Subject to
  R5's once-per-session cap.
- **R2**: After the self-chained `/design` invocation returns (from
  either R1's initial check or an R1b re-check), `/idea`'s flow
  discards/ignores any "Next stage: ..." text `/design` printed and
  proceeds directly to step 4's `/critique` invocation (R1 case) or
  continues the fix loop without restarting from step 3 (R1b case) —
  `/design`'s own closing line is written for its human-launched entry
  point and must not be surfaced to the user as this flow's next
  instruction.
- **R3**: Step 5's non-technology fallback reasons (user asked for spec
  only; non-interactive doubt) are unchanged — they still stop with the
  printed pointer, unaffected by R1/R1b/R2.
- **R4**: If `/design`'s own invocation leaves the SPEC.md's `## Open
  questions` section still non-empty (e.g. it could not resolve the
  choice, or surfaced a new one), `/idea` takes the printed-pointer
  fallback (the same one used for "user asked for spec only") instead of
  proceeding — R1 case: does not proceed to the first `/critique`
  invocation; R1b case: aborts the fix loop rather than continuing it —
  since an unresolved Open Questions entry already means `/breakdown`
  would refuse the spec (per `design/SKILL.md`'s own note: "`/breakdown`
  refuses any spec with unresolved entries there"). This same
  printed-pointer fallback also applies to R5's second-occurrence case
  below.
- **R5**: This is a same-session, single self-chain — `/idea` invokes
  `/design` at most once per idea session, whether triggered by R1's
  initial check or an R1b re-check (not both in the same run). If the
  once-per-session budget is already spent and `## Open questions` names
  a technology/architecture choice again (a genuinely new one, or the
  same one `/design` failed to resolve), `/idea` does NOT invoke
  `/design` a second time — it takes R4's printed-pointer fallback
  instead. If `/design` itself determines it needs another round
  (unusual), that is `/design`'s own concern, not handled by re-invoking
  it a second time from `/idea`.
- **R6**: `.claude-plugin/plugin.json`'s `version` is bumped as part of
  this change, per CLAUDE.md's "bump version whenever skill behavior
  changes" convention — this is a behavior change to
  `.claude/skills/idea/SKILL.md`.

## Out of scope

- Any change to `/design`'s own internals (`.claude/skills/design/SKILL.md`
  is untouched).
- A detached/background dispatch of `/design` — explicitly rejected in
  favor of the existing synchronous self-chain pattern (R1).
- Self-chaining `/design` from anywhere other than `/idea`'s new step
  (e.g. from `/breakdown` or `/critique` encountering an open choice) —
  out of scope for this spec.
- **No antigravity mirror for this change.** `antigravity/README.md`'s own
  translation table documents that skill self-chaining is deliberately
  **not ported**: "Skill self-chaining (/idea invokes /breakdown via the
  Skill tool) | Not ported — workflows are human-launched in the Agent
  Manager, so the port keeps printed pointers between stages." This
  spec's entire change is adding a new self-chain, so by that same
  existing, documented policy it does not port. The file this actually
  affects is `antigravity/.agents/skills/idea/SKILL.md` (its own step 5,
  "Hand off," carries the same technology-choice printed-pointer text as
  the `.claude/` version, per that skill body being the mirrored port) —
  **not** `antigravity/.agents/workflows/idea.md` (a 5-line wrapper that
  just says "follow .agents/skills/idea/SKILL.md exactly"; it contains no
  technology-choice branch to begin with, so exempting it would be
  meaningless). `antigravity/.agents/skills/idea/SKILL.md`'s step 5
  printed pointer stays exactly as-is, unchanged by this spec.

## Acceptance criteria

- [ ] `.claude/skills/idea/SKILL.md` has a new step between the
      spec-writing step and the `/critique`-invocation step (today
      numbered 3 and 4 — whether the implementer renumbers the tail steps
      or inserts an unnumbered step between them is an implementation
      choice this criterion doesn't pin) that reads as a self-chain
      instruction (announce + invoke `design` via the Skill tool) gated on
      `## Open questions` naming a technology/architecture choice. The
      hand-off step (today's step 5, whatever its number becomes after
      insertion) no longer contains any technology-choice `/design` branch
      (printed-pointer or otherwise) — identify it by its content
      ("Hand off" / the `/breakdown` self-chain step), not by a hardcoded
      number.
- [ ] The non-technology fallback (spec-only ask / non-interactive doubt)
      text is still present and unchanged, in that same hand-off step.
- [ ] The new step's instructions state explicitly that the SAME
      `## Open questions` check re-runs after every fix wave inside the
      `/critique` loop (not only once, immediately after the spec is
      first written) — grep/read check on the SKILL.md prose itself, not
      a live multi-turn run: the text must not describe two different
      detection mechanisms (a file check vs. a semantic read of critic
      findings).
- [ ] The new step's instructions state the once-per-session cap (R5) and
      its resolution: a second occurrence of an open technology/
      architecture choice after `/design` has already run once in this
      session takes the printed-pointer fallback, never a second `/design`
      invocation — inspectable directly on the SKILL.md prose.
- [ ] `antigravity/.agents/skills/idea/SKILL.md`'s step 5 ("Hand off")
      printed-pointer text for the technology-choice case is unchanged by
      this spec (per Out of scope's antigravity note) —
      `antigravity/.agents/workflows/idea.md` (the thin wrapper, which
      never contained this branch) is irrelevant to this check.
- [ ] `git diff <base-commit> -- .claude-plugin/plugin.json | grep
      '"version"'` shows the version increased from its base-commit value
      (R6).
- [ ] A fresh agent running `/idea` end-to-end on a test idea whose
      interview surfaces a genuine open library/framework choice: the
      transcript shows a `design` Skill-tool invocation with
      `specs/<slug>/SPEC.md` as its argument, occurring before the first
      `/critique` skill invocation.
- [ ] Same run: after `design` completes and the SPEC.md's `## Open
      questions` section is empty, the flow proceeds to invoke the
      `/critique` skill — it does not print `design`'s "Next stage:
      /breakdown..." line to the user as an instruction to run manually.
- [ ] The new step's instructions state R4's fallback explicitly for BOTH
      entry points (R1: does not proceed to the first `/critique`
      invocation; R1b: aborts the fix loop rather than continuing it) when
      `/design` leaves `## Open questions` non-empty — inspectable
      directly on the SKILL.md prose.
- [ ] A fixture where the self-chained `design` invocation returns with
      `## Open questions` still non-empty: the flow stops with the
      existing printed-pointer fallback instead of proceeding to
      `/critique`.
- [ ] A fresh agent running `/idea` on a test idea with NO open
      architecture choice: behavior is unchanged from today (`/critique`
      runs directly, no `design` invocation occurs).

## Open questions

(none)
