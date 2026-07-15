# Retiring or folding a skill: what green greps miss

When to read: deleting a skill/workflow, folding one skill into another,
or renaming a pipeline stage — before declaring the reference sweep done.

## The gotcha

On 2026-07-04, /parallel was folded into /drain. The reference sweep
(slash/path grep forms) came back clean and every deterministic gate was
green — and an opus critic pass on the diff still found five real gaps.
Green greps prove strings are absent; they don't prove the merge is
semantically complete.

## Checklist (each item is a class that was actually missed)

1. **Grep the bare name, case-insensitive** (`grep -ri parallel`), not
   just slash/path forms (`/parallel`, `parallel/SKILL.md`). The miss:
   an antigravity workflow said "the build prompt from the parallel
   workflow" — no slash, no path. Review hits manually; don't pre-filter
   with `grep -v` patterns that can hide phrasing variants.
2. **Port behaviors, not references.** List the retired skill's distinct
   behaviors and check each one landed. The miss: /parallel stopped on
   post-merge gate failures as well as merge conflicts; the fold-in kept
   only the conflict stop.
3. **Walk every dispatch path, including fallbacks.** A routing/dispatch
   change must reach the headless template, not just Task-tool dispatch.
   The miss: the escalation ladder existed only as an Agent-tool
   `model:` param; `claude -p` had no `--model`.
4. **Re-read absorbed text against the host skill's invariants.** The
   miss: group mode's "launch all in one message" sat next to drain's
   "one task at a time / wait, don't poll" with no reconciliation —
   two implementers would sequence status-flip commits differently.
5. **Then run the critic on the diff** even with all gates green — the
   four misses above are exactly the kind deterministic checks can't
   express. Cost: one deep-tier agent; it beat a clean sweep + green
   gates the day this file was written.
