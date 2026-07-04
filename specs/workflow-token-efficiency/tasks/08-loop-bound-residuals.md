# Task 08: residual loop-bound false-neg/false-pos classes in check-token-discipline

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: pending
Depends on: none
Priority: P3
Spec: ../SPEC.md
Discovered-by: 07-loop-bound-positional-check.md

## Goal

Task 07 tightened `LBOUND` so a bare stray numeral no longer counts as a loop
bound, and locked 16 adversarial cases into `tests/test_check_token_discipline.sh`.
Two adversarial verification passes then established that fully robust
natural-language bound detection is **not regex-achievable** — several residual
classes remain, and some fixes directly conflict (loose adjacency to accept
"two additional attempts" reopens "up to four sources"). Shipping decision: keep
the materially-improved regex, document the residuals here. This task tracks a
deeper fix (likely a small tokenizer/parser or a redesign that errs toward
false-positives, flagging when unsure).

Residual classes (all verified against the shipped checker):

- **Glued / hyphenated compounds (false negative).** A count fused to a cycle
  noun inside one word reads as a bound: `onetime` → "one time", `one-pass` →
  "one pass", `twotime` → "two time". Root: the count has no right word-edge
  before the noun gap.
- **Quantifier+count on a non-cycle noun (false negative).** The `LQUANT..LNUM`
  branch accepts "up to four" / "at most three" / "capped at two" / "a maximum
  of four" with NO cycle noun, so it binds to `sources` / `files` / `dashboards`
  / `shards` and masks an unbounded loop.
- **Adjective between count and noun (false positive).** A real cap with an
  interposed word is flagged: "two additional attempts", "three further cycles",
  "two more times", "two consecutive rounds" — the count→noun gap is too tight.
- **Missing nouns/forms (false positive).** `loop(s)` is absent from the noun
  list (ironic, given the `[loop]` check), hyphenated `re-dispatches` is not
  matched (only `redispatches`), and ordinals (`third pass`, `capped at the
  third attempt`) are not recognized as counts.
- **Temporal `once/twice` (false negative).** "relaunch once a check goes red"
  reads as the bound "relaunch once".

## Answers

**Open question — precision-vs-friction stance for the R6 dispatch/loop-bound
checks (flag-when-unsure vs permissive): decided flag-when-unsure
(false-positive-tolerant), bounded by the locked anti-FP fixtures.**

Rationale:

- The checker guards a *curated 9-file in-scope list* of authored skills
  (SPEC R6), not arbitrary user repos. The remediation for a false-positive
  is cheap and is itself the desired end state: the author makes the
  tier/bound explicit and adjacent — exactly what R3/R4 ask for. The
  remediation for a false-negative is nothing: a tier-less dispatch or
  unbounded loop ships silently, defeating the gate. Asymmetric costs →
  err toward flagging.
- This resolves the "some fixes directly conflict" note in the Goal. The
  conflict (loosening count→noun adjacency to accept "two additional
  attempts" reopens the "up to four sources" false-negative) is decided in
  favor of *not* loosening adjacency: keep the tight rule so
  quantifier+count on a non-cycle noun ("up to four sources") and temporal
  "once"/"twice" ("relaunch once a check goes red") FLAG rather than pass as
  phantom bounds. A genuinely-capped-but-oddly-phrased paragraph is fixed by
  rewriting it to state the bound adjacently (`at most two additional
  attempts`), not by widening the regex.
- Precision is preserved *narrowly and only via tested carve-outs*: the
  false-positive fixtures task 07 locked (tournament-cleanup, "no relaunch",
  "relaunch clean", "3× the tokens", max-generations) stay green. Any new
  legitimate phrasing that must not flag enters the same way — an added
  must-NOT-flag fixture plus a scoped exception — never by relaxing the
  general rule.

Net effect on the five residual classes: the two false-negative classes
(glued/hyphenated compounds; quantifier+count on non-cycle noun; temporal
once/twice) are closed by tightening toward flagging; the two false-positive
classes (adjective-between-count-and-noun; missing nouns/forms) are addressed
by *adding the missing noun/form vocabulary* (`loop(s)`, hyphenated
`re-dispatches`, ordinals) and by an explicit adjacency allowance for a
*single* interposed count-adjective (`additional`/`further`/`more`/
`consecutive`) — enumerated and fixture-locked, not a general gap widening —
so real caps pass without reopening the FN classes.

## Acceptance

- The five residual classes in this task's Goal are each encoded as
  adversarial fixtures (from `wf_312b145a-492`) in
  `tests/test_check_token_discipline.sh` with the flag-when-unsure verdict
  above: glued/hyphenated compounds, quantifier+count-on-non-cycle-noun, and
  temporal once/twice **must be flagged** (loop-bound check fails); the
  enumerated count-adjective and missing-noun/form phrasings **must pass**.
- No regression: the 16 cases task 07 locked and every existing fixture
  (incl. the must-NOT-flag list and the max-generations must-PASS fixture)
  still pass — `bash tests/test_check_token_discipline.sh` exits 0.
- `bin/check-token-discipline` still exits 0 on the retrofitted tree (the
  new vocabulary/adjacency must not flag any in-scope skill paragraph).
- SPEC R6's bounded-loops / dispatch prose is amended to state the
  flag-when-unsure stance in one line, citing this task, so the intent is
  recorded where the checker's contract lives.

Acceptance command: `bash tests/test_check_token_discipline.sh`
