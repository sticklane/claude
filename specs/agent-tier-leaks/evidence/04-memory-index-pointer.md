# Verification: 04-memory-index-pointer

Verdict: PASS

## Criterion 1 — index entry present, faithful to `Read when:` header

Command: `grep 'verifier-tier-leak' docs/memory.md`

Output:
```
- [verifier-tier-leak](memory/verifier-tier-leak.md) — an agent's frontmatter `model:` pin (verifier=sonnet, scout=haiku, etc.) appears not to hold in a cost profile (a pinned agent billed at the session's frontier model), or reasoning about why a shipped agent-def fix doesn't show up in a running install: the stale immutable plugin-cache snapshot still serves the old `model: inherit` pin.
```

Format matches the surrounding convention (`- [slug](memory/slug.md) — <hook>`),
one line, positioned as line 18 within the existing list (lines 7-18).

Cross-checked against `docs/memory/verifier-tier-leak.md` lines 3-6 (`Read
when:` header):
```
**Read when:** an agent's frontmatter `model:` pin (verifier=sonnet,
scout=haiku, etc.) appears not to hold in a cost profile — a pinned agent
billed at the session's frontier model — or when reasoning about why a
shipped agent-def fix doesn't show up in a running install.
```

The index entry's hook is a near-verbatim paraphrase of this header (same
three clauses: pin-not-holding-in-cost-profile / frontier-billed pinned
agent / shipped-fix-not-showing-in-install), not invented — the entry adds
one clarifying clause ("the stale immutable plugin-cache snapshot still
serves the old `model: inherit` pin") drawn from the note's own body (What
happened / Root cause), not fabricated.

Result: PASS

## Criterion 2 — exactly one entry, no duplicates

Command: `grep -c '^- \[verifier-tier-leak\]' docs/memory.md`

Output: `1`

Result: PASS

## Task-file append-only check

Base commit: 307b2c6
Command: `git diff 307b2c6 -- specs/agent-tier-leaks/tasks/04-memory-index-pointer.md`

Diff:
```diff
-Status: in-progress
+Status: done
@@
-- [ ] `grep 'verifier-tier-leak' docs/memory.md` finds a one-line index
+- [x] `grep 'verifier-tier-leak' docs/memory.md` finds a one-line index
   entry matching the existing convention (lines 7–15):
   `- [verifier-tier-leak](memory/verifier-tier-leak.md) — <one-line hook>`
   — the hook description should be drawn from
   `docs/memory/verifier-tier-leak.md`'s own `Read when:` header, not
   invented.
-- [ ] `grep -c '^- \[verifier-tier-leak\]' docs/memory.md` returns exactly 1
+  Evidence: grep returns the new entry; hook paraphrases the note's `Read
+  when:` header (frontmatter `model:` pin not holding / pinned agent billed
+  at frontier / fix not showing in running install).
+- [x] `grep -c '^- \[verifier-tier-leak\]' docs/memory.md` returns exactly 1
   (no duplicate entries).
+  Evidence: `grep -c` returns 1.
```

Only the Status line flipped and the two checkboxes ticked with evidence
lines appended — no Goal/Acceptance criterion TEXT altered. Compliant
(append-only).

## Scope-creep check

Command: `git diff 307b2c6 --stat`

```
 docs/memory.md                                          |  1 +
 specs/agent-tier-leaks/tasks/04-memory-index-pointer.md | 10 +++++++---
 2 files changed, 8 insertions(+), 3 deletions(-)
```

Only `docs/memory.md` (the declared `Touch:` target) and the task file
itself changed. No scope creep.

## Gates

No repo-level `scripts/check.sh` gate exists for this toolkit repo per
`docs/memory/claude-repo-no-checksh-gate.md` convention (task acceptance
here is the grep-based criteria above); no build/lint/test gate applies to
a docs/memory.md-only change.

## Working tree

`git status` on the worktree at time of verification: clean (no
uncommitted changes); this verification made no modifications other than
this evidence file.
