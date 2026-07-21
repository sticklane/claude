# Task 02: valid-deps dependent

Status: pending
Depends on: 1
Priority: P2
Touch: fixture/dependent

## Goal

Fixture task whose `Depends on: 1` resolves to task 01 in this same fixture
spec — a valid, resolvable reference. No `unresolved-external-dep`
diagnostic fires, so `drain_frontier.py --strict` must exit 0 with output
identical to the no-flag run.
