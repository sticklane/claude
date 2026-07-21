package main

import (
	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/judge"
)

// TriggerClass labels how a single Skill invocation was decided.
type TriggerClass string

const (
	// ClassCorrectlyTriggered marks a model-auto-trigger the judge deemed a good fit.
	ClassCorrectlyTriggered TriggerClass = "correctly-triggered"
	// ClassMisfired marks a model-auto-trigger the judge deemed a bad fit.
	ClassMisfired TriggerClass = "misfired"
	// ClassUnresolvable marks an invocation whose SKILL.md was not found at either path.
	ClassUnresolvable TriggerClass = "unresolvable"
	// ClassExplicitInvocation marks a slash-command or disable-model-invocation invocation.
	ClassExplicitInvocation TriggerClass = "explicit_invocation"
	// ClassSelfChained marks an invocation with no user turn since the previous one.
	ClassSelfChained TriggerClass = "self_chained"
)

// TriggerResult is one invocation's classification, plus the resolved description
// (populated only for the model-auto-trigger population that reached the judge).
type TriggerResult struct {
	Name        string
	Class       TriggerClass
	Description string
}

// TriggerInput pairs a task-01 SkillInvocation with the text of the user turn(s)
// that preceded it. SkillInvocation itself carries no user-turn text, so the
// caller supplies it here for the trigger-correctness judge comparison.
type TriggerInput struct {
	Invocation claude.SkillInvocation
	UserTurn   string
}

// Resolver locates a skill's SKILL.md by the two-path resolution order the spec
// fixes: cwd-relative .claude/skills, then the plugin cache.
type Resolver struct {
	Cwd             string
	PluginCacheRoot string
}

// ClassifyTriggers classifies each invocation into exactly one TriggerClass.
func ClassifyTriggers(inputs []TriggerInput, r Resolver, j judge.Judge) ([]TriggerResult, error) {
	return nil, nil
}

// PossibleMiss is one user turn whose text matched an installed skill's declared
// trigger phrase without a corresponding Skill invocation.
type PossibleMiss struct {
	UserTurn string
	Skill    string
	Phrase   string
}

// DetectPossibleMisses flags non-triggering user turns that match an installed
// skill's declared trigger phrase, via deterministic substring matching only.
func DetectPossibleMisses(userTurns []string, r Resolver) ([]PossibleMiss, error) {
	return nil, nil
}
