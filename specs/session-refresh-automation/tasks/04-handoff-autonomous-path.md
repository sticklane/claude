# Task 04: Handoff autonomous refresh path

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/handoff/SKILL.md, antigravity/.agents/workflows/handoff.md, antigravity/.agents/skills/handoff/SKILL.md, .claude-plugin/plugin.json

## Goal

/handoff documents the autonomous refresh-over-carry path: a session
refreshing under the hook's directive writes the standard handoff file,
surfaces the resume pointer where the restart will find it (next loop
firing, scheduled fresh session, or attended parent), and ends its turn —
explicitly not spawning a detached continuation, citing the
token-discipline detachment policy. Both antigravity mirrors are updated
and the plugin version is bumped.

## Touch

The handoff skill, its two antigravity mirrors, and plugin.json only. Do
NOT touch `.claude/rules/` (task 01 owns the doctrine — cite it).

## Steps

1. Add the autonomous path to the skill body (keep the contract within
   the first 30 lines' reach per CLAUDE.md; the phrase
   "refresh-over-carry" must appear).
2. Port the same content to both antigravity mirrors — paraphrased port,
   not byte-copy (docs/memory/workboard-mirror-verbatim.md).
3. Bump `version` in `.claude-plugin/plugin.json` (skill behavior
   changed).

## Acceptance

- [x] `grep -ci 'refresh-over-carry' .claude/skills/handoff/SKILL.md` → ≥ 1 — verifier: returns 1 (evidence/04-handoff-autonomous-path.md)
- [x] `grep -ci 'token-discipline' .claude/skills/handoff/SKILL.md` → ≥ 1 (policy cited, not restated) — verifier: returns 2; skill cites the token-discipline "Session refresh"/"Awaited children" sections, does not restate them (evidence/04-handoff-autonomous-path.md)
- [x] `grep -ci 'refresh-over-carry' antigravity/.agents/workflows/handoff.md` → ≥ 1 AND `grep -ci 'refresh-over-carry' antigravity/.agents/skills/handoff/SKILL.md` → ≥ 1 (content-coverage check — mirrors are paraphrased ports, never diffed byte-for-byte) — verifier: 1 each, both antigravity-native paraphrase not byte-copies (evidence/04-handoff-autonomous-path.md)
- [x] `git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'` differs from `grep '"version"' .claude-plugin/plugin.json` — compared against this task's own base commit, never a hard-coded literal — verifier: base 0.8.54 → head 0.8.55 (evidence/04-handoff-autonomous-path.md)
- [x] `claude plugin validate .` → passes — verifier: ✔ Validation passed (evidence/04-handoff-autonomous-path.md)
