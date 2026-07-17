# Task 02: Mirror the check into antigravity, bump plugin version, seed the manifest

Status: done
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirements R4, R5, R6)
Touch: antigravity/.agents/skills/idea/SKILL.md, .claude-plugin/plugin.json, tests/mirror-procedure-manifest.txt

## Goal

The antigravity mirror (`antigravity/.agents/skills/idea/SKILL.md`, its own
step 3 "Write the spec") carries the same procedural addition Task 01 made
to `.claude/skills/idea/SKILL.md` — same steps, same order, same stated
conditions, per `.claude/rules/mirror-procedure-discipline.md` (cited, not
restated: this is a port, so prose may differ, but the sequence of
sub-checks must not). `.claude-plugin/plugin.json`'s `version` is bumped.
`tests/mirror-procedure-manifest.txt` gets one new line anchoring the
"self-referential" phrase for this file pair, so
`tests/test_mirror_procedure_coverage.sh` actually exercises this change
instead of passing vacuously.

## Touch

Only the three paths listed in the header. Do not re-edit
`.claude/skills/idea/SKILL.md` (Task 01's landed content is the source of
truth to mirror from — read it, don't second-guess its wording).

## Steps

1. Read the current `.claude/skills/idea/SKILL.md` step 3 in full (Task 01
   already landed it) to see the exact new prose to mirror.
2. Read `antigravity/.agents/skills/idea/SKILL.md`'s own step 3 ("Write the
   spec", around lines 41–68) to find its equivalent insertion point —
   this mirror is a paraphrased port (per
   docs/memory/workboard-mirror-verbatim.md's port-not-copy convention:
   only workboard's two `.py` files are byte-identical across trees), so
   match the _procedure_ — the same sub-checks in the same order, applied
   at the same point in the same step — not the exact prose. Confirm
   today's absence of both anchor phrases first:
   - `grep -c "anchored-acceptance-criteria" antigravity/.agents/skills/idea/SKILL.md`
   - `grep -c "self-referential" antigravity/.agents/skills/idea/SKILL.md`
     Both must print `0` before you edit.
3. Add the mirrored prose to the antigravity step 3, adapted to that file's
   own voice/cross-reference conventions where needed (e.g. its own
   citation style), but preserving: the citation of
   `docs/memory/anchored-acceptance-criteria.md` by path, the "apply before
   writing into the SPEC.md, not deferred to /breakdown" framing, the
   current-on-disk-state grep/count check, the self-referential-trap
   rejection (using the literal word "self-referential"), and the inline
   outcome-recording instruction — same order as the `.claude/` source.
4. Bump `.claude-plugin/plugin.json`'s `version` field up from its value at
   this task's own base commit (check the current value first with
   `grep '"version"' .claude-plugin/plugin.json`; increment the patch
   component unless the repo's own convention for this file suggests
   otherwise).
5. Append one new line to `tests/mirror-procedure-manifest.txt` (respecting
   its existing `<source>|<mirror>|<phrase>` format — see any existing line
   for the pattern, e.g. the current `.claude/skills/idea/SKILL.md|antigravity/.agents/skills/idea/SKILL.md|one focused question each` entry):

   ```
   .claude/skills/idea/SKILL.md|antigravity/.agents/skills/idea/SKILL.md|self-referential
   ```

   Add it as a new line in the manifest (comment lines and blank lines are
   skipped by the parser; place it near the existing idea-pair line for
   readability, but any line position is functionally equivalent).

## Acceptance

- [x] `grep -c "anchored-acceptance-criteria" antigravity/.agents/skills/idea/SKILL.md` → 1 or more. — 2 — verifier PASS (2026-07-16 sweep)
- [x] `grep -c "self-referential" antigravity/.agents/skills/idea/SKILL.md` → 1 or more. — 1 — verifier PASS (2026-07-16 sweep)
- [x] `grep -Fc '.claude/skills/idea/SKILL.md|antigravity/.agents/skills/idea/SKILL.md|self-referential' tests/mirror-procedure-manifest.txt` → 1 or more. — 1 — verifier PASS (2026-07-16 sweep)
- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (with the new
      manifest line in place, this now actually fails if the antigravity
      mirror lacks the phrase — confirm it passes for real, not vacuously,
      by temporarily noting the check depends on both this task's edit AND
      Task 01's). — exit 0, confirmed non-vacuous — verifier PASS (2026-07-16 sweep)
- [x] This task's own commit modifies `.claude-plugin/plugin.json`'s
      version line: `git show <this-commit> -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` → match. — 0.9.3 → 0.9.4 — verifier PASS (2026-07-16 sweep)
- [x] Re-read the antigravity step-3 edit once and confirm by inspection it
      states the same three sub-checks (current-state grep,
      self-referential rejection, inline outcome recording) in the same
      order as the `.claude/` edit from Task 01. — confirmed, same order — verifier PASS (2026-07-16 sweep)

## Evidence

Merged `task/02-mirror-and-close` (commit f76d057) via merge commit
`58e0daa`. All 6 acceptance checks pass. `./specs/status.sh`, `claude
plugin validate .`, and `bash tests/test_mirror_procedure_coverage.sh`
green. Full `tests/test_*.sh` suite green except the same pre-existing
`test_antigravity_parity.sh`/`test_codex_parity.sh` qa-sweep-mirror-gap
failures noted on earlier tasks, unaffected by this change. This closes
the spec: 2/2 tasks done.
