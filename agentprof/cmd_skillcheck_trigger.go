package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

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

// triggerJudgeTier is the deep tier used for the trigger-correctness judgment.
const triggerJudgeTier = "opus"

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

// resolve returns the SKILL.md path for a skill name, trying the cwd-relative
// path first and the plugin cache (marketplace/plugin globbed) second.
func (r Resolver) resolve(name string) (string, bool) {
	local := filepath.Join(r.Cwd, ".claude", "skills", name, "SKILL.md")
	if isFile(local) {
		return local, true
	}
	matches, _ := filepath.Glob(filepath.Join(r.PluginCacheRoot, "*", "*", "skills", name, "SKILL.md"))
	for _, m := range matches {
		if isFile(m) {
			return m, true
		}
	}
	return "", false
}

// installedSkillPaths enumerates every currently-installed skill's SKILL.md
// across both the cwd-relative and plugin-cache layouts.
func (r Resolver) installedSkillPaths() []string {
	var paths []string
	local, _ := filepath.Glob(filepath.Join(r.Cwd, ".claude", "skills", "*", "SKILL.md"))
	paths = append(paths, local...)
	plugin, _ := filepath.Glob(filepath.Join(r.PluginCacheRoot, "*", "*", "skills", "*", "SKILL.md"))
	paths = append(paths, plugin...)
	return paths
}

// ClassifyTriggers classifies each invocation into exactly one TriggerClass.
// The population split runs first (explicit-slash-command, then self-chain); the
// remaining model-auto-trigger population is resolved to its SKILL.md and either
// exempted (disable-model-invocation), marked unresolvable, or scored by the judge.
func ClassifyTriggers(inputs []TriggerInput, r Resolver, j judge.Judge) ([]TriggerResult, error) {
	out := make([]TriggerResult, 0, len(inputs))
	for _, in := range inputs {
		res := TriggerResult{Name: in.Invocation.Name}
		switch {
		case in.Invocation.CommandTag != "":
			res.Class = ClassExplicitInvocation
		case !in.Invocation.PrecededByUserTurn:
			res.Class = ClassSelfChained
		default:
			path, ok := r.resolve(in.Invocation.Name)
			if !ok {
				res.Class = ClassUnresolvable
				break
			}
			fm, err := claude.SkillFrontmatter(path)
			if err != nil {
				return nil, err
			}
			if fm.DisableModelInvocation {
				res.Class = ClassExplicitInvocation
				break
			}
			res.Description = fm.Description
			reply, err := j.Judge(triggerPrompt(fm.Description, in.UserTurn), triggerJudgeTier)
			if err != nil {
				return nil, err
			}
			if judgedCorrect(reply) {
				res.Class = ClassCorrectlyTriggered
			} else {
				res.Class = ClassMisfired
			}
		}
		out = append(out, res)
	}
	return out, nil
}

// triggerPrompt builds the trigger-correctness grading prompt, grounding the
// judgment in the skill's actual description and the preceding user turn.
func triggerPrompt(description, userTurn string) string {
	return fmt.Sprintf(`A skill was auto-triggered by the model. Decide whether the trigger was a good fit.

Skill description (its declared purpose and trigger phrases):
%s

Preceding user turn(s):
%s

Answer with exactly one word: "correctly-triggered" if the user turn is a good fit for this skill's description, or "misfired" if it is not.`, description, userTurn)
}

// judgedCorrect reads the judge's verdict text, treating an affirmative reply as
// a correct trigger. It parses structure rather than an exact string.
func judgedCorrect(reply string) bool {
	r := strings.ToLower(strings.TrimSpace(reply))
	if strings.Contains(r, "misfire") {
		return false
	}
	return strings.Contains(r, "correct") || strings.HasPrefix(r, "yes")
}

// PossibleMiss is one user turn whose text matched an installed skill's declared
// trigger phrase without a corresponding Skill invocation.
type PossibleMiss struct {
	UserTurn string
	Skill    string
	Phrase   string
}

// DetectPossibleMisses flags non-triggering user turns that match an installed
// skill's declared trigger phrase, via deterministic substring matching only
// (no judge call). Trigger phrases are the double-quoted spans in each installed
// skill's description.
func DetectPossibleMisses(userTurns []string, r Resolver) ([]PossibleMiss, error) {
	type installedSkill struct {
		name    string
		phrases []string
	}
	var installed []installedSkill
	for _, path := range r.installedSkillPaths() {
		fm, err := claude.SkillFrontmatter(path)
		if err != nil {
			return nil, err
		}
		installed = append(installed, installedSkill{
			name:    filepath.Base(filepath.Dir(path)),
			phrases: quotedPhrases(fm.Description),
		})
	}

	var misses []PossibleMiss
	for _, turn := range userTurns {
		lower := strings.ToLower(turn)
		for _, s := range installed {
			for _, ph := range s.phrases {
				if ph == "" {
					continue
				}
				if strings.Contains(lower, strings.ToLower(ph)) {
					misses = append(misses, PossibleMiss{UserTurn: turn, Skill: s.name, Phrase: ph})
					break
				}
			}
		}
	}
	return misses, nil
}

// quotedPhrases extracts the double-quoted spans from a description, the
// deterministic proxy for a skill's declared trigger phrases.
func quotedPhrases(description string) []string {
	var phrases []string
	rest := description
	for {
		i := strings.IndexByte(rest, '"')
		if i < 0 {
			break
		}
		rest = rest[i+1:]
		j := strings.IndexByte(rest, '"')
		if j < 0 {
			break
		}
		if ph := strings.TrimSpace(rest[:j]); ph != "" {
			phrases = append(phrases, ph)
		}
		rest = rest[j+1:]
	}
	return phrases
}

// isFile reports whether path exists and is a regular file.
func isFile(path string) bool {
	info, err := os.Stat(path)
	return err == nil && !info.IsDir()
}
