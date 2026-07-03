# Task 04: Antigravity mirrors of the tier language

Status: pending
Depends on: 01, 02, ../../chaining-antipatterns/tasks/03-antipattern-guards.md
Budget: 10 turns
Spec: ../SPEC.md (requirement R8)

## Goal

Mirror the tier vocabulary into the antigravity port so both sides of the
mirror speak the same abstraction: `antigravity/AGENTS.md` adopts the
"scout-tier" phrasing in its token-discipline section and mirrors the
four-rung ladder (mirroring task 02's wording, with Antigravity's
Flash-class default inline and its deep-tier/frontier-tier mapping per
`runtimes/antigravity.md`), and `antigravity/README.md`'s mapping table
points at the new `runtimes/antigravity.md` profile from task 01. The port's structure is
unchanged — profiles describe it, they don't replace it.

## Touch

- antigravity/AGENTS.md
- antigravity/README.md

## Steps

1. `antigravity/AGENTS.md`: rephrase its token-discipline section to use
   "scout-tier" verbatim and mirror the four-rung ladder adopted in
   `.claude/rules/token-discipline.md` by task 02 (Antigravity defaults
   inline in parentheses: Flash-class for scout-tier; for deep-tier and
   frontier-tier, the mapping `runtimes/antigravity.md` records —
   strongest available model, or "no distinct mapping — session model").
   Tier pins stay a Claude Code mechanism; the mirror states the ladder
   and Antigravity's mappings, not the `.claude/runtime.md` machinery.
2. `antigravity/README.md`: add a row to the mapping table pointing at
   `runtimes/antigravity.md`.
3. Do not restructure anything else in `antigravity/` (out of scope per
   the SPEC).
4. Do NOT bump `.claude-plugin/plugin.json` — the single batch version
   bump (R10) is owned by global task 99 in specs/review-fixes.

Note (R10): do NOT bump plugin.json here — specs/review-fixes task 99
owns the single combined batch bump; record the pre-implementation
version as evidence.

## Acceptance

- [ ] `grep -q "scout-tier" antigravity/AGENTS.md && grep -q "deep-tier" antigravity/AGENTS.md && grep -q "runtimes/antigravity.md" antigravity/README.md` → exit 0 (R8 — including the four-rung ladder mirror)
