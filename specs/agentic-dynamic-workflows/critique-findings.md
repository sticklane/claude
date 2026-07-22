# Critique findings — READY (2026-07-22, /critique, two rounds settled)

SPEC.md sha256: 4b2b5afcc50b68c7608d6c90b07c20072d77f16f7640578fa9bcb994fc6e26bd

Critic verdict: READY (round-2 verdict READY WITH NITS; all three
nits were mechanical and applied in the same pass — the settled state
has no open findings). Breakdown-ready: true written; the spec also
carries the spec-level `Status: waiting` + `Unblock: run:` header
pair gating breakdown on core tasks 04 and 07, per its own
Sequencing section — auto-breakdown must not fire before the verbs
this spec builds on exist.

Resolution history:

- Round 1 (NOT READY): gating — run-write checkout ambiguity (fixed:
  `agentic run` executes from the primary checkout and refuses
  elsewhere, tested in RW-D); RW-V golden-output nondeterminism
  (fixed: frozen timestamps, pinned stream-end clock, COLUMNS and
  NO_COLOR pinned); DW2 tracker-silence unverified (fixed: RW-N
  export-diff over 8 concurrent dispatches plus a readable
  lock-attempt counter). Also applied: operator control verbs
  (statement 11, RW-O runs/stop with prefix-replay resume);
  turns→tokens factor calibration + RW-F fixture check; RW-G result
  validation; evidence output-token claim softened to marked
  inference; DW5 cap-default rationale (provisional, below
  ultracode's, profile-tunable); RW-B ctx-unmetered assertion; DW12
  tracker-free boundary definition; RW-C queuedAt/startedAt
  mechanism; DW10 workboard deferral; breakdown coverage obligation.
- Round 2 (READY WITH NITS): confirmed all fixes closed with no
  contradictions (statement 7 vs 8 mutually reinforcing; stop/resume
  consistent with prefix replay). Nits applied in-pass: statement
  6's workboard clause softened to match DW10; the primary-checkout
  refusal got its runnable check in RW-D; RW-N's vacuous lock clause
  replaced with a readable attempt counter.
