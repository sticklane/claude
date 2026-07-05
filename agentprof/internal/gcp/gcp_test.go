package gcp

import (
	"os"
	"strings"
	"testing"
	"time"
)

// validNested is a valid bq-shaped nested row; tests derive variants by
// string-replacing individual fields.
const validNested = `{"project":{"id":"proj-a"},"service":{"description":"Vertex AI"},"sku":{"description":"Vertex AI Online Prediction"},"usage_start_time":"2026-06-01 00:00:00","cost":"1.5","currency":"USD"}`

func parseOne(t *testing.T, row string) (stack []string, values map[string]int64, labels map[string]string, tm time.Time) {
	t.Helper()
	samples, skipped, err := Parse(strings.NewReader(row), nil)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	s := samples[0]
	return s.Stack, s.Values, s.Labels, s.Time
}

func TestParseAcceptsJSONArrayFile(t *testing.T) {
	in := `[` + validNested + `,` + validNested + `]`
	samples, skipped, err := Parse(strings.NewReader(in), nil)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 0 {
		t.Errorf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 2 {
		t.Errorf("len(samples) = %d, want 2", len(samples))
	}
}

func TestParseAcceptsJSONL(t *testing.T) {
	in := validNested + "\n" + validNested + "\n"
	samples, skipped, err := Parse(strings.NewReader(in), nil)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 0 {
		t.Errorf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 2 {
		t.Errorf("len(samples) = %d, want 2", len(samples))
	}
}

func TestParseBuildsStackValuesLabelsFromNestedRow(t *testing.T) {
	stack, values, labels, _ := parseOne(t, validNested)
	wantStack := []string{"proj-a", "Vertex AI", "Vertex AI Online Prediction"}
	if len(stack) != 3 || stack[0] != wantStack[0] || stack[1] != wantStack[1] || stack[2] != wantStack[2] {
		t.Errorf("stack = %v, want %v", stack, wantStack)
	}
	if values["cost_microusd"] != 1500000 {
		t.Errorf("cost_microusd = %d, want 1500000", values["cost_microusd"])
	}
	if values["calls"] != 1 {
		t.Errorf("calls = %d, want 1", values["calls"])
	}
	if labels["source"] != "gcp" {
		t.Errorf("labels[source] = %q, want %q", labels["source"], "gcp")
	}
	if labels["currency"] != "USD" {
		t.Errorf("labels[currency] = %q, want %q", labels["currency"], "USD")
	}
}

func TestParseAcceptsAliasedFlatKeys(t *testing.T) {
	row := `{"project_id":"proj-b","service_description":"Cloud Run","sku_description":"CPU Allocation Time","usage_start_time":"2026-06-01 00:00:00","cost":"0.5","currency":"EUR"}`
	stack, values, labels, _ := parseOne(t, row)
	wantStack := []string{"proj-b", "Cloud Run", "CPU Allocation Time"}
	if len(stack) != 3 || stack[0] != wantStack[0] || stack[1] != wantStack[1] || stack[2] != wantStack[2] {
		t.Errorf("stack = %v, want %v", stack, wantStack)
	}
	if values["cost_microusd"] != 500000 {
		t.Errorf("cost_microusd = %d, want 500000", values["cost_microusd"])
	}
	if labels["currency"] != "EUR" {
		t.Errorf("labels[currency] = %q, want %q", labels["currency"], "EUR")
	}
}

func TestParseAcceptsCostAsJSONStringOrNumber(t *testing.T) {
	asNumber := strings.Replace(validNested, `"cost":"1.5"`, `"cost":1.5`, 1)
	for name, row := range map[string]string{"string": validNested, "number": asNumber} {
		t.Run(name, func(t *testing.T) {
			_, values, _, _ := parseOne(t, row)
			if values["cost_microusd"] != 1500000 {
				t.Errorf("cost_microusd = %d, want 1500000", values["cost_microusd"])
			}
		})
	}
}

func TestParseTimeSpaceSeparated(t *testing.T) {
	cases := map[string]struct {
		in   string
		want time.Time
	}{
		"plain":               {"2026-06-01 09:30:00", time.Date(2026, 6, 1, 9, 30, 0, 0, time.UTC)},
		"fractional":          {"2026-06-01 09:30:00.123456", time.Date(2026, 6, 1, 9, 30, 0, 123456000, time.UTC)},
		"utc_suffix":          {"2026-06-01 09:30:00 UTC", time.Date(2026, 6, 1, 9, 30, 0, 0, time.UTC)},
		"fractional_plus_utc": {"2026-06-01 09:30:00.123456 UTC", time.Date(2026, 6, 1, 9, 30, 0, 123456000, time.UTC)},
	}
	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			row := strings.Replace(validNested, "2026-06-01 00:00:00", tc.in, 1)
			_, _, _, tm := parseOne(t, row)
			if !tm.Equal(tc.want) {
				t.Errorf("time = %v, want %v", tm, tc.want)
			}
		})
	}
}

