# Task 08: residual loop-bound false-neg/false-pos classes in check-token-discipline

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: draft
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

## Acceptance (to define when promoted)

- New adversarial cases from `wf_312b145a-492` added to the test contract and
  passing.
- No regression in the 16 cases task 07 locked, nor the existing fixtures.
- Decide and document the precision-vs-friction stance (flag-when-unsure vs
  permissive) in SPEC R6.
