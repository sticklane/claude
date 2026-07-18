# Task 01: Canonical commit doctrine in quality-discipline.md + AGENTS.md mirror

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: .claude/rules/quality-discipline.md, antigravity/AGENTS.md

## Goal

The `## Commits` section of `.claude/rules/quality-discipline.md` is the
single canonical commit doctrine: it states the subject-length rule (target
≤72 characters, hard cap 100), the subject/body split (subject = what
changed; ratification notes, verifier evidence, audit notes, acceptance
detail, multi-clause context = body), lists the sanctioned orchestration
prefixes (`drain:`, `merge:`, `spec:`, `breakdown:`) alongside the
conventional types, marks `drain: <spec-slug> task NN in-progress` as a
regex-pinned machinery contract the length rule must never cause an agent to
reword, and states the Co-Authored-By trailer expectation. The commits
bullet in `antigravity/AGENTS.md` mirrors the length rule, subject/body
split, and prefix sanction compactly, and that file stays ≤200 lines.

## Touch

Only the two files in the `Touch:` header. Do NOT edit
`.claude/skills/drain/*`, `.claude/skills/build/*`, any
`antigravity/.agents/` or `codex/` file, or `.claude-plugin/plugin.json` —
those are task 02's scope. Within `antigravity/AGENTS.md`, edit only the
commits bullet region (~line 126); everything else in that file is out of
scope.

## Steps

1. Read the `## Commits` section of `.claude/rules/quality-discipline.md`
   (~line 33; file is 64 lines) and extend it: keep the existing three
   bullets, add the subject-length rule using the literal phrase
   "hard cap 100", the subject/body split using the literal phrase
   "subject/body", the sanctioned orchestration prefixes (`drain:`,
   `merge:`, `spec:`, `breakdown:`), the regex-pinned callout naming
   `drain: <spec-slug> task NN in-progress` verbatim (singular "task" —
   drain's diff-base recovery greps for it; cite
   `.claude/skills/drain/SKILL.md`), and the trailer expectation
   (agent-authored commits keep the harness-provided `Co-Authored-By`
   trailer; never strip it).
2. Mirror the new rules compactly into the commits bullet of
   `antigravity/AGENTS.md` (~line 126; file is 185 lines): length rule with
   "hard cap 100", the "subject/body" split, and the prefix sanction. This
   is a paraphrased port, not a byte copy (per
   `.claude/rules/mirror-procedure-discipline.md`) — carry the same rules,
   adapt the prose. Keep the file ≤200 lines.
3. Run every acceptance command below; tick each box with one line of
   evidence.
4. Commit both files in one commit following the doctrine just written
   (docs type, subject ≤72 chars, detail in the body).

## Acceptance

- [x] `grep -c 'hard cap 100' .claude/rules/quality-discipline.md` → ≥ 1
      (verifier: 2; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -ci 'subject/body' .claude/rules/quality-discipline.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -c 'drain: <spec-slug> task NN in-progress' .claude/rules/quality-discipline.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -c 'regex' .claude/rules/quality-discipline.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -c 'breakdown:' .claude/rules/quality-discipline.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -ci 'Co-Authored' .claude/rules/quality-discipline.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -c 'hard cap 100' antigravity/AGENTS.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `grep -c 'subject/body' antigravity/AGENTS.md` → ≥ 1
      (verifier: 1; evidence/01-canonical-doctrine-and-agents-mirror.md)
- [x] `wc -l < antigravity/AGENTS.md` → ≤ 200 (verifier: 191)
