package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
)

// writeOutcomeSkillMD writes a SKILL.md with the given raw frontmatter+body
// under <cwd>/.claude/skills/<name>/SKILL.md and returns its path. It is named
// distinctly from task 02's writeSkillMD so this file compiles whether or not
// cmd_skillcheck_trigger_test.go is present in the tree (both are package main).
func writeOutcomeSkillMD(t *testing.T, name, content string) string {
	t.Helper()
	dir := filepath.Join(t.TempDir(), ".claude", "skills", name)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "SKILL.md")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

// scriptedOutcomeJudge is a test judge that returns a fixed sequence of replies
// (one per call, in order) and records every prompt/tier it was called with, so
// tests can assert both the per-call count and the exact prompt text. A shared
// judge.Fake cannot express per-call replies, which the 3-call generic rubric
// aggregation cases require.
type scriptedOutcomeJudge struct {
	replies []string
	prompts []string
	tiers   []string
}

func (s *scriptedOutcomeJudge) Judge(prompt, tier string) (string, error) {
	reply := "unknown"
	if len(s.prompts) < len(s.replies) {
		reply = s.replies[len(s.prompts)]
	}
	s.prompts = append(s.prompts, prompt)
	s.tiers = append(s.tiers, tier)
	return reply, nil
}

const outcomeRubricSkillMD = `---
description: Works the remaining task queue unattended.
outcome-rubric: |
  A successful drain merges each task's branch to the default branch with
  green gates; a run that only defers or blocks every task is not a success.
---

Body.
`

func skillMDNoRubric(description string) string {
	return "---\ndescription: " + description + "\n---\n\nBody.\n"
}

// assertAntiClosingInstruction fails unless every recorded prompt carries R7's
// explicit "do not trust the closing message; require concrete evidence"
// instruction, asserted on the judge's actual input rather than any report field.
func assertAntiClosingInstruction(t *testing.T, prompts []string) {
	t.Helper()
	if len(prompts) == 0 {
		t.Fatal("no judge prompts were recorded")
	}
	for i, p := range prompts {
		lower := strings.ToLower(p)
		if !strings.Contains(lower, "do not trust") {
			t.Errorf("prompt %d missing 'do not trust' anti-closing instruction:\n%s", i, p)
		}
		if !strings.Contains(lower, "closing message") {
			t.Errorf("prompt %d does not name the 'closing message':\n%s", i, p)
		}
		if !strings.Contains(lower, "concrete") {
			t.Errorf("prompt %d does not demand 'concrete' in-transcript evidence:\n%s", i, p)
		}
	}
}

func TestClassifyOutcomeCustomRubricIsSingleCallOverFullText(t *testing.T) {
	path := writeOutcomeSkillMD(t, "drain", outcomeRubricSkillMD)
	inv := claude.SkillInvocation{Name: "drain", Result: "Merged task 03; gates green."}
	j := &scriptedOutcomeJudge{replies: []string{"success"}}

	got, err := ClassifyOutcome(inv, path, j, "scout")
	if err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	if got != OutcomeSuccess {
		t.Errorf("class = %q, want success", got)
	}
	if len(j.prompts) != 1 {
		t.Fatalf("custom rubric made %d judge calls, want exactly 1", len(j.prompts))
	}
	// The single custom call must carry the rubric's full text.
	if !strings.Contains(j.prompts[0], "merges each task's branch") {
		t.Errorf("custom-rubric prompt does not contain the rubric text:\n%s", j.prompts[0])
	}
	// It must NOT fall back to the generic rubric's wording.
	if strings.Contains(strings.ToLower(j.prompts[0]), "correction or redo") {
		t.Errorf("custom-rubric prompt leaked generic rubric wording:\n%s", j.prompts[0])
	}
	assertAntiClosingInstruction(t, j.prompts)
}

func TestClassifyOutcomeAbsentRubricRoutesToThreeGenericCalls(t *testing.T) {
	path := writeOutcomeSkillMD(t, "build", skillMDNoRubric("Executes one task file end to end."))
	inv := claude.SkillInvocation{Name: "build", Result: "Task complete."}
	j := &scriptedOutcomeJudge{replies: []string{"yes", "no", "no"}}

	got, err := ClassifyOutcome(inv, path, j, "scout")
	if err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	if len(j.prompts) != 3 {
		t.Fatalf("generic rubric made %d judge calls, want exactly 3 (one per dimension)", len(j.prompts))
	}
	if got != OutcomeSuccess {
		t.Errorf("class = %q, want success for yes/no/no", got)
	}
	assertAntiClosingInstruction(t, j.prompts)
}

func TestClassifyOutcomeGenericAllAffirmYieldsSuccess(t *testing.T) {
	path := writeOutcomeSkillMD(t, "build", skillMDNoRubric("Executes one task file."))
	inv := claude.SkillInvocation{Name: "build", Result: "Done, tests pass."}
	// terminal non-error = yes; error signal present = no; redo shortly after = no.
	j := &scriptedOutcomeJudge{replies: []string{"yes", "no", "no"}}

	got, err := ClassifyOutcome(inv, path, j, "scout")
	if err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	if got != OutcomeSuccess {
		t.Errorf("class = %q, want success", got)
	}
}

func TestClassifyOutcomeGenericErrorSignalYieldsFailure(t *testing.T) {
	path := writeOutcomeSkillMD(t, "build", skillMDNoRubric("Executes one task file."))
	inv := claude.SkillInvocation{Name: "build", Result: "BLOCKED: cannot proceed."}
	// terminal non-error = yes, but an explicit error/blocked signal = yes -> failure dominates.
	j := &scriptedOutcomeJudge{replies: []string{"yes", "yes", "no"}}

	got, err := ClassifyOutcome(inv, path, j, "scout")
	if err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	if got != OutcomeFailure {
		t.Errorf("class = %q, want failure (any-failure-dominates)", got)
	}
}

func TestClassifyOutcomeGenericUnknownDimensionYieldsUnknown(t *testing.T) {
	path := writeOutcomeSkillMD(t, "build", skillMDNoRubric("Executes one task file."))
	inv := claude.SkillInvocation{Name: "build", Result: "..."}
	// no failure anywhere, but one dimension is unknown -> overall unknown.
	j := &scriptedOutcomeJudge{replies: []string{"unknown", "no", "no"}}

	got, err := ClassifyOutcome(inv, path, j, "scout")
	if err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	if got != OutcomeUnknown {
		t.Errorf("class = %q, want unknown", got)
	}
}

func TestClassifyOutcomeCustomRubricUnknownReply(t *testing.T) {
	path := writeOutcomeSkillMD(t, "drain", outcomeRubricSkillMD)
	inv := claude.SkillInvocation{Name: "drain", Result: "Ambiguous."}
	j := &scriptedOutcomeJudge{replies: []string{"unknown"}}

	got, err := ClassifyOutcome(inv, path, j, "scout")
	if err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	if got != OutcomeUnknown {
		t.Errorf("class = %q, want unknown", got)
	}
}

func TestClassifyOutcomePassesTierThrough(t *testing.T) {
	path := writeOutcomeSkillMD(t, "build", skillMDNoRubric("Executes one task file."))
	inv := claude.SkillInvocation{Name: "build", Result: "Done."}
	j := &scriptedOutcomeJudge{replies: []string{"yes", "no", "no"}}

	if _, err := ClassifyOutcome(inv, path, j, "opus"); err != nil {
		t.Fatalf("ClassifyOutcome: %v", err)
	}
	for i, tier := range j.tiers {
		if tier != "opus" {
			t.Errorf("call %d used tier %q, want the caller-supplied opus", i, tier)
		}
	}
}
