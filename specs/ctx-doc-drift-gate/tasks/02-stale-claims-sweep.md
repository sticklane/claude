# Task 02: stale-claims sweep — rust caution + Output-shaping flags section

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q 'ctx-doc-drift-gate' specs/ctx-skill-token-doctrine/SPEC.md || echo "BLOCKED: registry slot absent — an attended/breakdown session must land the atomic registry commit (SPEC.md Landing order (a)+(b)+(c)) once the specs/ctx-cujs/DRAIN-OWNER.md lease clears"
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md, .claude-plugin/plugin.json

## Goal

The ctx skill's stale capability claims are fixed: the scope caution no
longer says "NOT rust" (rust extraction works — `ctx tree
context-tree/src` returns symbols, cited in the caution as the check),
and the existing output-shaping flags (`tree --depth/--limit/--doc`,
`refs --limit`, `map --tokens/--doc`, global `--json`/`--no-sync`) are
documented under a section headed exactly `## Output-shaping flags`.
Skill + antigravity mirror in the same commit, plus the plugin.json bump
(this spec's only skill-editing task carries it).

## Touch

REGISTRY-GOVERNED: this task may only run after this spec's slot exists
in specs/ctx-skill-token-doctrine's Landing order registry (the Unblock
check). It lands serialized per that registry — never in parallel with
another SKILL.md-editing task from any spec. NOTHING auto-flips this
task: /drain does not re-run `Unblock: run:` on pre-existing blocked
tasks — a human or later session re-checks and flips to pending after
the registry commit lands. The registry commit itself is NOT this task's
work (breakdown-session obligation, deferred 2026-07-21 under a live
cujs drain lease — see critique-findings.md).

## Steps

1. Verify the registry slot exists (the Unblock command) and re-verify
   rust extraction live: `ctx tree context-tree/src | head -5` returns
   symbols.
2. Edit the scope cautions: remove/correct "NOT rust", keeping any
   genuinely unextracted languages accurate against the extractor
   registry in `context-tree/src/`; cite `ctx tree context-tree/src` as
   the self-check.
3. Add the `## Output-shaping flags` section documenting the eight
   flags. Mirror both edits to
   `antigravity/.agents/skills/ctx/SKILL.md` in the same commit; bump
   plugin.json.

## Acceptance

- [ ] `grep -c 'NOT rust' .claude/skills/ctx/SKILL.md` → 0
- [ ] `grep -q 'ctx tree context-tree/src' .claude/skills/ctx/SKILL.md && echo ok` → ok
- [ ] For each flag F in `--depth --limit --doc --tokens --json --no-sync`: `sed -n '/^## Output-shaping flags/,/^## /p' .claude/skills/ctx/SKILL.md | grep -c -- "$F"` → ≥1
- [ ] Same six sed-scoped greps against `antigravity/.agents/skills/ctx/SKILL.md` → all ≥1
- [ ] `cd context-tree && cargo test --test doc_conformance` → exit 0 (the new section's invocations validate against the binary — requires task 01 landed; if not yet landed, mark this criterion manual-pending with that reason)
- [ ] `git show $(git merge-base HEAD origin/main):.claude-plugin/plugin.json | grep '"version"'` differs from current (base-commit comparison, never a pinned literal)
