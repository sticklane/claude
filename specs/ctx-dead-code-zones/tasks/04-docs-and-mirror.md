# Task 04: R4 — skill docs + antigravity mirror + CUJ citation

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: blocked
Unblock: run: ls specs/ctx-skill-token-doctrine/tasks/*.md >/dev/null 2>&1 && { for f in specs/ctx-skill-token-doctrine/tasks/*.md; do grep -q '^Status: done' "$f" || echo "not done: $f"; done; } || echo "ctx-skill-token-doctrine not broken down yet"
Depends on: 03
Priority: P3
Budget: 8 turns
Spec: ../SPEC.md (R4)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md, docs/guides/ctx-cujs.md

## Goal

The ctx skill documents the new zone commands and rewrites its dead-tree scope
caution to "zone dead trees, don't exclude them" (superseding the attic/vendored
"exclude via `.ctxignore`" caution that ctx-skill-token-doctrine R7 authored).
The antigravity mirror carries the same content (same commit), and the CUJ
guide's DEDUP / DEAD CODE section cites this spec.

## Blocked rationale (cross-spec landing-order registry)

R4 holds SLOT 5 of the SKILL.md editor registry in ctx-skill-token-doctrine's
`## Landing order`: it rewrites the attic caution AUTHORED BY that spec's R7
(slot 1). Until R7 lands, there is no attic/vendored caution to rewrite, and
concurrent edits to the same SKILL.md collide. `ctx-skill-token-doctrine` is not
yet broken down, so the `Unblock: run:` prints a "not broken down yet" line
(non-empty → still blocked) until that spec exists and all its tasks are `done`.
Nothing auto-flips this: `/drain` does not re-run `Unblock: run:` on a
pre-existing blocked task, so a human or later session re-checks and flips the
status to `pending` once the sibling is done and R7's caution is present in
`.claude/skills/ctx/SKILL.md`.

## Touch

Edit only the ctx skill files and the CUJ guide. The antigravity SKILL.md is a
paraphrased port, NOT byte-identical — carry the concepts and the exact command
strings, but do not force a `diff`-clean copy (see
docs/memory/workboard-mirror-verbatim.md). Do NOT bump `plugin.json` — this
touches a skill's prose, not agent enumeration; but IF the plugin version bump
convention applies to ctx skill behavior docs, add `.claude-plugin/plugin.json`
to Touch before editing and bump `version`.

## Steps

1. In `.claude/skills/ctx/SKILL.md`: add the zone commands to the query-command
   table / relevant section — the exact strings the `doc_conformance` gate will
   verify against the binary: `ctx refs <sym> --zone <label>`,
   `ctx refs <sym> --live-only`, `ctx map --zone <label>`,
   `ctx map --live-only`. Reference `.ctxzones` alongside the existing
   `.ctxignore` "Optional wiring" bullet.
2. Rewrite the scope caution for dead/vendored trees to say zone them (keep
   them indexed, tag results, filter per-query) rather than exclude them via
   `.ctxignore` — replacing R7's attic caution.
3. Mirror the same content into `antigravity/.agents/skills/ctx/SKILL.md`
   (paraphrased port; same command strings).
4. Add a one-line citation of this spec to the DEDUP / DEAD CODE section of
   `docs/guides/ctx-cujs.md`.
5. Run the check script green.

## Acceptance

- [ ] `grep -c 'live-only' .claude/skills/ctx/SKILL.md` → ≥ 1 and
      `grep -c 'live-only' antigravity/.agents/skills/ctx/SKILL.md` → ≥ 1
      (both legs document the flag).
- [ ] `grep -c 'ctxzones' .claude/skills/ctx/SKILL.md` → ≥ 1.
- [ ] `grep -ci 'ctx-dead-code-zones' docs/guides/ctx-cujs.md` → ≥ 1
      (CUJ DEDUP/DEAD CODE section cites this spec).
- [ ] `cd context-tree && cargo test --test doc_conformance` → passes (every
      documented `ctx … --flag` resolves in the binary; requires task 03's flags
      to have landed).
- [ ] `cd context-tree && bash scripts/check.sh` → exits 0.
