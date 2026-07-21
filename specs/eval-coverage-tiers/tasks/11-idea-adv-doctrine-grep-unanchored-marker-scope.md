Status: draft
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
