Status: done
Discovered-from: specs/eval-coverage-tiers/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# `evals/idea/02-adv-doctrine-grep/assert.sh` greps its anchor markers repo-wide across the spec file, not scoped to the criterion under test

The grader greps for the `verified <date>` anchor and the `Depth ceiling:`
marker anywhere in the produced spec file, rather than scoping the check
to the specific grep criterion under test. A run that keeps an
unanchored/bad acceptance criterion but happens to place those marker
strings elsewhere in the file could pass this grader.

Not fixed by the spec-completion review that discovered it: judged
low-confidence/uncertain — the subject under test is the real `/idea`
skill, not an adversary actively gaming string placement, so
marker-presence may already be adequate signal in practice. Reported per
the review's uncertain-finding contract rather than edited.

Worth a human/reviewer look at whether tightening the grep's scope (e.g.
requiring the anchor and marker to appear within N lines of the specific
criterion line, not just anywhere in the file) meaningfully raises this
grader's rigor, or whether the current looseness is an acceptable
tradeoff given the non-adversarial subject.

## Resolution (done)

Tightened, at the Acceptance-section granularity rather than the
N-lines-proximity granularity the finding floated. Both marker greps now
run against the already-extracted `$accept` (acceptance-section body),
not the whole `$spec`:

- `/idea` records the `verified <date>` anchor note and the `Depth
  ceiling:` line inline WITH the criterion they annotate, in the
  Acceptance section (SKILL.md step 3 + step 4). So a marker appearing
  only in Problem/Requirements no longer anchors the acceptance criterion
  under test — the exact false-pass the finding named.
- Section-scoping was chosen over an arbitrary N-line proximity window:
  the subject is the real (non-adversarial) `/idea` skill, and a
  line-proximity window would risk false-FAILing legitimate output whose
  annotation sits a few lines from its criterion. Acceptance-section scope
  captures the real rigor gain (markers-elsewhere-in-file no longer count)
  with no false-fail risk, since the skill's own procedure puts both
  markers in that section.

Verified with throwaway fixtures (no paid eval run needed): an unanchored
grep criterion whose markers live only in Problem now FAILS both
anti-pattern checks (previously passed); a legitimately anchored criterion
and a no-grep-criterion spec both still PASS. Change confined to
`evals/idea/02-adv-doctrine-grep/assert.sh`; no antigravity/codex mirror
of the `evals/` scenario tree exists, so no mirror obligation.
