package main

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
)

// runClaudeSummary runs `claude --claude-dir testdata/claude-dir -o summary`
// and returns the parsed stdout rows. It fails the test on a nonzero exit or
// unparseable stdout.
func runClaudeSummary(t *testing.T) []map[string]any {
	t.Helper()
	var stdout, stderr bytes.Buffer
	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir", "-o", "summary"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	var rows []map[string]any
	if err := json.Unmarshal(stdout.Bytes(), &rows); err != nil {
		t.Fatalf("stdout is not a JSON array: %v\nstdout: %s", err, stdout.String())
	}
	return rows
}

func TestClaudeSummaryEmitsOneRowPerSessionModelWithR1Keys(t *testing.T) {
	rows := runClaudeSummary(t)
	if len(rows) == 0 {
		t.Fatal("want at least one summary row, got none")
	}
	required := []string{
		"session", "model", "input_tokens", "output_tokens",
		"cache_read_tokens", "cache_write_tokens", "cost_microusd", "priced",
	}
	seen := map[string]bool{}
	for _, r := range rows {
		for _, k := range required {
			if _, ok := r[k]; !ok {
				t.Errorf("row %v missing R1 key %q", r, k)
			}
		}
		key := r["session"].(string) + "|" + r["model"].(string)
		if seen[key] {
			t.Errorf("duplicate (session, model) row: %s — want one row per distinct pair", key)
		}
		seen[key] = true
	}
}

func TestClaudeSummaryAttributesSubagentSpendToParentSession(t *testing.T) {
	rows := runClaudeSummary(t)

	var haikuInput float64
	haikuFound := false
	for _, r := range rows {
		sess := r["session"].(string)
		if strings.HasPrefix(sess, "agent-") {
			t.Errorf("row session = %q: subagent spend must attribute to the spawning session, never an agent basename (R2)", sess)
		}
		if sess == "sess-0001" && r["model"].(string) == "claude-haiku-4-5" {
			haikuInput = r["input_tokens"].(float64)
			haikuFound = true
		}
	}
	if !haikuFound {
		t.Fatal("want a sess-0001 / claude-haiku-4-5 row")
	}
	// agent-B.jsonl (400 input tokens, claude-haiku-4-5) is a subagent of
	// sess-0001; its spend must fold into the parent session's row (R2).
	// Main-transcript haiku spend alone is 100, so a value >= 400 proves the
	// subagent tokens rolled in rather than landing under an agent id.
	if haikuInput < 400 {
		t.Errorf("sess-0001 claude-haiku-4-5 input_tokens = %v, want >= 400 (subagent agent-B spend folded into parent, R2)", haikuInput)
	}
}

func TestClaudeSummaryMarksUnpricedModelPricedFalseZeroCost(t *testing.T) {
	rows := runClaudeSummary(t)

	found := false
	for _, r := range rows {
		if r["model"].(string) != "mystery-model-9" {
			continue
		}
		found = true
		if r["priced"].(bool) {
			t.Errorf("mystery-model-9 row priced = true, want false (R3)")
		}
		if got := r["cost_microusd"].(float64); got != 0 {
			t.Errorf("mystery-model-9 cost_microusd = %v, want 0 (R3)", got)
		}
		if got := r["input_tokens"].(float64); got <= 0 {
			t.Errorf("mystery-model-9 input_tokens = %v, want > 0 (unpriced but tokens counted, R3)", got)
		}
	}
	if !found {
		t.Fatal("want a mystery-model-9 row in the fixture output")
	}
}

func TestClaudeSummaryNonexistentDirExitsNonzeroWithMessage(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"claude", "--claude-dir", "/nonexistent", "-o", "summary"}, &stdout, &stderr)
	if code == 0 {
		t.Errorf("exit code = 0, want nonzero for a missing --claude-dir (R4)")
	}
	if stderr.Len() == 0 {
		t.Error("want an error message on stderr for a missing --claude-dir (R4)")
	}
}
