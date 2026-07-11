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

// reprimeSample builds a main-loop model-call sample carrying reprime=true.
func reprimeSample(session, project string, cacheWrite, cost int64) schema.Sample {
	return schema.Sample{
		Time:   time.Now(),
		Stack:  []string{project, "t01 · x", "skill:build", "main", "claude-fable-5"},
		Values: map[string]int64{"cache_write_tokens": cacheWrite, "cost_microusd": cost, "calls": 1},
		Labels: map[string]string{"source": "claude-code", "session": session, "reprime": "true"},
	}
}

// mainCall builds a main-loop model-call sample with a context (input +
// cache_read) and cost.
func mainCall(session, project string, input, cacheRead, cost int64) schema.Sample {
	return schema.Sample{
		Time:  time.Now(),
		Stack: []string{project, "t01 · x", "skill:build", "main", "claude-fable-5"},
		Values: map[string]int64{
			"input_tokens": input, "cache_read_tokens": cacheRead,
			"cost_microusd": cost, "calls": 1,
		},
		Labels: map[string]string{"source": "claude-code", "session": session},
	}
}

// agentCall builds a subagent model-call sample (carries an agent: frame) with
// the given session label — it must NOT contribute to per-session ctx stats.
func agentCall(session, project string, input, cost int64) schema.Sample {
	return schema.Sample{
		Time:   time.Now(),
		Stack:  []string{project, "t01 · x", "skill:build", "main", "agent:scout", "claude-haiku-4-5"},
		Values: map[string]int64{"input_tokens": input, "cost_microusd": cost, "calls": 1},
		Labels: map[string]string{"source": "claude-code", "session": session},
	}
}

func TestBuildReprimeSectionCountsTokensCostAndByProject(t *testing.T) {
	samples := []schema.Sample{
		reprimeSample("s1", "proj", 70000, 100),
		reprimeSample("s2", "beta", 80000, 200),
		// A high-cache-write main-loop call that is NOT labeled reprime must be excluded.
		mainCall("s3", "proj", 0, 90000, 999),
	}
	s := Build(samples, nil)
	if s.Reprime.Count != 2 {
		t.Errorf("reprime.count = %d, want 2", s.Reprime.Count)
	}
	if s.Reprime.CacheWriteTokens != 150000 {
		t.Errorf("reprime.cache_write_tokens = %d, want 150000", s.Reprime.CacheWriteTokens)
	}
	if s.Reprime.CostMicrousd != 300 {
		t.Errorf("reprime.cost_microusd = %d, want 300", s.Reprime.CostMicrousd)
	}
	if got := s.Reprime.ByProject["proj"]["cache_write_tokens"]; got != 70000 {
		t.Errorf("reprime.by_project[proj][cache_write_tokens] = %d, want 70000", got)
	}
	if got := s.Reprime.ByProject["proj"]["count"]; got != 1 {
		t.Errorf("reprime.by_project[proj][count] = %d, want 1", got)
	}
	if got := s.Reprime.ByProject["beta"]["cost_microusd"]; got != 200 {
		t.Errorf("reprime.by_project[beta][cost_microusd] = %d, want 200", got)
	}
}

func TestBuildReprimeSectionEmptyWhenNoReprimeSamples(t *testing.T) {
	s := Build(groupingFixture(), nil)
	if s.Reprime.Count != 0 {
		t.Errorf("reprime.count = %d, want 0 when no samples are labeled reprime", s.Reprime.Count)
	}
	if s.Reprime.ByProject == nil {
		t.Error("reprime.by_project must be non-nil (initialized) so JSON emits {} not null")
	}
}

func TestBuildSessionsSectionContextPercentilesMainLoopOnly(t *testing.T) {
	samples := []schema.Sample{
		mainCall("long", "proj", 100, 0, 10),   // ctx 100
		mainCall("long", "proj", 100, 200, 20), // ctx 300
		mainCall("long", "proj", 0, 500, 30),   // ctx 500
		// Same session label, but a subagent call — a huge ctx that must be
		// excluded from the percentiles and from calls/cost.
		agentCall("long", "proj", 9999, 999),
		mainCall("short", "beta", 50, 0, 5), // ctx 50
	}
	s := Build(samples, nil)
	long, ok := s.Sessions["long"]
	if !ok {
		t.Fatal("sessions missing key 'long'")
	}
	if long.Project != "proj" {
		t.Errorf("sessions[long].project = %q, want proj", long.Project)
	}
	if long.Calls != 3 {
		t.Errorf("sessions[long].calls = %d, want 3 (main-loop calls only, agent excluded)", long.Calls)
	}
	if long.CostMicrousd != 60 {
		t.Errorf("sessions[long].cost_microusd = %d, want 60 (10+20+30, agent 999 excluded)", long.CostMicrousd)
	}
	// nearest-rank over sorted [100,300,500]: p50 -> index2 -> 300, p90 -> 500.
	if long.P50Ctx != 300 {
		t.Errorf("sessions[long].p50_ctx = %d, want 300", long.P50Ctx)
	}
	if long.P90Ctx != 500 {
		t.Errorf("sessions[long].p90_ctx = %d, want 500 (agent ctx 9999 excluded)", long.P90Ctx)
	}
	short, ok := s.Sessions["short"]
	if !ok {
		t.Fatal("sessions missing key 'short'")
	}
	if short.P50Ctx != 50 || short.P90Ctx != 50 {
		t.Errorf("sessions[short] p50/p90 = %d/%d, want 50/50", short.P50Ctx, short.P90Ctx)
	}
}

func TestBuildSessionsSectionNonNilWhenEmpty(t *testing.T) {
	s := Build(nil, nil)
	if s.Sessions == nil {
		t.Error("sessions must be non-nil (initialized) so JSON emits {} not null")
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
