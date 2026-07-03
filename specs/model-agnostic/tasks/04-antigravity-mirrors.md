# Task 04: Antigravity mirrors of the tier language

Status: pending
Depends on: 01, 02
Budget: 10 turns
Spec: ../SPEC.md (requirement R8)

## Goal

Mirror the tier vocabulary into the antigravity port so both sides of the
mirror speak the same abstraction: `antigravity/AGENTS.md` adopts the
"scout-tier" phrasing in its token-discipline section (mirroring task
02's wording, with Antigravity's Flash-class default inline), and
`antigravity/README.md`'s mapping table points at the new
`runtimes/antigravity.md` profile from task 01. The port's structure is
unchanged — profiles describe it, they don't replace it.

## Touch

- antigravity/AGENTS.md
- antigravity/README.md

## Steps

1. `antigravity/AGENTS.md`: rephrase its token-discipline section to use
   "scout-tier" verbatim, matching the tier phrasing adopted in
   `.claude/rules/token-discipline.md` by task 02 (Antigravity default:
   Flash-class model, named inline in parentheses).
2. `antigravity/README.md`: add a row to the mapping table pointing at
   `runtimes/antigravity.md`.
3. Do not restructure anything else in `antigravity/` (out of scope per
   the SPEC).
4. Do NOT bump `.claude-plugin/plugin.json` — the single batch version
   bump (R10) is owned by global task 99 in specs/review-fixes.

## Acceptance

- `grep -q "scout-tier" antigravity/AGENTS.md && grep -q "runtimes/antigravity.md" antigravity/README.md` → exit 0 (R8)
