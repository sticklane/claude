package main

import (
	"fmt"
	"strings"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/judge"
)

// OutcomeClass scores how well one already-`correctly-triggered` Skill
// invocation actually landed, on the outcome axis (kept separate from the
// trigger axis per SPEC R6/the two-axis research finding).
type OutcomeClass string

const (
	// OutcomeSuccess marks an invocation whose applicable rubric affirms it
	// landed a real, terminal, uncorrected outcome.
	OutcomeSuccess OutcomeClass = "success"
	// OutcomeFailure marks an invocation the rubric found did not land.
	OutcomeFailure OutcomeClass = "failure"
	// OutcomeUnknown marks an invocation the rubric could not confidently score
	// (R8: any dimension may abstain rather than force success/failure).
	OutcomeUnknown OutcomeClass = "unknown"
)

// defaultOutcomeJudgeTier is the tier used when a caller supplies none; R9's
// `--judge-tier` (wired in task 04) overrides it by passing a tier to
// ClassifyOutcome. Kept as documentation of the SPEC default.
const defaultOutcomeJudgeTier = "scout"

// outcomeAntiClosingInstruction is R7's load-bearing anti-false-success
// instruction, embedded verbatim in EVERY outcome-judge prompt (generic and
// custom). LLM judges anchor on confident closing language as a completion
// signal; this forces them to look for concrete in-transcript evidence instead.
const outcomeAntiClosingInstruction = "Do not trust the invocation's own closing message as evidence of success. " +
	"An assertive final statement claiming the work is done is NOT sufficient. Require concrete evidence in the " +
	"transcript body — a verifier's PASS, a passing test run, a merged commit, ticked acceptance boxes with cited " +
	"commands. If that concrete evidence is absent, do not score it a success."

// genericDimension is one of the three fixed generic-rubric questions. yesIsGood
// records the question's polarity: a "yes" answer to a yesIsGood dimension is a
// success signal; a "yes" to a non-yesIsGood dimension (an error signal, a redo)
// is a failure signal.
type genericDimension struct {
	question  string
	yesIsGood bool
}

// genericDimensions are SPEC's three generic-rubric questions, each judged as a
// separate call (R8): terminal non-error state, explicit error/blocked/deferred
// signal, and a user correction/redo shortly after.
var genericDimensions = []genericDimension{
	{question: "Did the invocation reach a terminal, non-error state — not left mid-flight, not silently abandoned?", yesIsGood: true},
	{question: "Was there an explicit error, blocked, deferred, or DEFERRED signal in the transcript for this invocation?", yesIsGood: false},
	{question: "Was there a user correction or a redo of the same request shortly after this invocation (a signal the first attempt did not actually satisfy the user)?", yesIsGood: false},
}

// ClassifyOutcome scores one `correctly-triggered` invocation's outcome. It reads
// the invoked skill's `outcome-rubric:` via task 01's shared frontmatter parser:
// when present, ONE judge call over the rubric's full text decides the outcome
// (R6); when absent, the three generic-rubric questions are three separate judge
// calls (R8) aggregated by an any-failure-dominates rule (see aggregateGeneric).
// tier is the caller-supplied judge tier (R9); "" falls back to the SPEC default.
func ClassifyOutcome(inv claude.SkillInvocation, skillPath string, j judge.Judge, tier string) (OutcomeClass, error) {
	if tier == "" {
		tier = defaultOutcomeJudgeTier
	}
	fm, err := claude.SkillFrontmatter(skillPath)
	if err != nil {
		return OutcomeUnknown, err
	}
	if strings.TrimSpace(fm.OutcomeRubric) != "" {
		return classifyCustomOutcome(inv, fm.OutcomeRubric, j, tier)
	}
	return classifyGenericOutcome(inv, j, tier)
}

// classifyCustomOutcome runs the single custom-rubric judge call (R6: a custom
// `outcome-rubric:` is judged as ONE dimension, replacing all three generic calls).
func classifyCustomOutcome(inv claude.SkillInvocation, rubric string, j judge.Judge, tier string) (OutcomeClass, error) {
	reply, err := j.Judge(customOutcomePrompt(inv, rubric), tier)
	if err != nil {
		return OutcomeUnknown, err
	}
	return parseOutcomeReply(reply), nil
}

// classifyGenericOutcome runs the three generic-rubric questions as three
// separate judge calls and aggregates them.
func classifyGenericOutcome(inv claude.SkillInvocation, j judge.Judge, tier string) (OutcomeClass, error) {
	verdicts := make([]OutcomeClass, 0, len(genericDimensions))
	for _, dim := range genericDimensions {
		reply, err := j.Judge(genericOutcomePrompt(inv, dim), tier)
		if err != nil {
			return OutcomeUnknown, err
		}
		verdicts = append(verdicts, dimensionVerdict(dim, reply))
	}
	return aggregateGeneric(verdicts), nil
}

