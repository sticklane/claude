# Task 06: promote batons with a needs-attention section into the workboard inbox

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: deferred
Depends on: none
Spec: ../SPEC.md
Discovered-by: 04-workboard-baton-cards.md

## Goal

verbatim worker report — vet/rewrite before promoting:

> R6/SPEC says a headless drain generation that hits the batch-interview or
> the max-generations cap writes its deferred questions into the baton as a
> needs-attention section and 'the workboard surfaces it' — task 04's
> acceptance scoped this to a repo card only. A follow-up could also promote
> batons carrying a needs-attention section into the attention_items() inbox
> so they rank among blocked work, not just as a repo card.

## Answers

Decision (2026-07-04): worth doing, but **deferred to backlog** — not built
this session. Task 04 already surfaces needs-attention batons as a repo card,
which covers the SPEC's R6 "the workboard surfaces it" obligation; promoting
them into `attention_items()` so they rank alongside blocked work is a real
enhancement but not urgent. Left as `deferred` so it stops showing as active
blocked work; re-dispatch via /build when the backlog is picked up.
