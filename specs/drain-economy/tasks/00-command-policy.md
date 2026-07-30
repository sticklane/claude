# Task 00: the command policy for file-sourced execution

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: none
Priority: P0
Budget: 35 turns
Spec: ../SPEC.md (decision D11)
Touch: bin/command-policy, .claude/rules/file-sourced-commands.md, tests/test_command_policy.sh, tests/inventory/drain-economy-00.json, specs/toolkit-core-simplification/surface-inventory/drain-economy-00.json

## Goal

One implementation decides whether a command parsed out of a repository file
may execute. `bin/command-policy <argv…>` returns a verdict — accept, or reject
with a machine-readable reason — under D11: argv-0 resolves to a regular
executable under an allowlisted root, execution is direct and never through a
shell, arguments survive POSIX shell-word lexing with no ASCII control
characters, cwd is the repo root, a bounded timeout applies, and no network is
granted. `.claude/rules/file-sourced-commands.md` states the rule so both
consumers cite it rather than restating it.

## Touch

This task is the sole author of the policy. Task 02 (`Unblock: run:`) and task
08 (`bin/spec-gate`) both consume it and are forbidden from writing a second —
that is why this task exists separately and why both depend on it.

`.claude/rules/human-blockers.md` is the model, not the target: it already
defines this shape for blocker probes (name resolution, no shell, POSIX
lexing, argv execution, cwd at the git root). Reuse its reasoning and its
vocabulary; do not edit it, and do not fold probe resolution into this policy —
the probe contract stays where it is.

## Steps

1. Write the failing test first: `tests/test_command_policy.sh` over
   `mktemp -d` fixtures. Assert on the verdict and its reason code, never on
   prose, and prove the negative cases by observation — each hostile fixture
   plants a sentinel-creating command and the test asserts the sentinel is
   absent afterward, the technique `tests/test_human_blockers.sh` uses.
2. Cover the accept path: an allowlisted argv-0 with ordinary arguments
   accepts, and executing it produces its expected effect within the timeout.
3. Cover the reject paths, one case each: an argv-0 that resolves nowhere; one
   that resolves outside the allowlisted roots; a shell metacharacter
   (`;`, `|`, backtick, `$(`) reaching argv; an ASCII control character; an
   unbalanced quote; an argument-count or length bound if the design sets one;
   a command exceeding the timeout. Each records a distinct reason code.
4. Implement `bin/command-policy`, matching the existing `bin/` scripts'
   language and conventions. It decides and optionally executes; it never
   interprets the *meaning* of a command, and it has no knowledge of drain,
   spec-gate, or acceptance criteria.
5. Write `.claude/rules/file-sourced-commands.md` stating the policy as a rule
   both consumers cite: the accept conditions, the reason codes, and the
   demotion contract — a rejected command is never executed, and its consumer
   records the reason (EP18 demotes `run:` to `ask:`, EP12 records `skip`).
6. Register the new script, rule, and test in the surface and test inventories.

## Acceptance

- [ ] `bash tests/test_command_policy.sh` → exits 0, reports 0 failures. **L2**
- [ ] Every hostile fixture leaves no sentinel: the test's output contains no
      `SENTINEL` line, and the fixture directory's file count is unchanged
      after the run. **L2**
- [ ] `bin/command-policy /bin/echo hi; echo $?` → 0 on an allowlisted argv-0,
      and a resolvable-but-unallowlisted argv-0 exits nonzero with a reason
      code — asserted in the test. **L2**
- [ ] Each reject case returns a *distinct* reason code — asserted in the test
      by collecting the codes and checking the set size equals the case
      count. **L2**
- [ ] `grep -c 'command-policy' .claude/rules/file-sourced-commands.md` → ≥ 1
      (the file is new today, 2026-07-30). **L1**
- [ ] `bash tests/test_doc_links.sh` → passes, proving the new rule's links
      resolve. **L2**
- [ ] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