// aggregateGeneric folds the three per-dimension verdicts into one outcome.
//
// Rule (any-failure-dominates, unknown over success under uncertainty): the SPEC
// does not pin the 3-call aggregation, so it is fixed here, local to this task:
//   - failure if ANY dimension signals failure — a single concrete failure
//     signal outweighs the others, matching R7's anti-false-success bias (err
//     toward catching a failure, never toward claiming a success);
//   - else unknown if ANY dimension abstained — no failure, but incomplete
//     evidence, so refuse to assert success (R8's hallucination suppression);
//   - else success — all three dimensions affirmatively indicate a clean,
//     terminal, uncorrected outcome.
func aggregateGeneric(verdicts []OutcomeClass) OutcomeClass {
	sawUnknown := false
	for _, v := range verdicts {
		switch v {
		case OutcomeFailure:
			return OutcomeFailure
		case OutcomeUnknown:
			sawUnknown = true
		}
	}
	if sawUnknown {
		return OutcomeUnknown
	}
	return OutcomeSuccess
}

// dimensionVerdict maps a judge's yes/no/unknown reply to a success/failure/
// unknown verdict for one generic dimension, honoring the dimension's polarity.
func dimensionVerdict(dim genericDimension, reply string) OutcomeClass {
	switch parseTernary(reply) {
	case ternaryUnknown:
		return OutcomeUnknown
	case ternaryYes:
		if dim.yesIsGood {
			return OutcomeSuccess
		}
		return OutcomeFailure
	default: // ternaryNo
		if dim.yesIsGood {
			return OutcomeFailure
		}
		return OutcomeSuccess
	}
}

type ternary int

const (
	ternaryNo ternary = iota
	ternaryYes
	ternaryUnknown
)

// parseTernary reads a yes/no/unknown judge reply by structure (first meaningful
// token, then substring), never an exact-string match, mirroring the trigger
// judge's tolerant parsing. An unrecognized reply is treated as "no" (the
// conservative choice: a non-affirmative reply is not evidence of success).
func parseTernary(reply string) ternary {
	r := strings.ToLower(strings.TrimSpace(reply))
	if strings.HasPrefix(r, "unknown") || strings.Contains(r, "unknown") || strings.Contains(r, "cannot tell") || strings.Contains(r, "unclear") {
		return ternaryUnknown
	}
	if strings.HasPrefix(r, "yes") || strings.Contains(r, "yes") {
		return ternaryYes
	}
	return ternaryNo
}

// parseOutcomeReply reads a custom-rubric reply as success/failure/unknown
// directly, by structure. An unrecognized reply is treated as unknown so an
// unparseable custom judgment never silently reads as success.
func parseOutcomeReply(reply string) OutcomeClass {
	r := strings.ToLower(strings.TrimSpace(reply))
	if strings.HasPrefix(r, "unknown") || strings.Contains(r, "unknown") {
		return OutcomeUnknown
	}
	if strings.HasPrefix(r, "success") || strings.Contains(r, "success") {
		return OutcomeSuccess
	}
	if strings.HasPrefix(r, "failure") || strings.Contains(r, "fail") {
		return OutcomeFailure
	}
	return OutcomeUnknown
}

// invocationEvidence renders the concrete transcript evidence available for one
// invocation — its name, args, and paired tool_result text — for a judge prompt.
func invocationEvidence(inv claude.SkillInvocation) string {
	var b strings.Builder
	fmt.Fprintf(&b, "Skill invoked: %s\n", inv.Name)
	if strings.TrimSpace(inv.Args) != "" {
		fmt.Fprintf(&b, "Args: %s\n", inv.Args)
	}
	fmt.Fprintf(&b, "Invocation result / transcript excerpt:\n%s", inv.Result)
	return b.String()
}

// customOutcomePrompt builds the single custom-rubric grading prompt over the
// rubric's full text, carrying the R7 anti-closing-message instruction.
func customOutcomePrompt(inv claude.SkillInvocation, rubric string) string {
	return fmt.Sprintf(`Score whether this skill invocation actually landed a successful outcome, judged against the skill's own success rubric below.

%s

Skill's success rubric:
%s

%s

Answer with exactly one word: "success", "failure", or "unknown".`,
		invocationEvidence(inv), rubric, outcomeAntiClosingInstruction)
}

// genericOutcomePrompt builds one generic-dimension grading prompt, carrying the
// R7 anti-closing-message instruction.
func genericOutcomePrompt(inv claude.SkillInvocation, dim genericDimension) string {
	return fmt.Sprintf(`Score one aspect of whether this skill invocation actually landed a successful outcome.

%s

Question: %s

%s

Answer with exactly one word: "yes", "no", or "unknown".`,
		invocationEvidence(inv), dim.question, outcomeAntiClosingInstruction)
}
