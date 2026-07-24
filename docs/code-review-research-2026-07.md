# Automated Code Review at Frontier Labs (2026-07)

> Targeted-research run 2026-07-24 (two web agents under factcheck
> discipline: every claim carries a verbatim quote from a primary source or
> is marked UNVERIFIED). Commissioned to align this toolkit's review path —
> the `critic` agent and `/critique` — with how the labs run automated code
> review. The adopted doctrine lands in `.claude/rules/quality-discipline.md`
> ("Self-documenting code") and `.claude/agents/critic.md` (the diff
> rubric's code-health dimension); this file is the evidence, not the rule.
> Anthropic's own internal pipeline is already documented in
> docs/anthropic-playbook.md ("Multi-agent review with aggressive
> false-positive filtering") — this survey adds the cross-lab picture.

## Summary

The labs converge on one economics: an automated reviewer is optimized for
precision over recall, because false positives spend the scarcest resource —
developer trust — faster than missed bugs spend anything. Anthropic ships a
pipeline with a dedicated false-positive filtering stage and wholesale
exclusion of FP-prone finding classes; OpenAI states the trade as an explicit
utility function and accepts "modestly reduced recall in exchange for high
signal quality and developer trust". Both give the reviewer fresh context
(never the model that wrote the code), whole-repo access rather than
diff-only reading, severity-ranked findings, and an advisory posture — the
reviewer comments, humans merge. Success is measured by author behavior
(fix rate, reactions), not finding counts. Style is delegated to
deterministic tools; GitHub Copilot, which keeps style in scope, is the
counterexample among the surveyed systems, not the pattern.

What the LLM reviewers inherit their rubric from is Google's classical
review doctrine: a reviewer covers design, functionality, complexity, tests,
naming, comments, style, consistency, and documentation — and on comments
and naming Google is categorical: comments explain _why_, never _what_, and
code too unclear to explain itself "should be made simpler", not commented.
The Go guidelines sharpen the naming half into a context rule — a name is
read together with its package, type, and scope, so it repeats none of that
context and its length is proportional to its distance from the declaration.
Meta shows the scale end: risk-scored LLM review landing hundreds of
thousands of diffs with lower revert rates than the human-review baseline.

## Verified findings

### Anthropic: a pipeline stage exists solely to kill false positives

The claude-code-security-review GitHub Action runs five stages — PR
analysis, contextual review, finding generation ("severity ratings, and
remediation guidance"), then "False Positive Filtering: Advanced filtering
removes low-impact or false positive prone findings to reduce noise", then
line-anchored PR comments. Filtering is partly a wholesale class exclusion:
it "automatically excludes" DoS, rate limiting, memory/CPU exhaustion,
"Generic input validation without proven impact", and open redirects. The
reviewer is semantic, not pattern-based ("Understands code semantics and
intent, not just patterns") and diff-scoped for cost ("For PRs, only
analyzes changed files").
(github.com/anthropics/claude-code-security-review)

Their best-practices guidance sets the reviewer's stance: "A fresh context
improves code review since Claude won't be biased toward code it just
wrote"; a verification subagent "has a fresh model try to refute the result,
so the agent doing the work isn't the one grading it"; and against noise,
"Report gaps, not style preferences" — "A reviewer prompted to find gaps
will usually report some, even when the work is sound".
(code.claude.com/docs/en/best-practices)

Dogfooding evidence from the /security-review launch post: the flow caught a
remote code execution vulnerability "exploitable through DNS rebinding" in
an internal tool before merge. (claude.com/blog/automate-security-reviews-with-claude-code)

### OpenAI: precision over recall as an explicit utility function

OpenAI's code-verification write-up states the objective outright: a finding
is worth surfacing when it maximizes "P(correct) × C_saved - C_human
verification - P(incorrect) × C_false alarm", and they accepted "modestly
reduced recall in exchange for high signal quality and developer trust" —
"We optimize for signal-to-noise first, and only then push recall without
compromising reliability." The reviewer gets full context and a shell:
"Repo-wide tools and execution are necessary"; "repo-aware reviewers with
tool access can deliver reliable, high-signal feedback without slowing teams
down." Success is measured by what authors do: "authors address it with a
code change in 52.7% of cases", with "over 80% of comment reactions being
positive". The adoption thesis: "Safety requires adoption, so we optimize
the reviewer for low safety tax and high precision, earning user trust."
(alignment.openai.com/scaling-code-verification/)

### GitHub Copilot: style in scope, advisory-only, repo-tunable

Copilot code review flags "common issues such as bugs, security
vulnerabilities, and style inconsistencies" — style explicitly in scope,
unlike the labs. Its posture is strictly advisory: "Copilot always leaves a
'Comment' review, not an 'Approve' review or a 'Request changes' review",
and it never blocks merging. Repo-level tuning goes in
`.github/copilot-instructions.md` plus path-specific instruction files. A
documented weakness: it "may repeat the same comments again, even if they
have been dismissed". (docs.github.com/en/copilot/concepts/code-review)

### Google: the reviewer rubric, and comments as a simplicity signal

Google's eng-practices define review's purpose — "to make sure that the
overall code health of Google's code base is improving over time" — and its
bar: "reviewers should favor approving a CL once it is in a state where it
definitely improves the overall code health of the system being worked on,
even if the CL isn't perfect." The reviewer's checklist spans design,
functionality, complexity, tests, naming, comments, style, consistency, and
documentation. On naming: "A good name is long enough to fully communicate
what the item is or does, without being so long that it becomes hard to
read." On comments: they "should not be explaining what some code is doing.
If the code isn't clear enough to explain itself, then the code should be
made simpler … mostly comments are for information that the code itself
can't possibly contain, like the reasoning behind a decision" — with regular
expressions and complex algorithms named as the exceptions.
(google.github.io/eng-practices/review/reviewer/standard.html,
google.github.io/eng-practices/review/reviewer/looking-for.html)

On the ML side, Google integrated a DIDACT-based model into Critique that
proposes edits resolving reviewer comments: it "addresses 52% of comments
with a target precision of 50%", and "40% to 50% of all previewed suggested
edits are applied by code authors" — projected to save "hundreds of
thousands of hours annually".
(research.google/blog/resolving-code-review-comments-with-ml/)

### Go doctrine: a name accounts for its surrounding context

Effective Go: "The importer of a package will use the name to refer to its
contents, so exported names in the package can use that fact to avoid
repetition" — bufio's reader is `bufio.Reader`, not `BufReader`; the
constructor is `ring.New`, not `NewRing`. The Go wiki's CodeReviewComments
makes the anti-stutter rule concrete: in package chubby, "name the type
File, which clients will write as chubby.File", never `chubby.ChubbyFile` —
and gives the scope rule: "The basic rule: the further from its declaration
that a name is used, the more descriptive the name must be." The Google Go
Style Guide generalizes both: "The length of a name should be proportional
to the size of its scope and inversely proportional to the number of times
that it is used within that scope", and "Names that include information from
their surrounding context often create extra noise without benefit."
(go.dev/doc/effective_go, go.dev/wiki/CodeReviewComments,
google.github.io/styleguide/go/decisions)

### Meta: risk-scored LLM review at production scale

Meta's baseline is universal review — "Every diff must be reviewed, without
exception" (engineering.fb.com, 2022). RADAR, their LLM reviewer with risk
scoring for low-risk diffs, "has reviewed 535K+ diffs and landed 331K+",
with a revert rate a third of non-RADAR diffs and an incident rate of 1/50
the baseline (arxiv.org/abs/2605.30208). MetaMateCR, their comment-fixing
model, produces an exact-match patch 68% of the time, with a production
ActionableToApplied rate of 19.7% — and an instructive UX finding: showing
AI patches to _reviewers_ made reviews slower, fixed by showing patches only
to authors (arxiv.org/abs/2507.13499).

## Distilled design principles

1. Precision over recall — optimize signal-to-noise first; accept missed
   bugs to keep developer trust (OpenAI's utility function, Anthropic's
   high-signal rule).
2. Bugs and doctrine violations over style preferences — style belongs to
   deterministic tools (formatters, linters, hooks); Copilot is the
   counterexample, not the pattern.
3. A dedicated false-positive filtering stage after finding generation,
   plus wholesale exclusion of FP-prone finding classes.
4. Severity/priority-rank every finding, each with an explanation and the
   smallest remediation.
5. Whole-repo context and tool access — validate hypotheses against the
   codebase, not the diff text alone; diff-scoped for cost.
6. Fresh, independent reviewer context — never the model that wrote the
   code; adversarial "try to refute" framing for verification.
7. Semantic intent analysis, not pattern matching.
8. Measure by author actions (fix rate, reactions), never finding counts.
9. Advisory posture — the reviewer comments; humans approve and merge.
10. Repo-tunable policy via instruction files the reviewer reads.

## What the toolkit already does, and what this run added

The critic agent already matches the lab pattern: a fresh-context
adversarial reviewer (deep-tier pin), a hard high-signal rule with a
confidence floor (≥80 for diffs), a never-flag list (linter-catchable
issues, pre-existing problems, pedantic nitpicks, speculative inputs),
findings ranked by cost-if-missed with the smallest fix, and an advisory
verdict a human acts on. The ultra panel adds the parallel-finders →
adversarial-verify shape of Anthropic's shipped pipeline.

What was missing was the classical code-health dimension every human rubric
carries — Google's naming and comments items. This run added it to the
critic's diff rubric as doctrine-backed checks (not style preference):
comments outside public surface area are defect signals, a function body
must never surprise a reader of its signature, and names must account for
their surrounding context. The binding rule is
`.claude/rules/quality-discipline.md` ("Self-documenting code"); the critic
cites it, and this file holds the external evidence.

## Caveats

- The Codex launch post (openai.com/index/introducing-upgrades-to-codex/)
  returned HTTP 403 during research; its widely-reported stats (Codex
  reviewing the majority of OpenAI's internal PRs) are UNVERIFIED here.
- Codex CLI's P1/P2/P3 finding labels: UNVERIFIED.
- The claim that OpenAI's reviewer writes code to test its own hypotheses is
  search-result synthesis of the alignment post, not a verbatim quote.
- Meta's RADAR/MetaMateCR figures are from the papers' own claims; no
  independent replication was checked.
