# Task 01: Add the mirror-verification always-on rule

Status: pending
Depends on: none
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R6)
Touch: .claude/rules/mirror-verification.md

## Goal

`.claude/rules/mirror-verification.md` exists, matching the format of its
four siblings (`quality-discipline.md`, `concurrent-sessions.md`,
`token-discipline.md`, `untrusted-data.md`), and states — generically, not
Antigravity-specific — that: (1) existence/content-diff gates can't prove
semantic correctness, so a change touching a mirrored path must verify the
mirror's cross-references actually resolve under the target runtime; (2)
the live-test-sweep cadence is spec/task-closure-triggered as the primary
mechanism, with periodic sweeps as an optional secondary, explicitly
rejecting calendar cadence as primary; (3) unattended/drained workers get an
explicit manual-pending escape for this interactive step. All
Antigravity-specific and `.claude/skills`-specific terms sit only inside
citations or example asides, never inside an imperative sentence.

## Touch

Only `.claude/rules/mirror-verification.md` is created. This spec is
out-of-scope for: building the content-diff gate itself
(`codequality-antigravity-content-parity`), fixing known antigravity gaps
(`antigravity-mirror-broken-refs`, already done), adding a `rules/` mirror
under `antigravity/.agents/` (none needed — rules aren't per-runtime), or
wiring a cross-link from CLAUDE.md's authoring-conventions list (optional,
not required — confirmed no manifest enumerates `.claude/rules/` files).
Do not edit any sibling rules file, AGENTS.md, CLAUDE.md, or plugin.json.

## Steps

1. Read `.claude/rules/quality-discipline.md` and
   `.claude/rules/concurrent-sessions.md` to confirm the exact format: short
   unadorned H1, terse declarative prose, `##` subsections, em-dashes,
   parenthetical citations rather than restated content.
2. Draft `.claude/rules/mirror-verification.md` with an H1 title and 2–4 `##`
   subsections covering, generically:
   - Existence/content-diff gates prove structural conformance only; a
     change touching a path with a mirrored counterpart in another runtime
     must verify the mirror's cross-references resolve under that runtime.
   - Live-test-sweep cadence: triggered by closing any spec/task that
     touches a mirrored skill (primary), with an optional periodic
     broader sweep as secondary belt-and-suspenders — name calendar
     cadence explicitly as the rejected alternative.
   - Manual-pending escape: unattended/drained workers get an explicit
     manual-pending path with the reason stated when no scriptable harness
     exists, citing `docs/memory/unattended-worker-tool-limits.md`.
   - Citations (parenthetical, not restated): `antigravity-parity-gate`,
     `codequality-antigravity-content-parity`,
     `antigravity-mirror-broken-refs` (spec slugs), and
     `runtimes/antigravity.md` (source of the no-CLI fact). Antigravity and
     `.claude/skills` may appear only inside these citations or a concrete
     example aside — never in an imperative ("must verify" / cadence)
     sentence.
3. Run every grep-able acceptance check below and fix any miss.
4. Do a manual read-through (or dispatch one `critic` or `verifier` agent)
   confirming: (a) every Antigravity/`.claude/skills` mention sits inside a
   citation or example aside, not an imperative sentence (R6); (b) tone
   matches `quality-discipline.md` side by side (R1); (c) closure-triggered
   cadence reads as primary with periodic sweep as secondary, not reversed
   (R3).

## Acceptance

- [ ] `test -f .claude/rules/mirror-verification.md` → exits 0
- [ ] `grep -qi "cross-reference" .claude/rules/mirror-verification.md && grep -qi "resolve" .claude/rules/mirror-verification.md` → both match (R2)
- [ ] `grep -qi "closing" .claude/rules/mirror-verification.md && grep -qi "calendar" .claude/rules/mirror-verification.md` → both match (R3)
- [ ] `grep -q "unattended-worker-tool-limits" .claude/rules/mirror-verification.md` → matches (R4)
- [ ] `grep -q "antigravity-parity-gate" .claude/rules/mirror-verification.md && test -f specs/antigravity-parity-gate/SPEC.md` → both pass (R5)
- [ ] `grep -q "codequality-antigravity-content-parity" .claude/rules/mirror-verification.md && test -f specs/codequality-antigravity-content-parity/SPEC.md` → both pass (R5)
- [ ] `grep -q "antigravity-mirror-broken-refs" .claude/rules/mirror-verification.md && test -f specs/antigravity-mirror-broken-refs/SPEC.md` → both pass (R5)
- [ ] `grep -q "runtimes/antigravity.md" .claude/rules/mirror-verification.md && test -f runtimes/antigravity.md` → both pass (R5)
- [ ] Manual read-through (or a `critic`/`verifier` agent pass) confirms R6 (every runtime-specific mention is inside a citation/example aside, not an imperative sentence) and R1/R3 tone-and-ordering match — judgment check, not grep-able; do not skip it.
