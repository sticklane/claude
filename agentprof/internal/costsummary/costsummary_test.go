package costsummary

import (
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

// sample builds a schema.Sample with the given stack, session label, and values.
func sample(session string, stack []string, values map[string]int64) schema.Sample {
	return schema.Sample{
		Time:   time.Now(),
		Stack:  stack,
		Values: values,
		Labels: map[string]string{"source": "claude-code", "session": session},
	}
}

// groupingFixture is a set of samples with known project/skill/agent/model
// frames plus one (unlinked)-shaped sample carrying no skill frame.
func groupingFixture() []schema.Sample {
	return []schema.Sample{
		// proj / skill:build / agent:scout / claude-fable-5
		sample("s1",
			[]string{"proj", "t01 · start", "skill:build", "main", "agent:scout", "claude-fable-5"},
			map[string]int64{"input_tokens": 100, "cost_microusd": 50}),
		// proj / skill:build / (no agent) / claude-fable-5
		sample("s1",
			[]string{"proj", "t01 · start", "skill:build", "main", "claude-fable-5"},
			map[string]int64{"input_tokens": 200, "cost_microusd": 80}),
		// beta / (no skill) explicit / (no agent) / claude-sonnet-4-5
		sample("s2",
			[]string{"beta", "t01 · hello", "(no skill)", "main", "claude-sonnet-4-5"},
			map[string]int64{"input_tokens": 300, "cost_microusd": 120}),
		// proj / (unlinked): no skill frame at all / agent:(unknown) / claude-haiku-4-5
		sample("s3",
			[]string{"proj", "(unlinked)", "agent:(unknown)", "claude-haiku-4-5"},
			map[string]int64{"input_tokens": 400, "cost_microusd": 10}),
	}
}

func TestBuildGroupsSamplesByProject(t *testing.T) {
	s := Build(groupingFixture(), groupingFixture())
	if got := s.ByProject["proj"]["input_tokens"]; got != 700 {
		t.Errorf("by_project[proj][input_tokens] = %d, want 700 (samples 1+2+4)", got)
	}
	if got := s.ByProject["proj"]["cost_microusd"]; got != 140 {
		t.Errorf("by_project[proj][cost_microusd] = %d, want 140", got)
	}
	if got := s.ByProject["beta"]["input_tokens"]; got != 300 {
		t.Errorf("by_project[beta][input_tokens] = %d, want 300", got)
	}
}

func TestBuildGroupsSamplesBySkill(t *testing.T) {
	s := Build(groupingFixture(), groupingFixture())
	if got := s.BySkill["skill:build"]["input_tokens"]; got != 300 {
		t.Errorf("by_skill[skill:build][input_tokens] = %d, want 300", got)
	}
	// The explicit (no skill) sample (300) AND the (unlinked) sample with no
	// skill frame (400) both land in the (no skill) bucket — the unlinked one
	// must not vanish.
	if got := s.BySkill["(no skill)"]["input_tokens"]; got != 700 {
		t.Errorf("by_skill[(no skill)][input_tokens] = %d, want 700 (explicit no-skill + unlinked)", got)
	}
}

func TestBuildGroupsSamplesByAgentType(t *testing.T) {
	s := Build(groupingFixture(), groupingFixture())
	if got := s.ByAgentType["agent:scout"]["input_tokens"]; got != 100 {
		t.Errorf("by_agent_type[agent:scout][input_tokens] = %d, want 100", got)
	}
	if got := s.ByAgentType["agent:(unknown)"]["input_tokens"]; got != 400 {
		t.Errorf("by_agent_type[agent:(unknown)][input_tokens] = %d, want 400", got)
	}
	// Samples with no agent frame contribute to no by_agent_type bucket.
	if len(s.ByAgentType) != 2 {
		t.Errorf("by_agent_type has %d buckets, want 2 (agentless samples excluded)", len(s.ByAgentType))
	}
}

func TestBuildGroupsSamplesByModel(t *testing.T) {
	s := Build(groupingFixture(), groupingFixture())
	if got := s.ByModel["claude-fable-5"]["input_tokens"]; got != 300 {
		t.Errorf("by_model[claude-fable-5][input_tokens] = %d, want 300", got)
	}
	if got := s.ByModel["claude-haiku-4-5"]["cost_microusd"]; got != 10 {
		t.Errorf("by_model[claude-haiku-4-5][cost_microusd] = %d, want 10 (unlinked sample counts by model)", got)
	}
}

func TestBuildSumsTotalsAcrossAllSamples(t *testing.T) {
	s := Build(groupingFixture(), groupingFixture())
	if got := s.Totals["input_tokens"]; got != 1000 {
		t.Errorf("totals[input_tokens] = %d, want 1000", got)
	}
	if got := s.Totals["cost_microusd"]; got != 260 {
		t.Errorf("totals[cost_microusd] = %d, want 260", got)
	}
}

func TestBuildSessionsAddedCountsDistinctFreshSessions(t *testing.T) {
	s := Build(groupingFixture(), groupingFixture())
	if s.SessionsAdded != 3 {
		t.Errorf("sessions_added = %d, want 3 (distinct sessions s1,s2,s3)", s.SessionsAdded)
	}
}

func TestBuildSessionsAddedZeroForEmptyFresh(t *testing.T) {
	s := Build(groupingFixture(), nil)
	if s.SessionsAdded != 0 {
		t.Errorf("sessions_added = %d, want 0 for an empty fresh set", s.SessionsAdded)
	}
}

func TestBuildEmptyForEmptyGroupingSet(t *testing.T) {
	s := Build(nil, nil)
	if s.SessionsAdded != 0 {
		t.Errorf("sessions_added = %d, want 0", s.SessionsAdded)
	}
	if len(s.Totals) != 0 || len(s.ByProject) != 0 {
		t.Errorf("empty grouping set must yield empty totals/by_project, got totals=%v by_project=%v", s.Totals, s.ByProject)
	}
	// Empty maps (not nil) so the JSON shape is {} rather than null.
	if s.ByProject == nil || s.BySkill == nil || s.ByAgentType == nil || s.ByModel == nil || s.Totals == nil {
		t.Error("group maps must be non-nil (initialized) so JSON emits {} not null")
	}
}

func TestBuildGroupingFromMergedWhileSessionsAddedFromFreshOnly(t *testing.T) {
	// merged (post-eviction rolling window) has samples from sessions old1/old2;
	// fresh (this run's Collect) touched only new1.
	merged := []schema.Sample{
		sample("old1", []string{"proj", "t01 · x", "skill:build", "main", "claude-fable-5"},
			map[string]int64{"cost_microusd": 500}),
		sample("old2", []string{"proj", "t01 · y", "skill:build", "main", "claude-fable-5"},
			map[string]int64{"cost_microusd": 300}),
	}
	fresh := []schema.Sample{
		sample("new1", []string{"proj", "t01 · z", "skill:build", "main", "claude-fable-5"},
			map[string]int64{"cost_microusd": 999}),
	}
	s := Build(merged, fresh)
	// Totals come from the merged set, never fresh.
	if got := s.Totals["cost_microusd"]; got != 800 {
		t.Errorf("totals[cost_microusd] = %d, want 800 (merged 500+300, not fresh 999)", got)
	}
	// sessions_added counts fresh sessions only.
	if s.SessionsAdded != 1 {
		t.Errorf("sessions_added = %d, want 1 (fresh session new1 only)", s.SessionsAdded)
	}
}
