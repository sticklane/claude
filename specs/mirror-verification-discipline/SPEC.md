# Mirror verification discipline: catch cross-reference drift the mechanical gates can't

Breakdown-ready: true
Priority: P2

## Problem

This session live-tested the `antigravity/` mirror through the real
Antigravity runtime and found several real gaps — stale `.claude/`-rooted
paths in docstrings and workflow files, an unmirrored security-relevant
script dependency, an inconsistent half-populated skill directory (full list
and fixes: `specs/antigravity-mirror-broken-refs/SPEC.md`). The existing
mechanical gate, `tests/test_antigravity_parity.sh` (spec
`antigravity-parity-gate`), is existence-only by its own design — it proves
every `.claude/` skill/agent name has *some* antigravity counterpart and
inspects nothing further. A second mechanical gate is planned
(`specs/codequality-antigravity-content-parity/SPEC.md`) but is explicitly
scoped to byte-diffing mirrored `.py` files — it excludes SKILL.md prose and
cross-references by design, since a mirror is a port, not a copy, and prose
legitimately diverges between runtimes.

Neither gate — existing or planned — can catch a reference that diverges in
a way that still "looks fine" on a diff: a path that resolves under one
runtime's directory layout but not another's, a script dependency mirrored in
content but never wired into the target runtime's own invocation path, a
skill directory that mirrors some but not all of its source files. These are
found only by exercising the mirror through its target runtime, which no
mechanical diff can substitute for. Nothing today tells an agent *when* to
do that exercise or what to check when it does — so the class of gap this
session found is very likely to recur, especially as the toolkit's mirror
commitments broaden (a VCS-agnostic rework and a possible Codex CLI port are
both in flight as sibling specs, per this session's check of `specs/` for
matching slugs — neither exists yet, so there is nothing to cross-reference
today, but the rule this spec adds should not need a rewrite when one lands).

## Solution

Add `.claude/rules/mirror-verification.md`, a new always-on rule sitting
alongside `quality-discipline.md`, `concurrent-sessions.md`,
`token-discipline.md`, and `untrusted-data.md` — matching their format
exactly (short unadorned H1, terse declarative prose, `##` subsections,
em-dashes, citations to specs/docs in parentheses rather than restated
inline). Scouting this session confirmed `.claude/rules/` files are never
enumerated anywhere (no manifest, no listing in AGENTS.md/CLAUDE.md/
plugin.json) — adding the file requires no companion wiring edit — and that
`antigravity/.agents/` has no `rules/` counterpart to mirror into, since
rules govern the operating agent's own conduct regardless of which runtime's
skills it happens to be touching, not a per-runtime artifact.

