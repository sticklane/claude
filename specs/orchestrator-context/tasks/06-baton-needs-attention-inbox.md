# Task 06: promote batons with a needs-attention section into the workboard inbox

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: none
Spec: ../SPEC.md
Discovered-by: 04-workboard-baton-cards.md
Touch: .claude/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, antigravity/.agents/skills/workboard/test_workboard.py, .claude-plugin/plugin.json

## Goal

verbatim worker report — vet/rewrite before promoting:

> R6/SPEC says a headless drain generation that hits the batch-interview or
> the max-generations cap writes its deferred questions into the baton as a
> needs-attention section and 'the workboard surfaces it' — task 04's
> acceptance scoped this to a repo card only. A follow-up could also promote
> batons carrying a needs-attention section into the attention_items() inbox
> so they rank among blocked work, not just as a repo card.

## Answers

Decision (2026-07-04): un-deferred and built this session (user request while
draining the queue). Task 04 already surfaces needs-attention batons as a repo
card; this task additionally promotes them into `attention_items()` so they
rank alongside blocked work. Both surfaces coexist by design.

## Acceptance

- `attention_items()` emits one `blocked`/`serious` inbox item per baton whose
  `needs_attention` field is non-empty, carrying the deferred question in `why`
  and the baton's relaunch `command` as `cmd`.
- A baton with an empty/absent `needs_attention` adds NO inbox item (unchanged
  from task 04 — card-only).
- The promoted item ranks among blocked work (severity `serious`), sorting
  ahead of warning-level git-state items for the same repo.
- Antigravity mirror carries the same change in the same commit; both
  `test_workboard.py` mirrors stay in lockstep; `.claude-plugin/plugin.json`
  bumped (0.7.13 → 0.7.14).
- Acceptance command: `python3 -m unittest discover -s .claude/skills/workboard`

## Evidence (verifier PASS 2026-07-04)

- ✅ 33 tests OK on both `.claude` and antigravity mirror suites (4 new
  `TestBatonNeedsAttentionInbox` cases: promotion, relaunch cmd, empty→no-item,
  ranks-before-warnings).
- ✅ Both `workboard.py` + both `test_workboard.py` paths changed and
  byte-identical; plugin.json 0.7.13 → 0.7.14; smoke run exits 0.
