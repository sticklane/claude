package census

import "testing"

func skillUse(harness, session, name, invocation string) Activation {
	return Activation{Harness: harness, Session: session, Kind: KindSkill, Name: name, Invocation: invocation}
}

func TestAggregateSumsOneNamePerHarness(t *testing.T) {
	stats := Aggregate([]Activation{
		skillUse("claude", "s1", "critique", InvocationAuto),
		skillUse("codex", "s2", "critique", InvocationUnknown),
		skillUse("codex", "s3", "critique", InvocationUnknown),
	})
	if len(stats) != 1 {
		t.Fatalf("want 1 stat, got %d", len(stats))
	}
	got := stats[0]
	if got.Total != 3 {
		t.Errorf("Total = %d, want 3", got.Total)
	}
	if got.ByHarness["claude"] != 1 || got.ByHarness["codex"] != 2 {
		t.Errorf("ByHarness = %v, want claude:1 codex:2", got.ByHarness)
	}
}

func TestAggregateSplitsAutoFromExplicit(t *testing.T) {
	stats := Aggregate([]Activation{
		skillUse("claude", "s1", "drain", InvocationExplicit),
		skillUse("claude", "s2", "drain", InvocationAuto),
		skillUse("claude", "s3", "drain", InvocationAuto),
	})
	if stats[0].Auto != 2 {
		t.Errorf("Auto = %d, want 2", stats[0].Auto)
	}
	if stats[0].Explicit != 1 {
		t.Errorf("Explicit = %d, want 1", stats[0].Explicit)
	}
}

func TestAggregateCountsDistinctSessionsNotActivations(t *testing.T) {
	stats := Aggregate([]Activation{
		skillUse("claude", "s1", "build", InvocationAuto),
		skillUse("claude", "s1", "build", InvocationAuto),
		skillUse("claude", "s2", "build", InvocationAuto),
	})
	if stats[0].Sessions != 2 {
		t.Errorf("Sessions = %d, want 2", stats[0].Sessions)
	}
}

func TestAggregateKeepsAuthoringOutOfUseTotals(t *testing.T) {
	edit := skillUse("codex", "s1", "gate", InvocationUnknown)
	edit.Authoring = true
	stats := Aggregate([]Activation{
		skillUse("codex", "s2", "gate", InvocationUnknown),
		edit,
	})
	if stats[0].Total != 1 {
		t.Errorf("Total = %d, want 1 (authoring excluded)", stats[0].Total)
	}
	if stats[0].Authoring != 1 {
		t.Errorf("Authoring = %d, want 1", stats[0].Authoring)
	}
}

func TestAggregateSeparatesSkillsFromToolsOfTheSameName(t *testing.T) {
	stats := Aggregate([]Activation{
		{Harness: "claude", Session: "s1", Kind: KindSkill, Name: "ctx", Invocation: InvocationAuto},
		{Harness: "claude", Session: "s1", Kind: KindTool, Name: "ctx", Invocation: InvocationUnknown},
	})
	if len(stats) != 2 {
		t.Fatalf("want 2 stats (skill and tool kept apart), got %d", len(stats))
	}
}

func TestAggregateOrdersByTotalDescending(t *testing.T) {
	stats := Aggregate([]Activation{
		skillUse("claude", "s1", "rare", InvocationAuto),
		skillUse("claude", "s1", "common", InvocationAuto),
		skillUse("claude", "s2", "common", InvocationAuto),
	})
	if stats[0].Name != "common" {
		t.Errorf("first stat = %q, want %q", stats[0].Name, "common")
	}
}

func TestUnusedReportsInstalledSkillsWithNoUse(t *testing.T) {
	stats := Aggregate([]Activation{skillUse("claude", "s1", "critique", InvocationAuto)})
	got := Unused([]string{"critique", "humanizer", "taste"}, stats)
	if len(got) != 2 || got[0] != "humanizer" || got[1] != "taste" {
		t.Errorf("Unused = %v, want [humanizer taste]", got)
	}
}

func TestUnusedTreatsAuthoringOnlySkillAsUnused(t *testing.T) {
	edit := skillUse("codex", "s1", "gate", InvocationUnknown)
	edit.Authoring = true
	stats := Aggregate([]Activation{edit})
	got := Unused([]string{"gate"}, stats)
	if len(got) != 1 {
		t.Errorf("Unused = %v, want [gate] — editing a skill is not using it", got)
	}
}

func TestNormalizeNameDropsPluginNamespace(t *testing.T) {
	stats := Aggregate([]Activation{
		skillUse("claude", "s1", "agentic:critique", InvocationAuto),
		skillUse("claude", "s2", "critique", InvocationAuto),
	})
	if len(stats) != 1 {
		t.Fatalf("want plugin-namespaced and bare names merged, got %d stats", len(stats))
	}
	if stats[0].Name != "critique" {
		t.Errorf("Name = %q, want %q", stats[0].Name, "critique")
	}
}
