package claude_test

import (
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/schema"
)

// threeUnmatchedLine is one assistant message carrying three tool_use blocks
// (tu1/tu2/tu3) in a single turn, none of which gets a tool_result — the
// R3 consolidation case.
func threeUnmatchedLine() string {
	return `{"type":"assistant","timestamp":"2026-07-01T09:00:10.000Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"mtool3","model":"claude-fable-5","content":[{"type":"tool_use","id":"tu1","name":"Bash"},{"type":"tool_use","id":"tu2","name":"Read"},{"type":"tool_use","id":"tu3","name":"Grep"}],"usage":{"input_tokens":10,"output_tokens":1}}}`
}

func pendingSamples(samples []schema.Sample) []schema.Sample {
	return findByStack(samples, []string{"app", "t01 · go", "(no skill)", "main", "tool:(pending)"})
}

// TestUnmatchedToolCallsConsolidateIntoOnePendingSample covers R3: three
// unmatched tool_use blocks in one turn collapse into a single tool:(pending)
// sample carrying pending_calls=3 — not three empty-valued samples.
func TestUnmatchedToolCallsConsolidateIntoOnePendingSample(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		threeUnmatchedLine(),
	)

	samples, _, _, err := claude.CollectWithOptions(dir, anyCutoff, claude.Options{ReprimeThreshold: claude.DefaultReprimeThreshold})
	if err != nil {
		t.Fatalf("CollectWithOptions: %v", err)
	}
	got := pendingSamples(samples)
	if len(got) != 1 {
		t.Fatalf("got %d tool:(pending) samples, want 1; all: %v", len(got), stacks(samples))
	}
	if n := got[0].Values["pending_calls"]; n != 3 {
		t.Errorf("pending_calls = %d, want 3", n)
	}
	if _, ok := got[0].Values["duration_ms"]; ok {
		t.Errorf("consolidated pending sample has a duration_ms; want none")
	}
}

// TestConsolidatedPendingHasNoEmptyValuesSamples covers R3's acceptance edge:
// under the default no tool:(pending) sample carries an empty Values map.
func TestConsolidatedPendingHasNoEmptyValuesSamples(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		threeUnmatchedLine(),
	)
	samples, _, _, err := claude.CollectWithOptions(dir, anyCutoff, claude.Options{})
	if err != nil {
		t.Fatalf("CollectWithOptions: %v", err)
	}
	for _, s := range pendingSamples(samples) {
		if len(s.Values) == 0 {
			t.Errorf("found an empty-values tool:(pending) sample; want none under consolidation")
		}
	}
}

// TestKeepPendingPreservesPerCallEmptyValuedSamples covers the R3 debug escape
// hatch: with KeepPending, each unmatched call keeps today's own empty-valued
// tool:(pending) sample instead of consolidating.
func TestKeepPendingPreservesPerCallEmptyValuedSamples(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		threeUnmatchedLine(),
	)
	samples, _, _, err := claude.CollectWithOptions(dir, anyCutoff, claude.Options{KeepPending: true})
	if err != nil {
		t.Fatalf("CollectWithOptions: %v", err)
	}
	got := pendingSamples(samples)
	if len(got) != 3 {
		t.Fatalf("got %d tool:(pending) samples, want 3 (per-call under KeepPending); all: %v", len(got), stacks(samples))
	}
	for _, s := range got {
		if len(s.Values) != 0 {
			t.Errorf("KeepPending sample Values = %v, want empty map", s.Values)
		}
	}
}

// TestPendingParseStatCountsUnmatchedCalls covers R3's parse-stat: Stats.Pending
// equals the number of unmatched tool_use calls, independent of whether they are
// consolidated or kept per-call.
func TestPendingParseStatCountsUnmatchedCalls(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		threeUnmatchedLine(),
	)
	for _, keep := range []bool{false, true} {
		_, _, stats, err := claude.CollectWithOptions(dir, anyCutoff, claude.Options{KeepPending: keep})
		if err != nil {
			t.Fatalf("CollectWithOptions(keep=%v): %v", keep, err)
		}
		if stats.Pending != 3 {
			t.Errorf("keep=%v: Stats.Pending = %d, want 3", keep, stats.Pending)
		}
	}
}

// TestMatchedCallsAreNotCountedPending guards the parse-stat against
// false positives: a fully matched tool call contributes 0 to Stats.Pending
// and emits its tool:<name> sample, never a tool:(pending) one.
func TestMatchedCallsAreNotCountedPending(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		toolUseLine("2026-07-01T09:00:10.000Z"),
		toolResultLine("2026-07-01T09:00:10.250Z"),
	)
	samples, _, stats, err := claude.CollectWithOptions(dir, anyCutoff, claude.Options{})
	if err != nil {
		t.Fatalf("CollectWithOptions: %v", err)
	}
	if stats.Pending != 0 {
		t.Errorf("Stats.Pending = %d, want 0 for a matched call", stats.Pending)
	}
	if got := pendingSamples(samples); len(got) != 0 {
		t.Errorf("got %d tool:(pending) samples, want 0 for a matched call", len(got))
	}
}
