# Task 02: author-side principle in every runtime's conventions doc

Status: in-progress
Depends on: 01
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R3, R4)
Touch: CLAUDE.md, antigravity/AGENTS.md, codex/AGENTS.md

## Goal

The always-loaded author-side principle binds agents on all three runtimes:
added to CLAUDE.md's `## Authoring conventions` (Claude), to
`antigravity/AGENTS.md` in its own register (Antigravity/Gemini), and made
explicitly in-scope for `codex/AGENTS.md` (Codex/GPT) — whose deferral to
Antigravity currently covers only pipeline orientation, so it is widened to
name authoring/output conventions, or the principle is stated inline. Each
carries the canonical literal `lead with the result, not narrated intent`
plus the cash-out and known-number clauses and a trailing status-telegraphy
carve-out clause, and cites the reference.md agentic-register subsection
(task 01) for detail rather than restating it.

## Touch

Edit only CLAUDE.md, antigravity/AGENTS.md, codex/AGENTS.md. Do NOT re-edit
reference.md, the mirror, the manifest, or plugin.json — those are task 01's.
Depends on task 01 because the citation targets the subsection task 01
finalizes. The authored prose must itself avoid meta-discourse and varnish.

## Steps

1. In CLAUDE.md's `## Authoring conventions`, add one bullet with the
   canonical literal `lead with the result, not narrated intent` plus "replace
   a quality adjective with the checkable fact; state a known number rather
   than a `~` approximation", a trailing clause preserving terse factual
   status lines (so an agent with only conventions loaded does not
   over-suppress telegraphy), and a citation to reference.md's agentic-register
   subsection.
2. Add the same principle to `antigravity/AGENTS.md` under its most fitting
   existing heading (quality/output register), same canonical literal and
   trailing carve-out clause, citing the subsection via an antigravity-valid or
   runtime-neutral path — never a `.claude/` path.
3. Edit `codex/AGENTS.md` so the principle binds Codex: widen its deferral
   clause to explicitly name output/authoring conventions as inherited from
   `antigravity/AGENTS.md`, or state the principle inline. Do not rely on the
   existing pipeline-orientation-only deferral.
4. Run the acceptance commands.

## Acceptance

- [ ] `test $(grep -c 'lead with the result, not narrated intent' CLAUDE.md) -eq 1` and `awk '/lead with the result, not narrated intent/{p=1} p&&/reference.md/{print;exit}' CLAUDE.md | grep -q reference.md` → Claude bullet present + cites reference
- [ ] `grep -Ei 'lead with the result, not narrated intent' CLAUDE.md | grep -Eqi 'status|telegraphy|factual'` → carve-out clause present on the bullet
- [ ] `test $(grep -c 'lead with the result, not narrated intent' antigravity/AGENTS.md) -eq 1` → Antigravity bound
- [ ] `! grep -A1 'lead with the result, not narrated intent' antigravity/AGENTS.md | grep -q '\.claude/'` → antigravity citation uses no `.claude/` path
- [ ] `grep -Eqi 'authoring convention|output convention|lead with the result, not narrated intent' codex/AGENTS.md` → Codex bound, not silently skipped