func TestParseTimeRFC3339(t *testing.T) {
	row := strings.Replace(validNested, "2026-06-01 00:00:00", "2026-06-01T09:30:00Z", 1)
	_, _, _, tm := parseOne(t, row)
	want := time.Date(2026, 6, 1, 9, 30, 0, 0, time.UTC)
	if !tm.Equal(want) {
		t.Errorf("time = %v, want %v", tm, want)
	}
	if tm.Location() != time.UTC {
		t.Errorf("location = %v, want UTC", tm.Location())
	}
}

func TestParseTimeEpochSecondsString(t *testing.T) {
	// 1.7489952e+09 == 1748995200 == 2025-06-04T00:00:00Z
	want := time.Date(2025, 6, 4, 0, 0, 0, 0, time.UTC)
	for name, in := range map[string]string{
		"plain":      "1748995200",
		"scientific": "1.7489952e+09",
	} {
		t.Run(name, func(t *testing.T) {
			row := strings.Replace(validNested, `"2026-06-01 00:00:00"`, `"`+in+`"`, 1)
			_, _, _, tm := parseOne(t, row)
			if !tm.Equal(want) {
				t.Errorf("time = %v, want %v", tm, want)
			}
		})
	}
}

func TestParseSkipsRowsWithMissingRequiredFields(t *testing.T) {
	cases := map[string]string{
		"missing_project_id": strings.Replace(validNested, `{"id":"proj-a"}`, `{}`, 1),
		"empty_project_id":   strings.Replace(validNested, `"id":"proj-a"`, `"id":""`, 1),
		"missing_service":    strings.Replace(validNested, `"service":{"description":"Vertex AI"},`, ``, 1),
		"missing_sku":        strings.Replace(validNested, `"sku":{"description":"Vertex AI Online Prediction"},`, ``, 1),
		"missing_time":       strings.Replace(validNested, `"usage_start_time":"2026-06-01 00:00:00",`, ``, 1),
		"unparseable_time":   strings.Replace(validNested, "2026-06-01 00:00:00", "not-a-time", 1),
		"missing_cost":       strings.Replace(validNested, `"cost":"1.5",`, ``, 1),
		"unparseable_cost":   strings.Replace(validNested, `"cost":"1.5"`, `"cost":"abc"`, 1),
		"missing_currency":   strings.Replace(validNested, `,"currency":"USD"`, ``, 1),
	}
	for name, row := range cases {
		t.Run(name, func(t *testing.T) {
			samples, skipped, err := Parse(strings.NewReader(row), nil)
			if err != nil {
				t.Fatalf("Parse() error = %v", err)
			}
			if skipped != 1 {
				t.Errorf("skipped = %d, want 1", skipped)
			}
			if len(samples) != 0 {
				t.Errorf("len(samples) = %d, want 0", len(samples))
			}
		})
	}
}

func TestParseSkipsNegativeCostCreditRows(t *testing.T) {
	row := strings.Replace(validNested, `"cost":"1.5"`, `"cost":"-0.3"`, 1)
	samples, skipped, err := Parse(strings.NewReader(row), nil)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
	if len(samples) != 0 {
		t.Errorf("len(samples) = %d, want 0", len(samples))
	}
}

func TestParseFixtureFileYieldsSixSamplesAndTwoSkips(t *testing.T) {
	f, err := os.Open("../../testdata/gcp-billing.json")
	if err != nil {
		t.Fatalf("open fixture: %v", err)
	}
	defer f.Close()
	samples, skipped, err := Parse(f, nil)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 2 {
		t.Errorf("skipped = %d, want 2", skipped)
	}
	if len(samples) != 6 {
		t.Fatalf("len(samples) = %d, want 6", len(samples))
	}
	foundVertex := false
	for _, s := range samples {
		if len(s.Stack) == 3 && s.Stack[2] == "Vertex AI Online Prediction" {
			foundVertex = true
		}
	}
	if !foundVertex {
		t.Errorf("no sample with Vertex AI SKU leaf frame in %v", samples)
	}
}
