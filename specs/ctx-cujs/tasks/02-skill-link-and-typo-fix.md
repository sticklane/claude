# Task 02: ctx skill links the CUJ doc + fixes map flag typo

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R3)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md, .claude-plugin/plugin.json

## Goal

The ctx skill body links the CUJ playbook once ("CUJ playbook:
docs/guides/ctx-cujs.md") and its command table's `map [--limit N]` error
is fixed to `map [--tokens N]` (the flag `map` actually has — no `--limit`
exists per `cli.rs`).

## Touch

This is SLOT 7 (always last, confirmed at
specs/ctx-skill-token-doctrine/SPEC.md:20) of the SKILL.md editor registry
in that spec's Landing order (../../ctx-skill-token-doctrine/SPEC.md:5-24).
Do not touch any other section of either SKILL.md beyond the CUJ-doc link
and the `map` flag correction. Per CLAUDE.md's authoring conventions, a
task that changes `.claude/skills/` files must carry the plugin.json
version bump in its own `Touch:` — this task is that closing edit for
this spec (a later drain generation may also need it for the token-doctrine
chain's own final slot, but this task owns it for THIS spec's edit).

**This spec cannot reach `done` in isolation.** This task is the tail of
a 7-spec SKILL.md serialization chain — slots 1-6 belong to SIX OTHER
specs (ctx-skill-token-doctrine, ctx-static-analysis-augmentation,
ctx-query-ergonomics, ctx-minified-skip, ctx-dead-code-zones,
ctx-absence-check), each of which must land its own SKILL.md edit before
this one may. Tasks 01 and 03 of THIS spec can complete independently;
this task will likely park DEFERRED for a while.

## Steps

1. Confirm `docs/guides/ctx-cujs.md` exists (task 01's output; this task's
   `Depends on: 01` should already guarantee it, but verify before citing
   it in a link).
2. Run the registry-landed check below. If ANY of the 6 markers is
   missing, stop DEFERRED with "specs/ctx-skill-token-doctrine's SKILL.md
   editor registry slots 1-6 have not all landed yet" — do not proceed
   and do not guess which slot is missing beyond what the check reports.
   ```bash
   grep -q "Reading ladder" .claude/skills/ctx/SKILL.md &&   # slot 1a (token-doctrine R2)
   grep -q "ABSENCE FALLACY" .claude/skills/ctx/SKILL.md &&  # slot 1b (token-doctrine R7)
   grep -q "ast-grep --pattern" .claude/skills/ctx/SKILL.md &&  # slot 2 (augmentation R1)
   grep -q "ctx show <symbol>" .claude/skills/ctx/SKILL.md &&  # slot 3 (query-ergonomics R4)
   grep -q "\.ctxkeep" .claude/skills/ctx/SKILL.md &&  # slot 4 (minified-skip R4)
   grep -q "zone dead trees" .claude/skills/ctx/SKILL.md &&  # slot 5 (dead-code-zones R4)
   grep -q "now emits the guard itself" .claude/skills/ctx/SKILL.md &&  # slot 6 (absence-check R5)
   echo "all 6 slots landed"
   ```
   (These markers were the best available at breakdown time from each
   sibling spec's own requirement text — if a marker doesn't match because
   that spec's implementation phrased things differently, read the actual
   current SKILL.md content and use judgment on whether the slot's
   substantive change landed, not just this exact string.)
3. Add a single link line "CUJ playbook: docs/guides/ctx-cujs.md" to
   `.claude/skills/ctx/SKILL.md`'s body (near the top, where a skill
   typically points at its doctrine references).
4. Fix the command table: `map [--limit N]` → `map [--tokens N]`.
5. Apply both edits identically (content-parity, not necessarily verbatim
   text) to `antigravity/.agents/skills/ctx/SKILL.md` in the same commit.
6. Bump `.claude-plugin/plugin.json`'s `version` (patch component, unless
   recent `git log -p -- .claude-plugin/plugin.json` shows a different
   convention) in the same commit — skill behavior changed (CUJ link +
   corrected flag documentation).

## Acceptance

- [ ] `grep -q 'docs/guides/ctx-cujs.md' .claude/skills/ctx/SKILL.md`
      succeeds.
- [ ] `grep -q 'docs/guides/ctx-cujs.md' antigravity/.agents/skills/ctx/SKILL.md`
      succeeds.
- [ ] `grep -c 'map \[--limit' .claude/skills/ctx/SKILL.md` → 0.
- [ ] `grep -c 'map \[--limit' antigravity/.agents/skills/ctx/SKILL.md` → 0.
- [ ] The `version` value in `.claude-plugin/plugin.json` at HEAD differs
      from its value at this task's own base commit (`git merge-base HEAD
    main`) — a real bump, not unrelated drift.
- [ ] `git diff --stat` for this task's commit touches only the three
      files listed in Touch.