The rule states, generically (not Antigravity-specific — Antigravity is
named only as today's concrete instance, so a future VCS-agnostic or Codex
CLI mirror doesn't require rewriting it):

1. **Existence and content-diff gates prove structural conformance; they
   cannot prove semantic correctness.** A change touching a path with a
   mirrored counterpart in another runtime must verify the mirror's
   cross-references actually resolve under that runtime — not just that the
   mirror exists or byte-matches.
2. **Live-test-sweep cadence is spec/task-closure-triggered, not
   calendar-based.** Closing any spec or task that touches a mirrored skill
   is the checkpoint every workflow already passes through — a calendar
   cadence silently lapses without a scheduler to drive it. A periodic
   broader sweep across the whole mirror is a reasonable belt-and-suspenders
   addition, never the primary mechanism.
3. **Give unattended workers an explicit manual-pending escape.** Today's
   mirrored runtimes may have no scriptable harness at all — Antigravity's
   own runtime profile states it has no non-interactive command template,
   since its Agent Manager launches agents rather than accepting CLI
   invocations (`runtimes/antigravity.md`) — so the verification step is
   inherently manual/interactive. Per
   `docs/memory/unattended-worker-tool-limits.md`, a drained/unattended
   worker gets an explicit manual-pending path with the reason stated, never
   a check it structurally cannot pass.
4. Cross-references the three sibling specs by name without restating their
   content: `antigravity-parity-gate` (the existence gate),
   `codequality-antigravity-content-parity` (the planned byte-diff gate),
   and `antigravity-mirror-broken-refs` (this session's found-gaps sweep,
   which is itself the worked proof that this class of gap gets past both
   mechanical gates).

## Requirements

R1. `.claude/rules/mirror-verification.md` exists and opens with a short
    H1 title and unadorned prose (no `## Problem`/`## Solution` spec-style
    headers) — matching the four sibling rules files' structure.

R2. The file contains an explicit checklist-style statement that a change
    touching a mirrored path must verify the mirror's cross-references
    resolve, phrased generically (not restricted to Antigravity or
    `.claude/skills/` alone).

R3. The file states the spec/task-closure-triggered cadence for live-test
    sweeps as the primary mechanism, with an optional periodic sweep noted
    as secondary — not the reverse — and names calendar cadence explicitly
    as the rejected alternative.

R4. The file gives drained/unattended workers an explicit manual-pending
    escape for the interactive-verification step and cites
    `docs/memory/unattended-worker-tool-limits.md` for the pattern.

R5. The file cross-references `antigravity-parity-gate`,
    `codequality-antigravity-content-parity`, and
    `antigravity-mirror-broken-refs` by spec slug, and cites
    `runtimes/antigravity.md` for the no-CLI fact — each as a parenthetical
    citation, never restating their content.

R6. Every runtime-specific term in the file (`Antigravity`, `.claude/skills`)
    appears only inside a citation or a concrete-example aside — the rule's
    imperative sentences (the "must verify" / cadence statements) use
    generic mirror language so a future mirrored runtime needs no rewrite.

## Out of scope

- Building the content-diff mechanical gate itself — that is
  `codequality-antigravity-content-parity`'s job.
- Fixing today's known antigravity gaps — that is
  `antigravity-mirror-broken-refs`'s job, already done this session.
- Adding a `rules/` mirror directory under `antigravity/.agents/` — scouting
  this session confirmed none exists and none is needed; rules aren't a
  per-runtime mirrored artifact.
- Running a fresh live/interactive Antigravity Agent Manager session as part
  of this task's acceptance — no scriptable harness exists (R4), and this
  session's `antigravity-mirror-broken-refs` sweep already stands as the
  worked proof-of-concept that the rule addresses a real, previously-missed
  gap class.
- Adding a cross-link to this rule from CLAUDE.md's authoring-conventions
  list — optional, may be worth a follow-up, but not required since rules
  files are never enumerated anywhere (confirmed by scouting; nothing breaks
  by omitting it).

## Acceptance criteria

- [ ] `test -f .claude/rules/mirror-verification.md` exits 0.
- [ ] `grep -qi "cross-reference" .claude/rules/mirror-verification.md &&
      grep -qi "resolve" .claude/rules/mirror-verification.md` — the
      checklist statement (R2) is present.
- [ ] `grep -qi "closing" .claude/rules/mirror-verification.md &&
      grep -qi "calendar" .claude/rules/mirror-verification.md` — the
      spec/task-closure cadence (R3) is stated, with calendar cadence
      named as the rejected alternative.
- [ ] `grep -q "unattended-worker-tool-limits" .claude/rules/mirror-verification.md`
      — the manual-pending escape (R4) cites the existing memory doc.
- [ ] For each of `antigravity-parity-gate`, `codequality-antigravity-content-parity`,
      `antigravity-mirror-broken-refs`: `grep -q "<slug>" .claude/rules/mirror-verification.md`
      finds the citation, AND `test -f specs/<slug>/SPEC.md` confirms the
      cited spec actually exists (R5) — no dangling cross-reference.
- [ ] `grep -q "runtimes/antigravity.md" .claude/rules/mirror-verification.md`
      and `test -f runtimes/antigravity.md` both pass (R5).
- [ ] Manual read-through (or a `critic`/`verifier` pass) confirms every
      `Antigravity`/`.claude/skills`-specific mention sits inside a citation
      or example aside, not an imperative sentence (R6) — this is a
      judgment check, not grep-able, so name it explicitly rather than
      skip it.
- [ ] End-to-end: a side-by-side read of `.claude/rules/mirror-verification.md`
      against `.claude/rules/quality-discipline.md` confirms matching tone —
      H1 title, terse declarative prose, `##` subsections, em-dashes,
      parenthetical citations (R1) — and confirms closure-triggered cadence
      is stated as primary with periodic sweeps as secondary, not the
      reverse (R3) — as a human or `critic` would judge it, not a
      mechanical diff.

## Open questions

(none)

## Parallelization

Single task (01) covers the whole spec — one file, interlocking
requirements (R1–R6 all describe the same document), no independent
sub-slices. No concurrent-safe groups; task 01 runs solo.
