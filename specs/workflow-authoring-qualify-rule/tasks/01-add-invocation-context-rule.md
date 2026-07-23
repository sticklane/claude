# Task 01: Add the Workflow-vs-Agent-dispatch decision rule to workflow-author's Qualify step

Status: done
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/workflow-author/SKILL.md

## Goal

`.claude/skills/workflow-author/SKILL.md`'s step 1 ("Qualify") gains a
concrete two-part decision rule for when a repeated orchestration should be
authored as a Workflow script versus dispatched as plain `Agent`-tool calls
inside an existing skill's own procedure: a primary invocation-context test
(standalone/human-named/repeatable artifact vs. control flow embedded in
another skill's own already-active loop) and a secondary "at least one
genuine data-dependent barrier" filter against trivial one-shot tasks. Both
pillars land inside step 1's own text without adding a new top-level `##`
section.

## Touch

Only `.claude/skills/workflow-author/SKILL.md`, and only inside or
immediately adjacent to step 1 ("Qualify"). Do not add a new top-level `##`
section — the file's `## `-heading count must stay at 4. Do not change
`reference.md`'s templates, the Stage tiering section, or the Doctrine
guards section.

## Steps

1. Read `.claude/skills/workflow-author/SKILL.md` in full (87 lines), and
   `.claude/skills/workflow-author/reference.md`'s "Template: tournament.js"
   section, to see the worked example this task must reconcile: a
   `parallel()` build fan-out, per-item verify, then a `rank` stage the
   file's own comment calls "a true cross-item barrier" — the same shape
   `/drain`'s own tournament dispatch has, yet drain's tournament stays
   plain `Agent`-tool dispatch inside drain's own step 3.
2. Extend step 1 ("Qualify," currently the paragraph starting "Confirm the
   orchestration is genuinely deterministic control flow...") with, in
   addition to — not replacing — the existing sentences:
   - **Primary — invocation context.** An orchestration meant to be its own
     standalone artifact — invoked by name, or under the ultracode opt-in,
     repeatably across sessions, independent of any particular skill's run
     — is authored as a Workflow. An orchestration that is control flow
     already living inside another skill's own procedure, dispatched as one
     internal step of that skill's own already-active, single-writer loop
     (drain's tournament dispatch is the canonical case) stays plain
     `Agent`-tool dispatch inside that skill's own procedure, regardless of
     its internal fan-out/barrier/verify shape. State explicitly that
     `tournament.js` and drain's tournament share the identical
     fan-out-then-reduce shape but land on opposite sides because of this
     invocation-context difference, not because of any structural/barrier-
     count difference — a reader should be able to explain why the two
     differ without re-deriving it.
   - **Secondary — genuine orchestration shape.** Even a standalone,
     human-named routine only earns a Workflow's authoring overhead when it
     has at least one real data-dependent barrier — a stage that cannot
     start without the merged or reduced output of a prior fan-out (not
     merely "runs after" it). A single linear one-shot task stays prose or
     direct dispatch even when asked to be "saved as a workflow."
3. Run every acceptance command below and confirm all pass.

## Acceptance

- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qiE 'embedded|already[- ]active|already[- ]running'` → matches (the embedded-in-another-skill's-loop case is named inside step 1)
- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qiE 'standalone|repeatable across'` → matches (the standalone/human-named case is named inside step 1)
- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qi 'tournament'` → matches (the tournament.js-vs-drain worked example is present inside step 1)
- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qiE 'data-dependent|barrier'` → matches (the secondary genuine-barrier filter landed inside step 1, not just the primary invocation-context test)
- [ ] `test $(grep -c '^## ' .claude/skills/workflow-author/SKILL.md) -eq 4` → true (no new top-level section added)
- [ ] MANUAL: the new text explicitly states that `tournament.js` and drain's tournament dispatch share the same barrier/schema shape and are separated by invocation context, not structure
- [ ] MANUAL: the new sentence(s) sit inside or immediately after step 1 ("Qualify"), before step 2 ("Write the script") begins — confirm by line order, not just presence
