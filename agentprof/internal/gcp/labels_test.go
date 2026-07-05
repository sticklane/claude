package gcp

import (
	"os"
	"reflect"
	"strings"
	"testing"
)

const labelRowBase = `"service":{"description":"Vertex AI"},"sku":{"description":"Online Prediction"},"usage_start_time":"2026-06-01 00:00:00","cost":"1.5","currency":"USD"`

func parseOneLabeled(t *testing.T, row string, frameLabels []string) []string {
	t.Helper()
	samples, skipped, err := Parse(strings.NewReader(row), frameLabels)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 0 || len(samples) != 1 {
		t.Fatalf("got %d samples / %d skipped, want 1 / 0", len(samples), skipped)
	}
	return samples[0].Stack
}

func TestParseFrameLabelsInsertLabelFramesAfterProjectInFlagOrder(t *testing.T) {
	row := `{"project":{"id":"proj-a"},"labels":[{"key":"team","value":"vision"},{"key":"env","value":"prod"}],` + labelRowBase + `}`
	got := parseOneLabeled(t, row, []string{"env", "team"})
	want := []string{"proj-a", "env:prod", "team:vision", "Vertex AI", "Online Prediction"}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("stack = %v, want %v", got, want)
	}
}

func TestParseFrameLabelsMissingKeyGetsNone(t *testing.T) {
	row := `{"project":{"id":"proj-a"},"labels":[{"key":"env","value":"prod"}],` + labelRowBase + `}`
	got := parseOneLabeled(t, row, []string{"team"})
	want := []string{"proj-a", "team:(none)", "Vertex AI", "Online Prediction"}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("stack = %v, want %v", got, want)
	}
}

func TestParseFrameLabelsAbsentOrMalformedLabelsFieldKeepsRow(t *testing.T) {
	cases := []struct{ name, labels string }{
		{"absent", ""},
		{"string not array", `"labels":"oops",`},
		{"array of strings", `"labels":["team"],`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			row := `{"project":{"id":"proj-a"},` + tc.labels + labelRowBase + `}`
			got := parseOneLabeled(t, row, []string{"team"})
			want := []string{"proj-a", "team:(none)", "Vertex AI", "Online Prediction"}
			if !reflect.DeepEqual(got, want) {
				t.Errorf("stack = %v, want %v (row must not be skipped)", got, want)
			}
		})
	}
}

func TestParseFrameLabelsDuplicateKeyFirstOccurrenceWins(t *testing.T) {
	row := `{"project":{"id":"proj-a"},"labels":[{"key":"team","value":"vision"},{"key":"team","value":"audio"}],` + labelRowBase + `}`
	got := parseOneLabeled(t, row, []string{"team"})
	if got[1] != "team:vision" {
		t.Errorf("stack = %v, want first occurrence team:vision", got)
	}
}

func TestParseFixtureWithTeamFrameLabels(t *testing.T) {
	f, err := os.Open("../../testdata/gcp-billing.json")
	if err != nil {
		t.Fatalf("open fixture: %v", err)
	}
	defer f.Close()
	samples, _, err := Parse(f, []string{"team"})
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	vision, none := 0, 0
	for _, s := range samples {
		switch s.Stack[1] {
		case "team:vision":
			vision++
		case "team:(none)":
			none++
		default:
			t.Errorf("sample lacks a team label frame: %v", s.Stack)
		}
	}
	if vision < 1 {
		t.Errorf("team:vision samples = %d, want >= 1", vision)
	}
	if none < 2 {
		t.Errorf("team:(none) samples = %d, want >= 2 (malformed-labels row must survive)", none)
	}
}

func TestParseWithoutFrameLabelsLeavesStacksUnchanged(t *testing.T) {
	row := `{"project":{"id":"proj-a"},"labels":[{"key":"team","value":"vision"}],` + labelRowBase + `}`
	got := parseOneLabeled(t, row, nil)
	want := []string{"proj-a", "Vertex AI", "Online Prediction"}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("stack = %v, want %v", got, want)
	}
}
