# Critique findings — verification-machinery-integrity

Spec-content-sha256: afe7d534f5736bf50f37295245d3f6272dc6a3e0055e13e77c34142ca099d424
Verdict: NOT READY

## 2026-07-30

Single critic pass. All ten findings are JUDGMENT-class: gameable criteria are
never MECHANICAL, since changing what a criterion checks changes what the spec
verifies. All ten were applied by the author in the same session; no second
critic pass was run, per the skill's single-dispatch rule.

The sharpest finding is that the spec was guilty of the defect it describes —
four of its own acceptance criteria were gameable or vacuous.

1. (92) R1 and the Solution paragraph contradicted each other on the third
   liveness value: Solution said mtime fallback, R1/A2 required a distinct
   `unknown`. Both readings passed their own text.
2. (90) No requirement said what callers do with `unknown`, which is the whole
   safety question when both callers delete directories.
3. (88) R3 reintroduced the destructive bug when the inventory is unavailable —
   mtime is then the only basis, and discounting it releases a worktree a live
   session may own. A4 green-checked the unsafe path.
4. (85) R3 named no mechanism for "was just gated by the calling process";
   pre-gate baseline, caller flag, PID exclusion, and marker file were all
   conforming with different failure modes.
5. (86) R5's `serial` hatch made A6 gameable — satisfiable by marking every
   offending suite serial without isolating anything — and is invalid for the
   `pkill` class R5 itself enumerates, since `serial` only orders suites within
   one check.sh run while a machine-wide signal reaches other processes.
6. (82) Nothing required the new lint to be registered in the test inventory,
   so A13 could pass with the lint never executing.
7. (84) A5 was a timing race that could pass by luck, and mutated the real
   `.beads/` with no cleanup — the spec's own stated failure mode.
8. (80) A12 said "verbatim" with no canonical text anywhere in the spec, so two
   workers write two sentences and both self-certify.
9. (68) A11 was an L1 string check labelled L2 — "names the action to take" is
   satisfied by any string.
10. (70) R8 added a disposition value with no runtime dispatch requirement, so
    a retired test could still be executed.

Not examined (tool ceiling): the supersession logic at
scripts/inventory-core-surface.py:798 behind R7/A8, and whether the new test
files A2/A4/A8/A11 name exist today.
