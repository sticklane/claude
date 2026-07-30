# Task 03: the discovered-work economy — discriminator, triage label, cap, floor

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 02
Priority: P1
Budget: 35 turns
Spec: ../SPEC.md (requirements EP1, EP2, EP3, EP4, decisions D1, D5, D7)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/work/SKILL.md, agentic/ready.py, tests/test_drain_triage_economy.sh, tests/inventory/drain-economy.json

## Goal

Discovered work stops being an unbounded ratchet. Every discovered item is
classified blocking or adjacent by one stated discriminator: an item is
*blocking* iff its parent issue's (or the focus feature's) acceptance criteria
cannot pass without it. Blocking children file as today, uncapped, citing the
failing criterion. Adjacent items file with label `triage`, are excluded from
every ready query, and are admitted only at the batch interview's three verbs.
At most `DRAIN_TRIAGE_CAP` (default 5) adjacent filings reach bd per run;
overflow lands in the report's Discovered digest. Auto-filing at all requires
clearing a severity floor.

## Touch

This task owns the filing step and the ready-query exclusion. It must NOT
touch the selector (task 01), the spillover branch (task 02), the run bead or
narration (task 04), or `bin/drain-report` (task 05) — the Discovered digest
is *named* here as the overflow destination and *rendered* there. Janitor's
triage decay is task 11's; this task defines the label, that task expires it.

`declined-at-triage` and `triage-archived` are one convention per the spec's
resolved question: both close the bead and both label why it died. Write the
decline half here; task 11 writes the decay half against the same convention.

## Steps

1. Write the failing test first: `tests/test_drain_triage_economy.sh` over
   `mktemp -d` bd fixtures, asserting the query contract — a `triage`-labeled
   issue never appears in the ready set, an unlabeled one does, and stripping
   the label returns it. Assert on parsed JSON structure, not on printed
   strings.
2. Edit `agentic/ready.py` so the ready computation excludes `triage`-labeled
   issues, and confirm no other caller silently depends on their inclusion.
3. Edit `.claude/skills/drain/SKILL.md`'s filing step (loop step 3 and the
   workflow-compile bullet) with the discriminator wording, stated as
   "blocking iff …" so it is greppable, and the severity floor: auto-filing
   even to triage requires the item to block acceptance somewhere or violate a
   named rule in `.claude/rules/` or a repo invariant; style and opportunity
   findings are digest-only.
4. Carry the same discriminator wording into `.claude/skills/drain/reference.md`'s
   worker prompt, and require the worker to name the failing criterion when it
   files blocking work.
5. Document `DRAIN_TRIAGE_CAP` (default 5) in `reference.md` with the overflow
   behavior: excess adjacent findings go to the report's Discovered digest with
   enough context to re-file by hand; blocking children are exempt from the cap.
6. Add the batch-interview verbs to SKILL.md's existing interview section:
   promote (strip label), decline (close the bead **and** label it
   `declined-at-triage`), defer (leave). Add the label entries to
   `.claude/skills/work/SKILL.md`'s bd command reference, which CLAUDE.md
   names as the conventions home for bd usage.
7. Keep SKILL.md under its size budget; long-form detail goes to `reference.md`.

## Acceptance

- [ ] `bash tests/test_drain_triage_economy.sh` → exits 0, reports 0
      failures. **L2**
- [ ] `python3 -m pytest tests/test_agentic_ready.py -q` → passes, proving the
      exclusion did not break the existing ready contract. **L2**
- [ ] `grep -c 'blocking iff' .claude/skills/drain/SKILL.md` → ≥ 1 (verified 0
      in the whole file today, 2026-07-30). **L0** — Depth ceiling: the
      discriminator is a judgment instruction to a worker, not an executable
      rule; its behavioral complement is the triage-count assertion in task
      14's end-to-end eval.
- [ ] `grep -c 'severity floor' .claude/skills/drain/SKILL.md` → ≥ 1 with the
      rule-citation requirement on the same or an adjacent line (verified 0
      today, 2026-07-30). **L0** — Depth ceiling: as above.
- [ ] `grep -c 'DRAIN_TRIAGE_CAP' .claude/skills/drain/reference.md` → ≥ 1
      with default 5 stated (verified 0 in both drain files today,
      2026-07-30). **L0** — Depth ceiling: as above.
- [ ] `grep -c 'declined-at-triage' .claude/skills/work/SKILL.md` → ≥ 1
      (verified 0 today, 2026-07-30). **L0** — Depth ceiling: a conventions
      entry has no runtime; task 11's janitor test exercises the shared
      close-plus-label convention.
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500. **L1**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
