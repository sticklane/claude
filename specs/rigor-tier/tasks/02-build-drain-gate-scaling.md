# Task 02: /build and /drain scale gates on Rigor: prototype, state the promotion rule

Status: done
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R4, R6, R8)
Touch: .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, antigravity/.agents/workflows/build.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/build/SKILL.md, codex/.agents/skills/drain/SKILL.md

## Goal

`/build` and `/drain` read a task's `Rigor:` header and scale gates at each
gate's real locus, exactly as SPEC.md's Solution section describes: on
`Rigor: prototype`, the /build procedure (attended, and drain's
attempt-1/relaunch workers, who run /build verbatim) skips TDD red-first
and its own verifier spawn, substituting a mechanical acceptance-command
run for the reported verdict; drain's orchestrator does the same
substitution only in the tournament path's per-candidate verifier
dispatch; the orchestrator's mechanical pre-merge gate is unchanged in
every case. Commit hygiene, the task's runnable acceptance criteria, and
the untrusted-data rules are never skipped. Both skills also state the
promotion rule in their own text (R6): prototype code never merges into a
`Rigor: production` spec's work without re-running the full gates —
promotion means flipping the header and treating the existing code as
untested input to a normal production task, not as done work. All four
mirrors (antigravity build/drain workflows, codex build/drain skills)
carry the equivalent behavior in the same commit.

## Touch

Do not touch `.claude/skills/idea/SKILL.md` or `.claude/skills/breakdown/SKILL.md`
— those belong to task 01. Do not touch `.claude/skills/list-specs/SKILL.md`
or `.claude/rules/quality-discipline.md` — those belong to task 03. Do not
touch `.claude-plugin/plugin.json`.

## Steps

1. In `.claude/skills/build/SKILL.md`'s procedure, add the `Rigor:
prototype` branch: skip TDD red-first, skip the verifier-agent spawn,
   run the task's acceptance commands directly and report DONE/BLOCKED on
   that signal instead. State this applies on the primary path (attended
   /build, and drain's attempt-1/relaunch workers running /build
   verbatim).
2. In `.claude/skills/drain/SKILL.md`'s tournament-path description, add
   the orchestrator-side substitution: where drain itself dispatches
   per-candidate verifier runs, it substitutes an acceptance-command run
   and ranks candidates on that instead, for `Rigor: prototype` tasks
   only. State explicitly that the pre-merge whitelist diff and project
   gates stay mechanical and unchanged in every case (they're already
   mechanical, not verifier-driven).
3. Add the promotion-rule sentence (R6) to both `.claude/skills/build/SKILL.md`
   and `.claude/skills/drain/SKILL.md` — the exact concept from Solution's
   "Promotion rule" paragraph: prototype code never merges into a
   `Rigor: production` spec's work without re-running the full gates.
4. Port steps 1-3 into `antigravity/.agents/workflows/build.md` and
   `antigravity/.agents/workflows/drain.md` (these ARE the real ported
   content for build/drain under antigravity, not thin stubs — paraphrase
   freely, match the behavior).
5. Port steps 1-3 into `codex/.agents/skills/build/SKILL.md` and
   `codex/.agents/skills/drain/SKILL.md` (real content per CLAUDE.md's
   codex mirroring convention, not symlinks).
6. Run `bash evals/lint-ultra-gate.sh` before committing (build and drain
   are both ultra-path skills).

## Acceptance

- [x] `grep -q "Rigor:" .claude/skills/build/SKILL.md && grep -q "Rigor:" .claude/skills/drain/SKILL.md` — exit 0 (verifier evidence/02-build-drain-gate-scaling.md)
- [x] `grep -qi "re-running the full gates" .claude/skills/build/SKILL.md && grep -qi "re-running the full gates" .claude/skills/drain/SKILL.md` — exit 0 (verifier evidence/02-build-drain-gate-scaling.md)
- [x] `bash evals/lint-ultra-gate.sh` exits 0 — "OK — all ultra mentions gated in 4 files" (verifier evidence)
- [x] `grep -qi "rigor" antigravity/.agents/workflows/build.md && grep -qi "rigor" antigravity/.agents/workflows/drain.md` — exit 0 (verifier evidence)
- [x] `grep -qi "rigor" codex/.agents/skills/build/SKILL.md && grep -qi "rigor" codex/.agents/skills/drain/SKILL.md` — exit 0 (verifier evidence)
