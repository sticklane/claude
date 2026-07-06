package claude_test

import (
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/schema"
)

// toolUseLine is an assistant line carrying a single tool_use block (id "tu1",
// name "Bash") at the given timestamp.
func toolUseLine(ts string) string {
	return `{"type":"assistant","timestamp":"` + ts + `","cwd":"/z/app","sessionId":"sess-z","message":{"id":"mtool","model":"claude-fable-5","content":[{"type":"text","text":"running a command"},{"type":"tool_use","id":"tu1","name":"Bash"}],"usage":{"input_tokens":10,"output_tokens":1}}}`
}

// toolResultLine is a user line carrying the tool_result for tu1 at the given
// timestamp.
func toolResultLine(ts string) string {
	return `{"type":"user","timestamp":"` + ts + `","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"tu1","content":"done"}]}}`
}

// TestToolCallSampleReportsExactDuration covers R1: a tool_use/tool_result pair
// yields one sample with a tool:<name> leaf at the model-name position and
// duration_ms equal to the exact result-minus-use delta in milliseconds.
func TestToolCallSampleReportsExactDuration(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		toolUseLine("2026-07-01T09:00:10.000Z"),
		toolResultLine("2026-07-01T09:00:10.250Z"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · go", "(no skill)", "main", "tool:Bash"})
	if len(got) != 1 {
		t.Fatalf("got %d tool:Bash samples, want 1; all: %v", len(got), stacks(samples))
	}
	if d := got[0].Values["duration_ms"]; d != 250 {
		t.Errorf("duration_ms = %d, want 250", d)
	}
}

// TestToolCallDurationClampsNegativeDeltaToZero covers R1's clamp rule: an
// out-of-order (clock-skew) tool_result timestamp before the tool_use yields
// exactly 0, never a negative value.
func TestToolCallDurationClampsNegativeDeltaToZero(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		toolUseLine("2026-07-01T09:00:10.000Z"),
		toolResultLine("2026-07-01T09:00:09.000Z"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · go", "(no skill)", "main", "tool:Bash"})
	if len(got) != 1 {
		t.Fatalf("got %d tool:Bash samples, want 1; all: %v", len(got), stacks(samples))
	}
	if d, ok := got[0].Values["duration_ms"]; !ok || d != 0 {
		t.Errorf("duration_ms = %d (present=%v), want exactly 0", d, ok)
	}
}

// TestPendingToolUseHasEmptyValues covers R2: a tool_use with no matching
// tool_result produces a tool:(pending) leaf and an EMPTY Values map (no
// duration_ms key), asserted directly on the parsed sample slice.
func TestPendingToolUseHasEmptyValues(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		toolUseLine("2026-07-01T09:00:10.000Z"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · go", "(no skill)", "main", "tool:(pending)"})
	if len(got) != 1 {
		t.Fatalf("got %d tool:(pending) samples, want 1; all: %v", len(got), stacks(samples))
	}
	if len(got[0].Values) != 0 {
		t.Errorf("pending sample Values = %v, want empty map (no fabricated duration)", got[0].Values)
	}
}

// TestModelCallDurationOmitsFirstAndMeasuresRest covers R3: each model-call
// sample after the first in a transcript gains duration_ms = this_ts - prev_ts;
// the first sample omits it entirely.
func TestModelCallDurationOmitsFirstAndMeasuresRest(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		modelLine("m1", "2026-07-01T09:00:10.000Z"),
		modelLine("m2", "2026-07-01T09:00:12.500Z"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	first := modelSample(t, samples, "m1")
	if _, ok := first.Values["duration_ms"]; ok {
		t.Errorf("first sample has duration_ms = %d, want it omitted", first.Values["duration_ms"])
	}
	second := modelSample(t, samples, "m2")
	if d, ok := second.Values["duration_ms"]; !ok || d != 2500 {
		t.Errorf("second sample duration_ms = %d (present=%v), want 2500", d, ok)
	}
}

// TestModelCallDurationSpansInterveningToolResult covers R3's previous_ts
// definition: a tool_result user line between two model calls is the "previous"
// captured line for the second call's duration.
func TestModelCallDurationSpansInterveningToolResult(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"go"}}`,
		toolUseLine("2026-07-01T09:00:10.000Z"),
		toolResultLine("2026-07-01T09:00:11.000Z"),
		modelLine("m2", "2026-07-01T09:00:11.750Z"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	second := modelSample(t, samples, "m2")
	if d, ok := second.Values["duration_ms"]; !ok || d != 750 {
		t.Errorf("duration_ms = %d (present=%v), want 750 (measured from the tool_result line)", d, ok)
	}
}

// modelLine is an assistant line with message id and timestamp and no tool_use.
func modelLine(msgID, ts string) string {
	return `{"type":"assistant","timestamp":"` + ts + `","cwd":"/z/app","sessionId":"sess-z","message":{"id":"` + msgID + `","model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1}}}`
}

// modelSample returns a model-call sample (leaf frame "claude-fable-5") by
// position: msgID "m1" is the first such sample in transcript order, "m2" the
// last. Tool-call samples carry a tool: leaf and are skipped.
func modelSample(t *testing.T, samples []schema.Sample, msgID string) schema.Sample {
	t.Helper()
	var out []schema.Sample
	for _, s := range samples {
		if s.Stack[len(s.Stack)-1] == "claude-fable-5" {
			out = append(out, s)
		}
	}
	if len(out) == 0 {
		t.Fatalf("no model sample found; all: %v", stacks(samples))
	}
	if msgID == "m1" {
		return out[0]
	}
	if len(out) < 2 {
		t.Fatalf("want >=2 model samples, got %d; all: %v", len(out), stacks(samples))
	}
	return out[len(out)-1]
}
