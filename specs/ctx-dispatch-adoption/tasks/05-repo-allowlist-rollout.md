# Task 05: MANUAL — Bash(ctx *) allowlist rollout across the 8 indexed repos

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: obsolete
Closed: subsumed by specs/agentic-core-redesign — see specs/agentic-core-redesign/TRIAGE.md
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R3c)
Depends on: none
Touch: (no ~/claude paths — cross-repo, attended session only)

## Goal

Every indexed repo's `.claude/settings.json` allowlists `Bash(ctx *)`,
so interactive subagents and sessions stop hitting permission prompts on
ctx queries. MANUAL: the 8 target repos are outside this repo's Touch
scope — an unattended ~/claude drain worker must NOT be dispatched on
this task (docs/memory/unattended-worker-tool-limits.md pattern); an
attended session (any cwd) executes it and ticks the criteria. The
`Status: blocked` + `Unblock: decide:` header pair is the machine-read
guard (drain parses headers, never bodies); NOTHING auto-flips this —
the attended session that performs the rollout flips it straight to
done.

## Steps

1. For each repo R in: ~/automation ~/budget_analysis ~/claude
   ~/fooszone ~/hub ~/interview-prep ~/portfolio-tracker ~/ynab-mcp-new —
   add `"Bash(ctx *)"` to the permissions allow array of
   `R/.claude/settings.json` (create the file with just that permission
   block if absent). Use each repo's own conventions for committing
   (fooszone auto-pushes; check `core.hooksPath` in ex-beads repos
   before git ops — docs in memory).
2. Check for a live drain lease / busy session in each repo before
   committing (concurrent-sessions rule); skip and note any repo that is
   mid-drain, to be finished later.

## Acceptance

All manual-pending (attended session runs and ticks them):

- [ ] `for r in ~/automation ~/budget_analysis ~/claude ~/fooszone ~/hub ~/interview-prep ~/portfolio-tracker ~/ynab-mcp-new; do grep -ql 'Bash(ctx' "$r/.claude/settings.json" 2>/dev/null || echo "missing: $r"; done` → empty output
- [ ] Each edited repo's change is committed per that repo's conventions (no uncommitted settings edits left behind)

Depth ceiling: L1 config greps — the artifact is permission config; the
behavioral complement is task 04's telemetry showing subagent ctx calls
rising off the 0 baseline.
