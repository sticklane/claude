# Task 02: Grant scout the ctx binary and prefer-ctx prompt (R5)

Status: done
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: .claude/agents/scout.md, antigravity/.agents/skills/scout/SKILL.md

## Goal

The `scout` agent can actually run the ctx binary and is told to prefer it.
Two required changes to `.claude/agents/scout.md`: (a) add `Bash(ctx *)` to
the frontmatter `tools:` allowlist — today the allowlist physically cannot
execute the binary, so any prompt-only mention is dead text; (b) add a prompt
line directing scout to prefer `ctx` queries (when the repo is indexed)
before Grep/Read, including the binary-resolution one-liner. The antigravity
scout mirror gets the equivalent prefer-ctx prompt guidance in the same
commit (the mirror is a paraphrased port with no `tools:` frontmatter, so it
carries the prompt guidance, not the allowlist entry).

## Touch

`.claude/agents/scout.md` (frontmatter `tools:` line + prompt body) and the
antigravity mirror `antigravity/.agents/skills/scout/SKILL.md` (prompt body
only — it has no tool allowlist to widen). This task is unblocked by R4
(task 04), whose survey delegation only becomes functional once this grant
exists; land this before 04.

## Steps

1. Add `Bash(ctx *)` to the `tools:` frontmatter list in
   `.claude/agents/scout.md`.
2. Add a prompt line: prefer `ctx tree/sig/refs/deps` over Grep/Read when the
   repo is indexed, with the binary-resolution one-liner (`ctx` on PATH →
   `context-tree/target/release/ctx`). Note that Grep/Read stay the fallback
   for content questions and unindexed repos.
3. Mirror the prefer-ctx prompt guidance into
   `antigravity/.agents/skills/scout/SKILL.md`.
4. Run the acceptance commands.

## Acceptance

- [x] `grep -q 'Bash(ctx' .claude/agents/scout.md` → exit 0 (grant present) — verified: PASS, `tools:` line now includes `Bash(ctx *)`.
- [x] `grep -qi 'ctx' .claude/agents/scout.md` matches in prompt-body context (prefer-ctx guidance present, not just the frontmatter grant) — verified: PASS, new Rules bullet directs preferring `ctx tree/sig/refs/deps` with the binary-resolution one-liner.
- [x] `grep -qi 'ctx' antigravity/.agents/skills/scout/SKILL.md` → exit 0 (mirror carries prefer-ctx guidance) — verified: PASS, matching Rules bullet added (no `tools:` frontmatter to widen there).
