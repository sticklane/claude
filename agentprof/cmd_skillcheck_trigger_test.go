package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/judge"
)

// writeSkillMD writes a SKILL.md with the given frontmatter body under
// <skillsDir>/<name>/SKILL.md.
func writeSkillMD(t *testing.T, skillsDir, name, content string) {
	t.Helper()
	dir := filepath.Join(skillsDir, name)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SKILL.md"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

// localSkillsDir returns the cwd-relative .claude/skills dir for a Resolver rooted at cwd.
func localSkillsDir(cwd string) string {
	return filepath.Join(cwd, ".claude", "skills")
}

// pluginSkillsDir returns a plugin-cache skills dir (<root>/<mkt>/<plugin>/skills).
func pluginSkillsDir(root string) string {
	return filepath.Join(root, "acme-marketplace", "acme-plugin", "skills")
}

func skillMD(description string, disableModelInvocation bool) string {
	dmi := "false"
	if disableModelInvocation {
		dmi = "true"
	}
	return "---\ndescription: " + description + "\ndisable-model-invocation: " + dmi + "\n---\n\nBody.\n"
}

func TestClassifyTriggerExplicitViaCommandTag(t *testing.T) {
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "drain", CommandTag: "drain", PrecededByUserTurn: true},
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: t.TempDir(), PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Class != ClassExplicitInvocation {
		t.Fatalf("class = %v, want explicit_invocation", got)
	}
	if len(fake.Calls) != 0 {
		t.Errorf("judge called %d times for an explicit invocation, want 0", len(fake.Calls))
	}
}

func TestClassifyTriggerSelfChainedNoPrecedingUserTurn(t *testing.T) {
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "distill", CommandTag: "", PrecededByUserTurn: false},
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: t.TempDir(), PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Class != ClassSelfChained {
		t.Fatalf("class = %v, want self_chained", got)
	}
	if len(fake.Calls) != 0 {
		t.Errorf("judge called %d times for a self-chain, want 0", len(fake.Calls))
	}
}

func TestClassifyTriggerDisableModelInvocationExempt(t *testing.T) {
	cwd := t.TempDir()
	writeSkillMD(t, localSkillsDir(cwd), "evals", skillMD("Runs the eval harness.", true))
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "evals", CommandTag: "", PrecededByUserTurn: true},
		UserTurn:   "please run the evals",
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Class != ClassExplicitInvocation {
		t.Fatalf("class = %v, want explicit_invocation for disable-model-invocation skill", got)
	}
	if len(fake.Calls) != 0 {
		t.Errorf("judge called %d times for a disable-model-invocation skill, want 0", len(fake.Calls))
	}
}

func TestClassifyTriggerResolvesLocalSkillPath(t *testing.T) {
	cwd := t.TempDir()
	writeSkillMD(t, localSkillsDir(cwd), "onboard", skillMD("Prepares a repo for agentic development.", false))
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "onboard", PrecededByUserTurn: true},
		UserTurn:   "set this repo up for Claude",
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Class != ClassCorrectlyTriggered {
		t.Fatalf("class = %v, want correctly-triggered via local resolution", got)
	}
}

func TestClassifyTriggerResolvesPluginCachePath(t *testing.T) {
	cwd := t.TempDir()  // no local skill here
	root := t.TempDir() // plugin cache root
	writeSkillMD(t, pluginSkillsDir(root), "gate", skillMD("Installs deterministic quality gates.", false))
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "gate", PrecededByUserTurn: true},
		UserTurn:   "add quality gates",
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: cwd, PluginCacheRoot: root}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Class != ClassCorrectlyTriggered {
		t.Fatalf("class = %v, want correctly-triggered via plugin-cache resolution", got)
	}
}

