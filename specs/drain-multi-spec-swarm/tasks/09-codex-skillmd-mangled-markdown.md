Status: draft
Discovered-from: specs/drain-multi-spec-swarm/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# codex SKILL.md's new "Admission command" block has mangled markdown

`codex/.agents/skills/drain/SKILL.md`'s new "Admission command" block has
a blank line falling inside an opening inline-code span, so a line
renders as a stray list item and the code span reopens mid-sentence;
several backticked tokens also lost their surrounding spaces (words run
together, e.g. a closing backtick immediately followed by the next
backtick-opened token with no space). All the words are present, just
mis-structured — this is a formatting defect, not a content gap. The
parallel `antigravity/.agents/workflows/drain.md` block does not have
this problem (only a harmless line break inside a code span). (Reported
by the drain-multi-spec-swarm spec-completion review — excluded from that
review's fix scope as a style/formatting finding, not correctness/
behavior; vet/rewrite before promoting.)

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
