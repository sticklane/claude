package vertex

import (
	"os"
	"slices"
	"strings"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

// validGemini is a valid unary Gemini row with an inline-object full_response;
// tests derive variants by string-replacing individual fields.
const validGemini = `{"endpoint":"projects/proj-vertex/locations/us-central1/publishers/google/models/gemini-2.0-flash","logging_time":"2026-07-01 12:00:00","api_method":"google.cloud.aiplatform.v1.PredictionService.GenerateContent","model":"publishers/google/models/gemini-2.0-flash","full_response":{"modelVersion":"gemini-2.0-flash","usageMetadata":{"promptTokenCount":1000,"candidatesTokenCount":100,"thoughtsTokenCount":50,"cachedContentTokenCount":200}}}`

// validClaude is a valid Claude-on-Vertex row whose full_response is a
// JSON-encoded string (the `bq query --format=json` encoding of JSON columns)
// and whose endpoint carries a project number.
const validClaude = `{"endpoint":"projects/123456789/locations/us-east5/publishers/anthropic/models/claude-sonnet-4@20250514","logging_time":"2026-07-01 13:00:00","api_method":"rawPredict","model":"publishers/anthropic/models/claude-sonnet-4@20250514","full_response":"{\"model\":\"claude-sonnet-4-20250514\",\"usage\":{\"input_tokens\":500,\"output_tokens\":60,\"cache_read_input_tokens\":30,\"cache_creation_input_tokens\":40}}"}`

func parseOne(t *testing.T, row string) schema.Sample {
	t.Helper()
	samples, skipped, err := Parse(strings.NewReader(row))
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 0 {
		t.Fatalf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	return samples[0]
}

func parseSkipsOne(t *testing.T, row string) {
	t.Helper()
	samples, skipped, err := Parse(strings.NewReader(row))
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

func assertStack(t *testing.T, got, want []string) {
	t.Helper()
	if !slices.Equal(got, want) {
		t.Fatalf("stack = %v, want %v", got, want)
	}
}

func TestParseAcceptsJSONArray(t *testing.T) {
	in := `[` + validGemini + `,` + validClaude + `]`
	samples, skipped, err := Parse(strings.NewReader(in))
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
	in := validGemini + "\n" + validClaude + "\n"
	samples, skipped, err := Parse(strings.NewReader(in))
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

func TestParseGeminiRowStackMetricsAndLabels(t *testing.T) {
	s := parseOne(t, validGemini)
	assertStack(t, s.Stack, []string{"proj-vertex", "us-central1", "gemini-2.0-flash", "GenerateContent"})
	want := map[string]int64{"input_tokens": 1000, "output_tokens": 150, "cache_read_tokens": 200, "calls": 1}
	for name, v := range want {
		if s.Values[name] != v {
			t.Errorf("values[%s] = %d, want %d", name, s.Values[name], v)
		}
	}
	if _, ok := s.Values["cost_microusd"]; ok {
		t.Errorf("gemini sample has cost_microusd = %d, want no cost metric", s.Values["cost_microusd"])
	}
	if s.Labels["source"] != "vertex" {
		t.Errorf("labels[source] = %q, want vertex", s.Labels["source"])
	}
	if s.Labels["priced"] != "false" {
		t.Errorf("labels[priced] = %q, want false", s.Labels["priced"])
	}
}

func TestParseGeminiOmitsZeroCacheReadAndDefaultsThoughts(t *testing.T) {
	row := strings.Replace(validGemini, `"thoughtsTokenCount":50,"cachedContentTokenCount":200`, `"cachedContentTokenCount":0`, 1)
	s := parseOne(t, row)
	if _, ok := s.Values["cache_read_tokens"]; ok {
		t.Errorf("cache_read_tokens present with value %d, want omitted when 0", s.Values["cache_read_tokens"])
	}
	if s.Values["output_tokens"] != 100 {
		t.Errorf("output_tokens = %d, want 100 (thoughts default to 0)", s.Values["output_tokens"])
	}
}

func TestParseStreamingUsesLastPayloadChunkWithUsage(t *testing.T) {
	row := `{"endpoint":"projects/proj-vertex/locations/us-central1/publishers/google/models/gemini-2.0-flash","logging_time":"2026-07-01T12:05:00Z","api_method":"google.cloud.aiplatform.v1.PredictionService.StreamGenerateContent","model":"publishers/google/models/gemini-2.0-flash","response_payload":["{\"candidates\":[{\"content\":{\"parts\":[{\"text\":\"hel\"}]}}]}","{\"candidates\":[{\"content\":{\"parts\":[{\"text\":\"lo\"}]}}],\"usageMetadata\":{\"promptTokenCount\":300,\"candidatesTokenCount\":40}}"]}`
	s := parseOne(t, row)
	assertStack(t, s.Stack, []string{"proj-vertex", "us-central1", "gemini-2.0-flash", "StreamGenerateContent"})
	if s.Values["input_tokens"] != 300 || s.Values["output_tokens"] != 40 {
		t.Errorf("tokens = %d in / %d out, want 300 / 40", s.Values["input_tokens"], s.Values["output_tokens"])
	}
}

func TestParseAnthropicUsageMappingAndStringEncodedFullResponse(t *testing.T) {
	s := parseOne(t, validClaude)
	assertStack(t, s.Stack, []string{"123456789", "us-east5", "claude-sonnet-4@20250514", "rawPredict"})
	want := map[string]int64{"input_tokens": 500, "output_tokens": 60, "cache_read_tokens": 30, "cache_write_tokens": 40, "calls": 1}
	for name, v := range want {
		if s.Values[name] != v {
			t.Errorf("values[%s] = %d, want %d", name, s.Values[name], v)
		}
	}
}

func TestParseAnthropicOmitsZeroCacheMetrics(t *testing.T) {
	row := strings.Replace(validClaude,
		`,\"cache_read_input_tokens\":30,\"cache_creation_input_tokens\":40`, ``, 1)
	s := parseOne(t, row)
	for _, name := range []string{"cache_read_tokens", "cache_write_tokens"} {
		if _, ok := s.Values[name]; ok {
			t.Errorf("%s present with value %d, want omitted when absent/0", name, s.Values[name])
		}
	}
}

func TestParseClaudeRowIsPriced(t *testing.T) {
	s := parseOne(t, validClaude)
	// claude-sonnet-4@20250514 -> claude-sonnet-4-20250514 (claude-sonnet-
	// rates): 500×3 + 60×15 + 30×0.30 + 40×3.75 = 2559 micro-USD.
	if s.Values["cost_microusd"] != 2559 {
		t.Errorf("cost_microusd = %d, want 2559", s.Values["cost_microusd"])
	}
	if s.Labels["priced"] != "true" {
		t.Errorf("labels[priced] = %q, want true", s.Labels["priced"])
	}
	if s.Labels["currency"] != "USD" {
		t.Errorf("labels[currency] = %q, want USD", s.Labels["currency"])
	}
}

func TestParseClaudeOpus4AtDateResolvesToLegacyRates(t *testing.T) {
	// R9: @ must be replaced with -, not stripped — claude-opus-4-20250514
	// matches the legacy Opus 4 entry ($15/$75), not the newer claude-opus-4
	// rates ($5/$25). 100×15 + 10×75 = 2250 (mismatch would give 750).
	row := strings.Replace(strings.Replace(validClaude,
		"claude-sonnet-4@20250514", "claude-opus-4@20250514", 2),
		`\"usage\":{\"input_tokens\":500,\"output_tokens\":60,\"cache_read_input_tokens\":30,\"cache_creation_input_tokens\":40}`,
		`\"usage\":{\"input_tokens\":100,\"output_tokens\":10}`, 1)
	s := parseOne(t, row)
	if s.Labels["priced"] != "true" {
		t.Fatalf("labels[priced] = %q, want true", s.Labels["priced"])
	}
	if s.Values["cost_microusd"] != 2250 {
		t.Errorf("cost_microusd = %d, want 2250 (legacy Opus 4 rates)", s.Values["cost_microusd"])
	}
}

func TestParseEndpointFallsBackToUnknown(t *testing.T) {
	cases := map[string]string{
		"missing":   strings.Replace(validGemini, `"endpoint":"projects/proj-vertex/locations/us-central1/publishers/google/models/gemini-2.0-flash",`, ``, 1),
		"malformed": strings.Replace(validGemini, `projects/proj-vertex/locations/us-central1/publishers/google/models/gemini-2.0-flash`, `not-a-resource-name`, 1),
		"truncated": strings.Replace(validGemini, `projects/proj-vertex/locations/us-central1/publishers/google/models/gemini-2.0-flash`, `projects/proj-vertex`, 1),
	}
	for name, row := range cases {
		t.Run(name, func(t *testing.T) {
			s := parseOne(t, row)
			if s.Stack[0] != "(unknown)" || s.Stack[1] != "(unknown)" {
				t.Errorf("stack = %v, want (unknown) project and location frames", s.Stack)
			}
		})
	}
}

func TestParseModelFrameFallbacks(t *testing.T) {
	noModelCol := strings.Replace(validGemini, `"model":"publishers/google/models/gemini-2.0-flash",`, ``, 1)
	t.Run("gemini_modelVersion", func(t *testing.T) {
		s := parseOne(t, noModelCol)
		if s.Stack[2] != "gemini-2.0-flash" {
			t.Errorf("model frame = %q, want gemini-2.0-flash from response modelVersion", s.Stack[2])
		}
	})
	t.Run("anthropic_model", func(t *testing.T) {
		row := strings.Replace(validClaude, `"model":"publishers/anthropic/models/claude-sonnet-4@20250514",`, ``, 1)
		s := parseOne(t, row)
		if s.Stack[2] != "claude-sonnet-4-20250514" {
			t.Errorf("model frame = %q, want claude-sonnet-4-20250514 from response model", s.Stack[2])
		}
	})
	t.Run("neither", func(t *testing.T) {
		row := strings.Replace(noModelCol, `"modelVersion":"gemini-2.0-flash",`, ``, 1)
		s := parseOne(t, row)
		if s.Stack[2] != "(unknown)" {
			t.Errorf("model frame = %q, want (unknown)", s.Stack[2])
		}
	})
	t.Run("bare_model_column", func(t *testing.T) {
		row := strings.Replace(validGemini, `"model":"publishers/google/models/gemini-2.0-flash"`, `"model":"gemini-2.0-flash"`, 1)
		s := parseOne(t, row)
		if s.Stack[2] != "gemini-2.0-flash" {
			t.Errorf("model frame = %q, want bare id used as-is", s.Stack[2])
		}
	})
}

func TestParseAPIMethodFrame(t *testing.T) {
	t.Run("bare_value_as_is", func(t *testing.T) {
		row := strings.Replace(validGemini, `"api_method":"google.cloud.aiplatform.v1.PredictionService.GenerateContent"`, `"api_method":"generateContent"`, 1)
		s := parseOne(t, row)
		if s.Stack[3] != "generateContent" {
			t.Errorf("api_method frame = %q, want generateContent", s.Stack[3])
		}
	})
	t.Run("missing", func(t *testing.T) {
		row := strings.Replace(validGemini, `"api_method":"google.cloud.aiplatform.v1.PredictionService.GenerateContent",`, ``, 1)
		s := parseOne(t, row)
		if s.Stack[3] != "(unknown)" {
			t.Errorf("api_method frame = %q, want (unknown)", s.Stack[3])
		}
	})
}

func TestParseTimeFormats(t *testing.T) {
	cases := map[string]struct {
		in   string
		want time.Time
	}{
		"space_separated": {"2026-07-01 12:00:00", time.Date(2026, 7, 1, 12, 0, 0, 0, time.UTC)},
		"rfc3339":         {"2026-07-01T12:00:00Z", time.Date(2026, 7, 1, 12, 0, 0, 0, time.UTC)},
		"epoch_seconds":   {"1748995200", time.Date(2025, 6, 4, 0, 0, 0, 0, time.UTC)},
	}
	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			row := strings.Replace(validGemini, "2026-07-01 12:00:00", tc.in, 1)
			s := parseOne(t, row)
			if !s.Time.Equal(tc.want) {
				t.Errorf("time = %v, want %v", s.Time, tc.want)
			}
		})
	}
}

func TestParseSkipsUnusableRows(t *testing.T) {
	cases := map[string]string{
		"missing_logging_time":     strings.Replace(validGemini, `"logging_time":"2026-07-01 12:00:00",`, ``, 1),
		"unparseable_logging_time": strings.Replace(validGemini, "2026-07-01 12:00:00", "not-a-time", 1),
		"no_response_body":         strings.Replace(validGemini, `,"full_response":{"modelVersion":"gemini-2.0-flash","usageMetadata":{"promptTokenCount":1000,"candidatesTokenCount":100,"thoughtsTokenCount":50,"cachedContentTokenCount":200}}`, ``, 1),
		"response_without_usage":   strings.Replace(validGemini, `{"modelVersion":"gemini-2.0-flash","usageMetadata":{"promptTokenCount":1000,"candidatesTokenCount":100,"thoughtsTokenCount":50,"cachedContentTokenCount":200}}`, `{"candidates":[]}`, 1),
	}
	for name, row := range cases {
		t.Run(name, func(t *testing.T) {
			parseSkipsOne(t, row)
		})
	}
}

func TestParseSkipsUnparseableJSONLLine(t *testing.T) {
	in := validGemini + "\n" + `{"endpoint": trunca` + "\n" + validClaude + "\n"
	samples, skipped, err := Parse(strings.NewReader(in))
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
	if len(samples) != 2 {
		t.Errorf("len(samples) = %d, want 2", len(samples))
	}
}

func TestParseFixtureFileYieldsFourSamplesAndOneSkip(t *testing.T) {
	f, err := os.Open("../../testdata/vertex-logs.json")
	if err != nil {
		t.Fatalf("open fixture: %v", err)
	}
	defer f.Close()
	samples, skipped, err := Parse(f)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
	if len(samples) != 4 {
		t.Fatalf("len(samples) = %d, want 4", len(samples))
	}
	// Literal expected stacks, in fixture row order (fixturegen inventory).
	assertStack(t, samples[0].Stack, []string{"proj-vertex", "us-central1", "gemini-2.0-flash", "GenerateContent"})
	assertStack(t, samples[1].Stack, []string{"proj-vertex", "us-central1", "gemini-2.0-flash", "StreamGenerateContent"})
	assertStack(t, samples[2].Stack, []string{"123456789", "us-east5", "claude-sonnet-4@20250514", "rawPredict"})
	assertStack(t, samples[3].Stack, []string{"(unknown)", "(unknown)", "gemini-2.0-flash", "generateContent"})
	if got := samples[1].Values["input_tokens"]; got != 300 {
		t.Errorf("streaming row input_tokens = %d, want 300", got)
	}
	if got := samples[2].Values["cost_microusd"]; got != 2559 {
		t.Errorf("claude row cost_microusd = %d, want 2559", got)
	}
	priced := 0
	for _, s := range samples {
		if s.Labels["priced"] == "true" {
			priced++
		}
	}
	if priced != 1 {
		t.Errorf("priced samples = %d, want 1 (the claude row)", priced)
	}
}