func TestClassifyTriggerUnresolvableWhenNeitherPathExists(t *testing.T) {
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "ghost", PrecededByUserTurn: true},
		UserTurn:   "do the ghost thing",
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: t.TempDir(), PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Class != ClassUnresolvable {
		t.Fatalf("class = %v, want unresolvable", got)
	}
	if len(fake.Calls) != 0 {
		t.Errorf("judge called %d times for an unresolvable skill, want 0", len(fake.Calls))
	}
}

func TestClassifyTriggerCorrectlyTriggeredFromJudge(t *testing.T) {
	cwd := t.TempDir()
	writeSkillMD(t, localSkillsDir(cwd), "critique", skillMD("Runs an adversarial review of a spec.", false))
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "critique", PrecededByUserTurn: true},
		UserTurn:   "poke holes in this spec",
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if got[0].Class != ClassCorrectlyTriggered {
		t.Fatalf("class = %v, want correctly-triggered", got[0].Class)
	}
}

func TestClassifyTriggerMisfiredFromJudge(t *testing.T) {
	cwd := t.TempDir()
	writeSkillMD(t, localSkillsDir(cwd), "critique", skillMD("Runs an adversarial review of a spec.", false))
	fake := &judge.Fake{Reply: "misfired"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "critique", PrecededByUserTurn: true},
		UserTurn:   "what's the weather today",
	}}
	got, err := ClassifyTriggers(inputs, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}, fake)
	if err != nil {
		t.Fatal(err)
	}
	if got[0].Class != ClassMisfired {
		t.Fatalf("class = %v, want misfired", got[0].Class)
	}
}

func TestClassifyTriggerJudgePromptContainsSkillDescription(t *testing.T) {
	cwd := t.TempDir()
	desc := "Decomposes a SPEC.md into independent task files sized for one clean session."
	writeSkillMD(t, localSkillsDir(cwd), "breakdown", skillMD(desc, false))
	fake := &judge.Fake{Reply: "correctly-triggered"}
	inputs := []TriggerInput{{
		Invocation: claude.SkillInvocation{Name: "breakdown", PrecededByUserTurn: true},
		UserTurn:   "split this spec into tasks",
	}}
	if _, err := ClassifyTriggers(inputs, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}, fake); err != nil {
		t.Fatal(err)
	}
	if len(fake.Calls) != 1 {
		t.Fatalf("judge calls = %d, want 1", len(fake.Calls))
	}
	if !strings.Contains(fake.Calls[0].Prompt, desc) {
		t.Errorf("judge prompt did not contain the skill's description; prompt = %q", fake.Calls[0].Prompt)
	}
	if !strings.Contains(fake.Calls[0].Prompt, "split this spec into tasks") {
		t.Errorf("judge prompt did not contain the preceding user turn; prompt = %q", fake.Calls[0].Prompt)
	}
}

func TestClassifyTriggerPossibleMissMatchesPhrase(t *testing.T) {
	cwd := t.TempDir()
	writeSkillMD(t, localSkillsDir(cwd), "health-admin",
		skillMD(`Health portal assistant. Trigger phrases "refill my prescriptions", "check my prescriptions".`, false))
	turns := []string{"can you refill my prescriptions before friday"}
	got, err := DetectPossibleMisses(turns, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 {
		t.Fatalf("misses = %v, want exactly 1", got)
	}
	if got[0].Skill != "health-admin" {
		t.Errorf("miss skill = %q, want health-admin", got[0].Skill)
	}
	if !strings.Contains(strings.ToLower(got[0].UserTurn), "refill my prescriptions") {
		t.Errorf("miss did not carry the matching user turn; got %q", got[0].UserTurn)
	}
}

func TestClassifyTriggerPossibleMissCleanMiss(t *testing.T) {
	cwd := t.TempDir()
	writeSkillMD(t, localSkillsDir(cwd), "health-admin",
		skillMD(`Health portal assistant. Trigger phrases "refill my prescriptions".`, false))
	turns := []string{"what is the capital of France"}
	got, err := DetectPossibleMisses(turns, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 0 {
		t.Fatalf("misses = %v, want none for a non-matching turn", got)
	}
}
